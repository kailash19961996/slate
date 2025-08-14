// src/pages/SecondPage.jsx
import { useMemo, useState } from "react";
import ChatInterface from "../components/ChatInterface.jsx";
import FunctionPanel from "../components/FunctionPanel.jsx";
import { connectTronLinkNile, readTrxBalance } from "../utils/tronlink";
import { makeLogger } from "../utils/logger";

const API_BASE = "http://127.0.0.1:8000"; // adjust if needed
const log = makeLogger("SECOND_PAGE");

export default function SecondPage() {
  // ---------------- State ----------------
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Right-panel widget state
  const [currentWidget, setCurrentWidget] = useState("idle"); // 'idle' | 'thinking' | 'wallet'
  const [walletData, setWalletData] = useState(null);

  // Stable session id => enables backend conversation memory
  const [sessionId] = useState(() => (crypto?.randomUUID?.() || `session_${Date.now()}`));
  const nextId = useMemo(() => () => Math.floor(Math.random() * 1e15), []);

  // ---------------- Helpers ----------------
  async function postJSON(path, body) {
    log.debug("POST", path, body);
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    log.debug("RESP", path, res.status);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    log.debug("RESP JSON", path, json);
    return json;
  }

  function showBot(text) {
    setMessages((m) =>
      m.concat({ id: nextId(), text, sender: "ai", timestamp: new Date() })
    );
  }

  // ---------------- Tool Handlers ----------------
  async function handleWalletConnectRequest() {
    log.step("tool wallet_connection_request");
    try {
      const { address, nodeHost, network } = await connectTronLinkNile();
      log.info("wallet connected", { address, nodeHost, network });

      const trx = await readTrxBalance(address);
      log.info("trx balance", { trx });

      // let backend know we connected
      await postJSON("/api/wallet/connected", {
        session_id: sessionId,
        address,
        node_host: nodeHost,
        network,
      });

      // update right panel
      setWalletData({
        address,
        balance: `${Number(trx).toFixed(6)} TRX`,
        formatted_address: `${address.slice(0, 6)}...${address.slice(-4)}`,
        status: "connected",
      });
      setCurrentWidget("wallet");

      // echo to chat
      showBot(`✅ Wallet connected: ${address}`);
      showBot(`TRX balance: ${Number(trx).toFixed(6)} TRX`);
    } catch (err) {
      const errorMsg = err?.message || String(err);
      log.error("wallet connect failed", errorMsg);
      await postJSON("/api/wallet/error", { session_id: sessionId, error: errorMsg });
      showBot(`❌ Wallet connection failed: ${errorMsg}`);
      setCurrentWidget("idle");
    }
  }

  async function handleWalletDetailsRequest() {
    log.step("tool wallet_details_request");
    try {
      // ensure connected (or prompt)
      const { address, nodeHost, network } = await connectTronLinkNile();
      const trx = await readTrxBalance(address);
      const balanceStr = `${Number(trx).toFixed(6)} TRX`;
      log.info("details pulled", { address, nodeHost, network, trx });

      // update widget immediately
      setWalletData({
        address,
        balance: balanceStr,
        formatted_address: `${address.slice(0, 6)}...${address.slice(-4)}`,
        status: "connected",
      });
      setCurrentWidget("wallet");

      // send details to backend so agent can use next turn
      await postJSON("/api/wallet/details", {
        session_id: sessionId,
        address,
        trx_balance: balanceStr,
        extra: { node_host: nodeHost, network },
      });

      showBot(`📊 TRX balance: ${balanceStr}`);
    } catch (err) {
      const errorMsg = err?.message || String(err);
      log.error("wallet details failed", errorMsg);
      await postJSON("/api/wallet/error", { session_id: sessionId, error: errorMsg });
      showBot(`❌ Could not get wallet details: ${errorMsg}`);
      setCurrentWidget("idle");
    }
  }

  // ---------------- Chat send ----------------
  const handleSendToBackend = async (text) => {
    const trimmed = (text || "").trim();
    if (!trimmed) return;

    log.step("SEND", { text: trimmed, sessionId });
    setIsLoading(true);
    setCurrentWidget("thinking");

    // show user bubble
    const userMsg = { id: nextId(), text: trimmed, sender: "user", timestamp: new Date() };
    setMessages((m) => m.concat(userMsg));

    try {
      const data = await postJSON("/api/chat", {
        message: trimmed,
        session_id: sessionId,
      });

      // bot reply (if any)
      if (data.reply) {
        showBot(data.reply);
      }

      // obey tool calls
      if (Array.isArray(data.function_calls)) {
        const types = data.function_calls.map((fc) => fc.type);
        log.info("function_calls", types);

        for (const fc of data.function_calls) {
          log.step("tool dispatch", fc.type);
          if (fc.type === "wallet_connection_request") {
            await handleWalletConnectRequest();
          } else if (fc.type === "wallet_details_request") {
            await handleWalletDetailsRequest();
          } else {
            log.warn("unknown tool", fc);
          }
        }
      }
    } catch (err) {
      log.error("CHAT failed", err);
      showBot(`❌ Server error: ${err?.message || String(err)}`);
    } finally {
      setIsLoading(false);
      if (currentWidget === "thinking") setCurrentWidget("idle");
    }
  };

  // ---------------- Render ----------------
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, padding: 16 }}>
      <div>
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendToBackend}
          isLoading={isLoading}
          onBack={() => window.history.back()}
        />
      </div>

      <div>
        <FunctionPanel
          currentWidget={currentWidget}
          setCurrentWidget={setCurrentWidget}
          walletData={walletData}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
