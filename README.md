Here’s a polished, copy‑paste‑ready **README.md** you can ship with your hackathon repo. It explains what you’re building, how it meets each TRON track requirement, how to run it, and what the AI agent actually does (risk scoring, simulation, backtesting, payments, wallet management), in simple language.

---

# Artisty x TRON — **AI Wallet Concierge**

> An AI agent (LangChain + LangGraph + OpenAI) that connects to **TRON**, helps users **pay**, **lend/borrow** via **JustLend**, and manages wallets with **risk scoring, simulations, backtesting, anomaly alerts**, and **smart approvals**.

## 1) TL;DR (What it does)

* **Chat to Chain:** Talk to the agent: “connect my wallet”, “lend 100 USDT”, “simulate my yield for 30 days”.
* **DeFi on TRON:** Lists JustLend markets, explains APY, lets users **supply/borrow** (with guardrails).
* **Payments on TRON:** One‑tap **TRC‑20 USDT** checkout, tips, and subscriptions (recurring).
* **Wallet Intelligence:** Budget summary, **anomaly detection**, and **(scoped) auto‑approval** rules.
* **Explain Like I’m 5:** Every action includes a plain‑English explanation and a one‑line risk note.

---

## 2) Why this fits the TRON Hackathon (Tracks & Requirements)

### A) **DeFi Products & Services on TRON**

* **Integration:** Reads JustLend (Unitroller + jTokens) for markets, rates, collateral factors.
* **AI features:**

  * **Risk scoring**: labels positions *low/med/high* using LTV, utilization, buffer.
  * **Portfolio simulation**: “what‑if” earnings for N days.
  * **Strategy backtesting**: e.g., weekly DCA into lending, using cached historical rates.
* **Outcome:** Safer, simpler DeFi flows for newcomers.

### B) **AI‑Powered Payments Infrastructure**

* **TRC‑20 USDT payments** via TronLink (no custodial keys).
* **Personalized checkout**: preferred token, tip suggestion, split payouts (e.g., 90/10).
* **Fraud/UX optimization**: anomaly checks + “are you sure?” prompts on unusual payees/amounts.
* **Optional**: **Subscriptions** (recurring payments) with user‑set limits.

### C) **TRON Wallet Management Agent**

* **Wallet connect** (TronLink), **read balances/tx history**.
* **Budget view**: where funds moved (lend, borrow, tips, gas).
* **Anomaly detection**: large/new recipients, spiky activity, duplicate charges.
* **Auto‑approval** (scoped): user rules like “auto‑approve ≤ 5 USDT tips to known creators”.

### D) **AI Agent SDK + On‑chain Actions**

* **Framework**: LangChain (+ LangGraph for tool orchestration & memory).
* **On‑chain**: Reads contracts; prepares transactions for TronLink signature (safety).
* **Demonstrable use case**: chat demo—buy → tip → lend → simulate → withdraw.

---

## 3) Crypto in Simple Words

* **TRON** = the highway.
* **TRC‑20 tokens** (e.g., USDT) = cars that fit that highway.
* **JustLend** = a marketplace to **earn** (supply) or **borrow** tokens.
* **TronLink** = your wallet app; it pops up to approve actions (like Google Pay).
* **Gas fee** = postage stamp for your transaction.

---

## 4) Architecture

```
React (split screen)           Python Backend
--------------------           -----------------------------
Chat (left)                    FastAPI/Flask
Dynamic Panel (right)     ->   LangChain + LangGraph agent
TronLink popup                 Tools:
                              - wallet.balance()
                              - justlend.list_markets()
                              - justlend.market_detail()
                              - risk.score()
                              - simulate.yield()
                              - backtest.strategy()
                              - payments.tip()
                              - subscriptions.schedule()
```

* **Safety**: No private keys on server. All state‑changing txs **go to TronLink** for user signature.
* **Memory**: LangGraph checkpointing (conversation thread + preferences).
* **Observability**: (Optional) LangSmith for traces & evals.

---

## 5) Core Features (Agent Tools)

### Wallet

* `wallet.connect()` → handled client‑side via TronLink; backend reads view‑only.
* `wallet.balance(address)` → TRX + TRC‑20 balances.
* `wallet.activity(address)` → summarized recent txs.

### DeFi (JustLend)

* `justlend.list_markets()` → all jTokens with **supply/borrow rate**, utilization, **collateral factor**.
* `justlend.market_detail(symbol)` → exchange rate, total borrows/cash, borrow cap, etc.
* `justlend.user_position(address)` → supplied, borrowed, liquidity/shortfall.
* `justlend.supply(amount, token)` / `justlend.withdraw(...)` / `justlend.borrow(...)` / `justlend.repay(...)`

  * Returns **prepared tx** → user signs in TronLink.

### AI Finance

* `risk.score(position)` → *low/med/high* + reason (LTV, buffer, volatility).
* `simulate.yield(token, amount, days)` → what‑if earnings.
* `backtest.dca(token, weeks)` → “had you supplied weekly, you’d earn ≈ X”.

### Payments

* `payments.checkout(items, totals, token=USDT)` → TRC‑20 flow.
* `payments.tip(to, amount)` → small USDT tip.
* `subscriptions.schedule(to, amount, cadence)` → recurring with caps/alerts.

