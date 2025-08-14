export async function connectTronLinkNile() {
    if (!window.tronLink) throw new Error("TronLink not found. Install/enable the extension.");
    await window.tronLink.request({ method: "tron_requestAccounts" });
  
    const tw = window.tronWeb;
    if (!tw?.defaultAddress?.base58) throw new Error("TronLink locked or no account.");
    
    const address = tw.defaultAddress.base58;
    const nodeHost = tw.fullNode?.host || "unknown";
    if (!/nile/i.test(nodeHost)) throw new Error("Wrong network. Switch TronLink to NILE.");
  
    return { address, nodeHost, network: "nile" };
  }
  
  export async function readTrxBalance(address) {
    const tw = window.tronWeb;
    if (!tw) throw new Error("TronWeb unavailable.");
    const balSun = await tw.trx.getBalance(address);
    return (balSun / 1e6).toFixed(6) + " TRX";
  }
  