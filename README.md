# SLATE — Simplified Blockchain AI agent

> **AI agents that act on-chain.** Type what you want; the agent plans the steps, calls tools, and connects to your wallet. One place to research, decide, and execute — fast.

---

## What this is 

An **AI‑agent front end** for TRON that reads data, explains it in simple language, and shows you clear insights. Built with **LangChain**, **agent tooling**, and **JustLend** for DeFi flows.

---
Watch the demo below
[![Watch the demo](https://img.youtube.com/vi/1GjkSVrluDs/hqdefault.jpg)](https://www.youtube.com/watch?v=1GjkSVrluDs)
 

## Why it matters

Today you bounce between docs, dashboards, and wallets. With SLATE, an agent can **do the busywork in front of you** — check if your wallet is connected, fetch market data, and give plain‑English answers like “how much can I borrow?” or “is this investment good?”. It’s a teaser of a near future where **every button on a website can be driven by an AI agent**.

---

## What we used&#x20;

* **AI agents**: Planner + tool‑calling graph using **Lightchain (LangChain)**.
* **Wallet integration**: Detects TronLink presence and wallet connection.
* **DeFi**: **JustLend** — list all markets, get details of a specific market.
* **Insights**: Explain borrow/supply limits, rough investment outlooks based on live values.
* **Stack**: React (UI), FastAPI (backend), Python tools, TronPy (reads), Langchain, simple state in memory.

---

## How it works (at a glance)

Here’s what you can try right now:

1. **Check wallet connection**
   Ask: “Is my wallet connected?” → The agent checks if **TronLink** is installed and connected.

2. **Explore JustLend markets**
   Ask: “Show me JustLend markets” → The agent fetches the list of markets.

3. **Deep dive into a market**
   Ask: “Tell me about the USDT market” → The agent returns supply/borrow rates and explains in plain English.

4. **Ask for insights**
   Example: “How much can I borrow with my balance?” or “Is this a good investment?” → The agent gives an estimate based on live values.

That’s the current working demo — no fake promises, just things you can test.

---

## Live demo (deployed)

The project is deployed here: [https://slate-frontend-0gfa.onrender.com](https://slate-frontend-0gfa.onrender.com)

Backend: \[ [https://slate-sk7k.onrender.com](https://slate-sk7k.onrender.com)]

> **Heads‑up:** The **backend on the live site is unstable** right now, so interactive actions may fail. **Local setup works perfectly** — see below.

---

## Install & run locally

### Prereqs

* Node 18+
* Python 3.10+
* A Chromium browser with **TronLink** extension

### 1) Backend

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U fastapi uvicorn langchain langgraph tronpy python-dotenv
```

Create **.env** in the backend folder:

```dotenv
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

JL_LIST_LIMIT_DEFAULT=6
JL_PER_MARKET_DELAY_MS=300
JL_MAX_ATTEMPTS=4
JL_BASE_DELAY_MS=300
JL_CACHE_TTL_SEC=180

TRON_NETWORK=mainnet
TRONGRID_API_KEY=1cc6c501-...
JL_UNITROLLER_MAIN=TGjYzgCyPobsNS9n6WcbdLVR9dH7mWqFx7

```

Run it:

```bash
uvicorn server:app --reload --port 8000
```

### 2) Frontend

```bash
cd frontend
npm i
npm run dev
```

Open the shown localhost URL, connect **TronLink**, and start chatting.

---

## Project status

* ✅ Wallet connection check
* ✅ Detect TronLink presence
* ✅ JustLend market list + market detail
* ✅ Agent explains borrowing/investment insights
* ⚠️ **Deployed backend** has issues; local run is the recommended path for judging

---

## Future scope (where this goes next)

* **More tools**: portfolio health, repay planner, cross‑market optimizer, notifications.
* **More integrations**: more TRON DeFi protocols, price oracles.
* **Safer automation**: user rules like “auto‑approve tips ≤ 5 USDT to known addresses”.
* **Better memory**: preferences and previously used addresses across sessions.
* **Multi‑chain later**: same agent UI, different highway.

---

## Vision

If an agent can click every button you see — **research, compare, and execute** — you stop tab‑hopping. You say what you want; the agent does the rest, transparently, with your approval. That’s SLATE.