### Safety/Trust

* `detect.anomaly(tx_history)` → flags unusual recipients/amounts/spikes.
* `policy.guardrails(tx)` → block or require explicit confirmation.

---

## 6) UX Demo Flows

1. **Buy + Tip (TRC‑20 USDT)**
   “Buy ‘Blue Crane’” → shows price, fees, split → TronLink confirm → **receipt + tx link**.

2. **Save (Supply) on JustLend**
   “Save 100 USDT for 30 days” → simulation + *low risk* note → TronLink supply → yield summary.

3. **Borrow Carefully**
   “Borrow 200 USDT” → LTV suggestion, safe buffer → TronLink borrow → payback plan.

4. **Anomaly Alert**
   New large transfer? Agent: “Looks unusual—proceed?” → user reviews or blocks.

---

## 7) Installation & Run

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U fastapi uvicorn langchain langchain-openai langgraph tronpy python-dotenv
```

**Env (.env)**

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
TRON_FULLNODE=https://api.trongrid.io
UNITROLLER=Tx...     # JustLend Unitroller address
JUSDT=Ty...          # jUSDT address (add more jTokens as needed)
```

**Start**

```bash
uvicorn server:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm i
npm run dev
```

---

## 8) Minimal Endpoints (for your React panel)

```
POST /agent/chat        { text, session_id }  -> { reply, tool_events }
GET  /defi/markets                          -> [{symbol, supplyAPR, borrowAPR, collatFactor, utilization}]
GET  /defi/market/:symbol                   -> {...deep stats...}
GET  /wallet/:address/positions             -> {supplied, borrowed, liquidity, shortfall}
POST /defi/simulate                         -> { token, amount, days } -> { est_earnings }
POST /defi/backtest                         -> { token, weeks } -> { summary, series }
POST /pay/checkout                          -> { items, total, token } -> { prepared_tx }
POST /pay/tip                               -> { to, amount } -> { prepared_tx }
```

> **Prepared tx** = object your frontend submits to **TronLink** for the signature (server never signs).

---

## 9) LangChain + LangGraph Skeleton

* **Planner node** (decide intent)
* **Tool node** (call the right tool; can loop)
* **Safety node** (guardrails/anomaly checks)
* **Explainer** (generate ELI5 + risk note)
* **Memory** (thread history + user prefs)

```python
# Pseudocode wiring
graph: Planner -> Tools <-> Planner
                 \-> Safety -> Planner
                 -> END (when no more tool calls)
```

---

## 10) Risk Model (simple & transparent)

* **Inputs:** Collateral factor, user LTV, market utilization, recent rate variance.
* **Score:**

  * *Low*: LTV ≤ 40% & utilization < 70%
  * *Medium*: LTV 40–60% or utilization 70–85%
  * *High*: LTV > 60% or utilization > 85%
* **Output:** Label + “why” line (e.g., “Safe buffer: your LTV is 32% with low utilization.”)

---

## 11) Backtesting (quick & fair)

* Cache daily/weekly rates (server).
* Recreate DCA: supply `x` per week → sum interest using period rates.
* Report **range** (min/avg/max) with “not financial advice” tag.

---

## 12) Security & Guardrails

* **No private keys** server‑side.
* **All** state‑changing ops go through **TronLink**.
* Clear risk/fee warnings; double confirmation for risky LTV or unknown recipient.
* Rate limits, schema validation on tool inputs.
* Optional: **allowlist** for auto‑approval; everything else prompts.

---

## 13) Judge‑friendly Checklist

* ✅ **Recognized agent framework**: LangChain + LangGraph
* ✅ **On‑chain interactions**: Read JustLend, prepare txs; TronLink signs
* ✅ **DeFi integration**: Markets, supply/borrow, collateral factors
* ✅ **AI features**: Risk scoring, simulation, backtesting, anomaly detection
* ✅ **Payments**: TRC‑20 USDT checkout, tips, optional subscriptions
* ✅ **Clear UX**: Chat to action + ELI5 + receipts/tx links
* ✅ **Safety**: No custody, explicit approvals, warnings

---

## 14) Roadmap (post‑MVP)

* **Royalty Splitter** mini‑contract (auto revenue share to multiple addresses).
* **Notifications** (subs due, health factor drops).
* **Telegram mini‑app** mirroring the same agent tools.
* **LangSmith** traces + evals; unit tests for tools.

---

## 15) Dev Tips

* Start **read‑only** (markets, positions), then add a **single supply** flow.
* Keep APR scaling factors configurable to match JustLend’s UI.
* Cache reads to keep chat snappy; show timestamps like “rates updated 1m ago”.
* Always attach a short **ELI5** and **risk note** to actions.

---

## 16) Legal / NFA

This project is for educational/demo purposes. It is **not** financial advice. Users should review risks and confirm every transaction in TronLink.

---

If you want, I can also drop in:

* a tiny **`/defi/markets`** FastAPI route that calls TronPy and returns normalized rows,
* the **LangGraph** wiring for planner→tool→safety,
* or a **React** right‑panel component that renders markets + one‑click “Simulate / Supply” buttons.
