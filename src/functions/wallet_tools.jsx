// src/functions/wallet_tools.jsx
// ------------------------------------------------------------
// Wallet tools used by SecondPage.jsx
// 1) checkTronLinkPresence()
// 2) connectWalletIfNeeded()
// 3) fetchBalanceFlow()
// ------------------------------------------------------------

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function waitFor(predicate, timeoutMs, intervalMs, onTimeoutMessage) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      if (predicate()) return;
    } catch {}
    await sleep(intervalMs);
  }
  throw new Error(onTimeoutMessage || "Operation timed out.");
}

// Tool #1 — Check TronLink
export async function checkTronLinkPresence() {
  console.log("🔎 [wallet_tools] checkTronLinkPresence()");
  const present = !!window.tronLink;
  const injected = !!window.tronWeb;
  return {
    tool: "wallet_check_tronlink",
    tronLinkPresent: present,
    tronWebInjected: injected,
  };
}

// Tool #2 — Connect wallet
export async function connectWalletIfNeeded() {
  console.log("🔌 [wallet_tools] connectWalletIfNeeded() start");
  await waitFor(() => !!window.tronLink, 8000, 150, "TronLink not found. Please install/enable it.");
  await waitFor(() => !!window.tronWeb, 8000, 150, "TronWeb not injected by TronLink yet.");

  const tw = window.tronWeb;
  const current = tw?.defaultAddress?.base58 || "";
  if (!current) {
    await window.tronLink.request({ method: "tron_requestAccounts" });
    await waitFor(() => !!(window.tronWeb?.defaultAddress?.base58), 8000, 200, "No account selected or TronLink locked.");
  }

  const address = tw?.defaultAddress?.base58 || "";
  const nodeHost = tw?.fullNode?.host || "unknown";
  const network = /nile/i.test(nodeHost)
    ? "nile"
    : /mainnet|api\.trongrid\.io/i.test(nodeHost)
    ? "mainnet"
    : "unknown";

  if (!address) throw new Error("Connected to TronLink but no active address found.");

  return {
    tool: "wallet_connect",
    address,
    nodeHost,
    network,
  };
}

// Tool #3 — Full "fetch balance" flow
export async function fetchBalanceFlow() {
  console.log("🧾 [wallet_tools] fetchBalanceFlow() start");

  const presence = await checkTronLinkPresence();
  if (!presence.tronLinkPresent) {
    return { tool: "wallet_fetch_balance", ok: false, error: "TronLink extension not found." };
  }

  let address, nodeHost, network;
  try {
    const connect = await connectWalletIfNeeded();
    address = connect.address;
    nodeHost = connect.nodeHost;
    network = connect.network;
  } catch (err) {
    return { tool: "wallet_fetch_balance", ok: false, error: err?.message || String(err) };
  }

  const tw = window.tronWeb;
  if (!tw) return { tool: "wallet_fetch_balance", ok: false, error: "TronWeb not available after connect." };

  try {
    const [balSun, acct, res] = await Promise.all([
      tw.trx.getBalance(address),
      tw.trx.getAccount(address),
      tw.trx.getAccountResources(address),
    ]);

    const toTRX = (v) => Number(v || 0) / 1e6;

    const snapshot = {
      address,
      nodeHost,
      network,
      core: { trx: toTRX(balSun) },
      resources: {
        energy: { used: Number(res?.EnergyUsed || 0), limit: Number(res?.EnergyLimit || 0) },
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
      fetchedAt: new Date().toISOString(),
    };

    return {
      tool: "wallet_fetch_balance",
      ok: true,
      summary: {
        address: `${address.slice(0, 6)}...${address.slice(-4)}`,
        network,
        trx: Number(snapshot.core.trx).toFixed(6),
        energyUsed: snapshot.resources.energy.used,
        energyLimit: snapshot.resources.energy.limit,
        bwUsed: snapshot.resources.bandwidth.used,
        bwFreeLimit: snapshot.resources.bandwidth.freeLimit,
      },
      snapshot,
    };
  } catch (err) {
    return { tool: "wallet_fetch_balance", ok: false, error: err?.message || String(err) };
  }
}

