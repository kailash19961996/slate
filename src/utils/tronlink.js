// src/utils/tronlink.js
import { makeLogger } from "./logger";

const log = makeLogger("TRONLINK");

export async function connectTronLinkNile() {
  log.step("connect start");

  if (!window.tronLink) {
    log.error("extension not found");
    throw new Error("TronLink not found. Install/enable the extension.");
  }

  try {
    log.info("requesting accounts via tron_requestAccounts");
    await window.tronLink.request({ method: "tron_requestAccounts" });
  } catch (e) {
    log.error("user rejected or wallet error", e);
    throw new Error(e?.message || "User rejected wallet request.");
  }

  const tw = window.tronWeb;
  if (!tw?.defaultAddress?.base58) {
    log.error("no defaultAddress.base58 (locked or no account)");
    throw new Error("TronLink locked or no account selected.");
  }

  const address = tw.defaultAddress.base58;
  const nodeHost = tw.fullNode?.host || "unknown";
  const onNile = /nile/i.test(nodeHost);

  log.info("connected", { address, nodeHost });
  if (!onNile) {
    log.warn("wrong network", { nodeHost });
    throw new Error("Wrong network. Switch TronLink to NILE testnet.");
  }

  log.step("connect success");
  return { address, nodeHost, network: "nile" };
}

export async function readTrxBalance(address) {
  const tw = window.tronWeb;
  if (!tw) {
    log.error("tronWeb unavailable");
    throw new Error("TronWeb unavailable.");
  }
  log.info("reading TRX balance", { address });
  const balSun = await tw.trx.getBalance(address);
  const trx = balSun / 1e6;
  log.info("balance read", { trx });
  return trx; // numeric
}
