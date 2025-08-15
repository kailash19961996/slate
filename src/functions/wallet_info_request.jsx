// src/functions/wallet_info_request.jsx
// Unified handler for { type: "wallet_info_request" } from the backend.
// MAINNET-safe: accepts whatever network TronLink is on, shows it to the user.
// Always fetches a fresh snapshot, then posts back to backend for memory.

export async function handleWalletInfoRequest({
    setMessages,
    setWalletData,
    setCurrentWidget,
    sessionId,
    API_BASE
  }) {
    try {
      console.log('🔧 [wallet_info_request] start — ensure connection and fresh snapshot');
  
      // UX hint
      setMessages(prev => [...prev, {
        id: Date.now() + Math.random(),
        text: '🔄 Attempting to connect to TronLink… please approve the popup.',
        sender: 'ai',
        timestamp: new Date()
      }]);
  
      // 1) Connect and wait for address/network to stabilize
      const { address, nodeHost, network } = await fullyConnectWallet();
  
      // Show connected network to the user (mainnet or otherwise)
      setMessages(prev => [...prev, {
        id: Date.now() + Math.random(),
        text: `✅ Wallet connected (${network}). Fetching details…`,
        sender: 'ai',
        timestamp: new Date()
      }]);
  
      // 2) ALWAYS read a fresh snapshot
      const snap = await getFreshWalletSnapshot(address);
  
      // 3) Update right panel widget + summary line
      setWalletData({
        ...snap,
        balance: `${Number(snap.core.trx).toFixed(6)} TRX`,
        formatted_address: `${address.slice(0, 6)}...${address.slice(-4)}`,
        status: 'connected'
      });
      setCurrentWidget('wallet');
  
      const summary =
        `📊 TRX balance: ${Number(snap.core.trx).toFixed(6)} TRX | ` +
        `Energy ${snap.resources.energy.used}/${snap.resources.energy.limit} | ` +
        `Bandwidth ${snap.resources.bandwidth.used}/${snap.resources.bandwidth.freeLimit}`;
      setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: summary, sender: 'ai', timestamp: new Date() }]);
  
      // 4) Push to backend to refresh memory (so AI answers from memory next time)
      await postJson(`${API_BASE}/api/wallet/connected`, {
        session_id: sessionId,
        address,
        node_host: nodeHost,
        network
      });
      await postJson(`${API_BASE}/api/wallet/details`, {
        session_id: sessionId,
        address,
        trx_balance: `${Number(snap.core.trx).toFixed(6)} TRX`,
        extra: { snapshot: snap, node_host: nodeHost, network }
      });
  
      console.log('✅ [wallet_info_request] complete — backend memory refreshed');
    } catch (err) {
      console.error('❌ [wallet_info_request] failed:', err);
      setMessages(prev => [...prev, {
        id: Date.now() + Math.random(),
        text: `❌ Wallet action failed: ${err?.message || err}`,
        sender: 'ai',
        timestamp: new Date()
      }]);
      try {
        await postJson(`${API_BASE}/api/wallet/error`, {
          session_id: sessionId,
          error: err?.message || String(err)
        });
      } catch { /* ignore */ }
      setCurrentWidget('idle');
    }
  }
  
  /* -----------------------------------------------------------------------------
   * Helpers (kept local — no utils folder)
   * ---------------------------------------------------------------------------*/
  
  async function fullyConnectWallet() {
    console.log('🔌 [wallet] fullyConnectWallet()');
  
    await waitFor(() => !!window.tronLink, 8000, 100, 'TronLink extension not found. Install or enable it.');
    await waitFor(() => !!window.tronWeb, 8000, 100, 'TronWeb not injected by TronLink yet.');
    await window.tronLink.request({ method: 'tron_requestAccounts' });
  
    const prev = window.tronWeb?.defaultAddress?.base58 || '';
    console.log('ℹ️ [wallet] previous defaultAddress:', prev || '(empty)');
  
    await waitFor(() => !!(window.tronWeb?.defaultAddress?.base58), 8000, 100, 'No account selected or TronLink locked.');
    await sleep(200);
  
    const addr = window.tronWeb?.defaultAddress?.base58 || '';
    const host = window.tronWeb?.fullNode?.host || 'unknown';
    const network =
      /nile/i.test(host) ? 'nile' :
      (/mainnet|api\.trongrid\.io/i.test(host) ? 'mainnet' : 'unknown');
  
    console.log('✅ [wallet] connected →', { address: addr, host, network });
    if (!addr) throw new Error('TronLink connected but no active address found.');
    return { address: addr, nodeHost: host, network };
  }
  
  async function getFreshWalletSnapshot(address) {
    console.log('🧾 [wallet] getFreshWalletSnapshot()', address);
    const tw = window.tronWeb;
    if (!tw) throw new Error('TronWeb not available (TronLink not injected).');
  
    const [balSun, acct, res] = await Promise.all([
      tw.trx.getBalance(address),
      tw.trx.getAccount(address),
      tw.trx.getAccountResources(address),
    ]);
  
    const toTRX = v => Number(v || 0) / 1e6;
  
    const host = tw.fullNode?.host || 'unknown';
    const network =
      /nile/i.test(host) ? 'nile' :
      (/mainnet|api\.trongrid\.io/i.test(host) ? 'mainnet' : 'unknown');
  
    const snapshot = {
      address,
      nodeHost: host,
      network,
      core: { trx: toTRX(balSun) },
      resources: {
        energy: {
          used: Number(res?.EnergyUsed || 0),
          limit: Number(res?.EnergyLimit || 0),
        },
        bandwidth: {
          used: Number(res?.NetUsed || 0),
          limit: Number(res?.NetLimit || 0),
          freeUsed: Number(res?.freeNetUsed || 0),
          freeLimit: Number(res?.freeNetLimit || 0),
        },
      },
      frozen: {
        forBandwidthTRX: toTRX((acct?.frozen?.[0]?.frozen_balance) || 0),
        forEnergyTRX: toTRX((acct?.account_resource?.frozen_balance_for_energy) || 0),
      },
      permissions: {
        ownerKeys: acct?.owner_permission?.keys?.length || 1,
        ownerThreshold: acct?.owner_permission?.threshold || 1,
        activeCount: Array.isArray(acct?.active_permission) ? acct.active_permission.length : 0,
      },
      tokens: [],
      fetchedAt: new Date().toISOString(),
    };
  
    console.log('📦 [wallet] fresh snapshot:', snapshot);
    return snapshot;
  }
  
  async function postJson(url, body) {
    console.log('📡 [postJson]', url, body);
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      const t = await res.text().catch(() => '');
      console.error('❌ [postJson] failed', res.status, t);
      throw new Error(`POST ${url} failed with ${res.status}`);
    }
    return res.json().catch(() => ({}));
  }
  
  async function waitFor(predicate, timeoutMs, intervalMs, onTimeoutMessage) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      try { if (predicate()) return; } catch {}
      await sleep(intervalMs);
    }
    throw new Error(onTimeoutMessage || 'Operation timed out.');
  }
  
  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
  