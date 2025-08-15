// src/functions/wallet_info_request.jsx
// Unified handler for the backend tool call: { type: "wallet_info_request" }
// - Connects to TronLink (Nile/Mainnet detection)
// - Builds a full snapshot
// - Updates right panel + chat
// - Posts /api/wallet/connected and /api/wallet/details back to backend

export async function handleWalletInfoRequest({
    setMessages,
    setWalletData,
    setCurrentWidget,
    sessionId,
    API_BASE
  }) {
    try {
      // --- Step 0: show intent in the chat
    //   setMessages(prev => [...prev, {
    //     id: Date.now() + Math.random(),
    //     text: '🔄 Attempting to connect to TronLink... Please approve the popup.',
    //     sender: 'ai',
    //     timestamp: new Date()
    //   }]);
  
      // --- Step 1: connect wallet via TronLink
      const { address, nodeHost, network } = await connectTronLinkNile();
  
      // --- Step 2: acknowledge connection
      setMessages(prev => [...prev, {
        id: Date.now() + Math.random(),
        text: `Wallet connected (${network}). Fetching details...`,
        sender: 'ai',
        timestamp: new Date()
      }]);
  
      // --- Step 3: build snapshot
      const snap = await getWalletSnapshot(address);
  
      // --- Step 4: update the right panel widget
      setWalletData({
        ...snap,
        balance: `${Number(snap.core.trx).toFixed(6)} TRX`,
        formatted_address: `${address.slice(0, 6)}...${address.slice(-4)}`,
        status: 'connected'
      });
      setCurrentWidget('wallet');
  
      // --- Step 5: post a concise summary to chat (Bandwidth uses freeLimit)
      const sumText =
        `📊 TRX balance: ${Number(snap.core.trx).toFixed(6)} TRX | ` +
        `Energy ${snap.resources.energy.used}/${snap.resources.energy.limit} | ` +
        `Bandwidth ${snap.resources.bandwidth.used}/${snap.resources.bandwidth.freeLimit}`;
      setMessages(prev => [...prev, {
        id: Date.now() + Math.random(),
        text: sumText,
        sender: 'ai',
        timestamp: new Date()
      }]);
  
      // --- Step 6: notify backend (so it can answer from memory next time)
      await fetch(`${API_BASE}/api/wallet/connected`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, address, node_host: nodeHost, network })
      });
  
      await fetch(`${API_BASE}/api/wallet/details`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          address,
          trx_balance: `${Number(snap.core.trx).toFixed(6)} TRX`,
          extra: { snapshot: snap, node_host: nodeHost, network }
        })
      });
  
      console.log('✅ [wallet_info_request] Completed');
    } catch (err) {
      console.error('❌ [wallet_info_request] Failed:', err);
      setMessages(prev => [...prev, {
        id: Date.now() + Math.random(),
        text: `❌ Wallet action failed: ${err?.message || err}`,
        sender: 'ai',
        timestamp: new Date()
      }]);
      try {
        await fetch(`${API_BASE}/api/wallet/error`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId, error: err?.message || String(err) })
        });
      } catch (_) { /* ignore secondary error */ }
      setCurrentWidget('idle');
    }
  }
  
  /* -------------------------------------------------------------------------- */
  /* Helpers (kept local to this file — no utils folder needed)                 */
  /* -------------------------------------------------------------------------- */
  
  async function connectTronLinkNile() {
    console.log('🔌 [WALLET] connectTronLinkNile() invoked');
  
    if (!window.tronLink) {
      console.error('❌ [WALLET] TronLink extension not found');
      throw new Error('TronLink not found. Install or enable the extension.');
    }
  
    // Ask wallet to expose accounts (user may approve/reject)
    await window.tronLink.request({ method: 'tron_requestAccounts' });
  
    const tw = window.tronWeb;
    const addr = tw?.defaultAddress?.base58;
    if (!addr) {
      console.error('❌ [WALLET] No defaultAddress.base58 (locked or no account)');
      throw new Error('TronLink locked or no account selected.');
    }
  
    const host = tw?.fullNode?.host || 'unknown';
    let network = 'unknown';
    if (/nile/i.test(host)) network = 'nile';
    else if (/mainnet|api\.trongrid\.io/i.test(host)) network = 'mainnet';
  
    console.log('✅ [WALLET] Connected', { address: addr, host, network });
    return { address: addr, nodeHost: host, network };
  }
  
  async function getWalletSnapshot(address) {
    console.log('🧾 [WALLET] getWalletSnapshot()', address);
    const tw = window.tronWeb;
    if (!tw) throw new Error('TronWeb not available');
  
    const [balSun, acct, res] = await Promise.all([
      tw.trx.getBalance(address),
      tw.trx.getAccount(address),
      tw.trx.getAccountResources(address),
    ]);
  
    const toTRX = (sun) => Number(sun || 0) / 1e6;
    const frozenBandwidthTRX = toTRX(acct?.frozen?.[0]?.frozen_balance || 0);
    const frozenEnergyTRX = toTRX(acct?.account_resource?.frozen_balance_for_energy || 0);
  
    const host = tw.fullNode?.host || 'unknown';
  
    const snapshot = {
      address,
      nodeHost: host,
      network: /nile/i.test(host) ? 'nile' : (/mainnet|api\.trongrid\.io/i.test(host) ? 'mainnet' : 'unknown'),
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
        forBandwidthTRX: frozenBandwidthTRX,
        forEnergyTRX: frozenEnergyTRX,
      },
      permissions: {
        ownerKeys: acct?.owner_permission?.keys?.length || 1,
        ownerThreshold: acct?.owner_permission?.threshold || 1,
        activeCount: Array.isArray(acct?.active_permission) ? acct.active_permission.length : 0,
      },
      tokens: [],
      fetchedAt: new Date().toISOString(),
    };
  
    console.log('📦 [WALLET] Snapshot:', snapshot);
    return snapshot;
  }
  