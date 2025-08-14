import { useEffect, useState } from "react";
import { comptrollerAbi, jTokenAbi } from "./jlabi";

// NOTE: fill these with the NILE testnet addresses for JustLend on Tronscan (Comptroller + a few jTokens).
const NILE_COMPTROLLER = "TCOMPTROLLER_ADDRESS"; // e.g., T... (look up “Comptroller” under JustLend on Nile)
const JUSDT = "TJUSDT_JTOKEN_ADDRESS";          // a jUSDT market
const JTRX  = "TJTRX_JTOKEN_ADDRESS";           // a jTRX market (receipt for TRX)

const BN1e18 = 1e18;
const BLOCKS_PER_YEAR = 10512000;

export default function JustLendRates() {
  const [addr, setAddr] = useState("");
  const [markets, setMarkets] = useState([]);
  const [error, setError] = useState("");

  const connect = async () => {
    try {
      await window.tronLink.request({ method: "tron_requestAccounts" });
      setAddr(window.tronWeb.defaultAddress.base58);
    } catch (e) {
      setError(String(e));
    }
  };

  const call = async (contractAddr, abi, method, args = []) => {
    const tw = window.tronWeb;
    const c = await tw.contract(abi, contractAddr);
    return await c[method](...args).call();
  };

  const toApy = (ratePerBlockMantissa) => {
    const r = Number(ratePerBlockMantissa) / BN1e18;
    return (Math.pow(1 + r, BLOCKS_PER_YEAR) - 1) * 100;
  };

  const load = async () => {
    try {
      const tw = window.tronWeb;
      if (!tw) return setError("TronWeb not available");
      // 1) list markets (addresses of jTokens)
      const jTokenAddrs = await call(NILE_COMPTROLLER, comptrollerAbi, "getAllMarkets");

      // 2) for each, read symbol + rates
      const rows = [];
      for (const jt of jTokenAddrs) {
        try {
          const sym = await call(jt, jTokenAbi, "symbol");
          const supplyPerBlock = await call(jt, jTokenAbi, "supplyRatePerBlock");
          const borrowPerBlock = await call(jt, jTokenAbi, "borrowRatePerBlock");
          rows.push({
            addr: jt,
            symbol: sym,
            supplyAPY: toApy(supplyPerBlock).toFixed(2) + " %",
            borrowAPY: toApy(borrowPerBlock).toFixed(2) + " %",
          });
        } catch {}
      }
      setMarkets(rows);
    } catch (e) {
      console.error(e);
      setError(String(e));
    }
  };

  useEffect(() => { if (addr) load(); }, [addr]);

  return (
    <div style={{padding:20}}>
      <h2>JustLend (Nile) – Markets & Rates</h2>
      {!addr && <button onClick={connect}>Connect TronLink</button>}
      {error && <div style={{color:"salmon"}}>{error}</div>}
      {markets.map((m) => (
        <div key={m.addr} style={{margin:"8px 0", padding:8, border:"1px solid #333", borderRadius:8}}>
          <div><b>{m.symbol}</b></div>
          <div>Supply APY: {m.supplyAPY}</div>
          <div>Borrow APY: {m.borrowAPY}</div>
          <div style={{fontSize:12, opacity:0.8}}>jToken: {m.addr}</div>
        </div>
      ))}
    </div>
  );
}
