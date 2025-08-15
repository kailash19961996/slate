"""
SLATE Backend (LangGraph + Memory + TronLink orchestration)
- Enforces the 4-step wallet flow
- Adds dynamic LLM memory (facts) via structured extraction + LangGraph checkpointing
- Keeps your frontend contract: return { reply, function_calls }
"""

import os
import time
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

import json
from pydantic import BaseModel as PydModel, Field as PydField, ValidationError
from typing import Dict, List

# LangChain / LangGraph
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool

from pydantic import BaseModel as PydModel, Field as PydField
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from tronpy import Tron
from tronpy.providers import HTTPProvider

# ------------------------------------------------------------------------------
# Boot & globals
# ------------------------------------------------------------------------------

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPEN_AI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set.")

print(f"🤖 Model: {MODEL}")

TRON_NETWORK = os.getenv("TRON_NETWORK", "mainnet").lower()  # 'mainnet' | 'nile'
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")  # required for mainnet
if TRON_NETWORK == "mainnet" and not TRONGRID_API_KEY:
    raise RuntimeError("TRONGRID_API_KEY is required on mainnet")

UNITROLLER_NILE = "TGjYzgCyPobsNS9n6WcbdLVR9dH7mWqFx7" # Contracts (mainnet)
JUSDT_NILE = "TXJgMdjVX5dKiQaUi9QobwNxtSQaFqccvd" # Example jToken: jUSDT (mainnet)

app = FastAPI(title="SLATE Backend", version="7.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plain in‑memory sessions (used by HTTP endpoints)
sessions: Dict[str, Dict[str, Any]] = {}

# ------------------------------------------------------------------------------
# Frontend ↔ Backend contract (request/response models)
# ------------------------------------------------------------------------------
COMPTROLLER_ABI = [
    {"name": "getAllMarkets","type":"function","inputs":[],"outputs":[{"name":"","type":"address[]"}],"stateMutability":"view","constant":True},
    {"name": "markets","type":"function","inputs":[{"name":"jToken","type":"address"}],
     "outputs":[{"name":"isListed","type":"bool"},{"name":"collateralFactorMantissa","type":"uint256"},{"name":"isComped","type":"bool"}],
     "stateMutability":"view","constant":True},
    {"name": "getAccountLiquidity","type":"function","inputs":[{"name":"account","type":"address"}],
     "outputs":[{"name":"error","type":"uint256"},{"name":"liquidity","type":"uint256"},{"name":"shortfall","type":"uint256"}],
     "stateMutability":"view","constant":True},
]

JTOKEN_ABI = [
    {"name":"symbol","type":"function","inputs":[],"outputs":[{"name":"","type":"string"}],"stateMutability":"view","constant":True},
    {"name":"supplyRatePerBlock","type":"function","inputs":[],"outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","constant":True},
    {"name":"borrowRatePerBlock","type":"function","inputs":[],"outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","constant":True},
    {"name":"exchangeRateStored","type":"function","inputs":[],"outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","constant":True},
    {"name":"totalBorrows","type":"function","inputs":[],"outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","constant":True},
    {"name":"getAccountSnapshot","type":"function","inputs":[{"name":"account","type":"address"}],
     "outputs":[{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"}],
     "stateMutability":"view","constant":True},
]

def _tron_client() -> Tron:
    if TRON_NETWORK == "mainnet":
        return Tron(provider=HTTPProvider(api_key=TRONGRID_API_KEY, timeout=20.0))
    # Nile endpoint (public); adjust if you use your own fullnode
    return Tron(provider=HTTPProvider(endpoint_uri="https://nile.trongrid.io", timeout=20.0))

def _get_comptroller(client: Tron):
    c = client.get_contract(UNITROLLER)
    c.abi = COMPTROLLER_ABI
    return c

def _get_jtoken(client: Tron, addr: str):
    j = client.get_contract(addr)
    j.abi = JTOKEN_ABI
    return j

# Helper: basic APR math from per-block rate (approx; TRON ~3s block)
def _per_block_to_apy(rate_per_block: int) -> float:
    # Very rough: ~28,800 blocks/day, ~10.5M/year if 3s blocks.
    # Safer: assume ~20,000 blocks/day => ~7.3M blocks/year
    blocks_year = 7_300_000
    r = float(rate_per_block) / 1e18
    return ( (1 + r) ** blocks_year - 1 ) * 100.0


class ChatMessage(BaseModel):
    message: str
    session_id: str = Field(default="default")

class ChatResponse(BaseModel):
    reply: str
    function_calls: List[Dict[str, Any]] = Field(default_factory=list)
    session_id: str
    timestamp: str

class WalletConnected(BaseModel):
    session_id: str
    address: str
    network: str = "nile"
    node_host: str = "unknown"

class WalletError(BaseModel):
    session_id: str
    error: str

class WalletDetails(BaseModel):
    session_id: str
    address: str
    trx_balance: str
    extra: Dict[str, Any] = {}

# ------------------------------------------------------------------------------
# Tools (the only “tool” your agent uses is: get_wallet_info)
#   Your React handles this by opening TronLink + building a snapshot.
# ------------------------------------------------------------------------------

@tool
def get_wallet_info(user_request: str) -> Dict[str, Any]:
    """Ask the frontend to ensure TronLink is connected and return a fresh wallet snapshot."""
    return {
        "type": "wallet_info_request",
        "message": "Connect/ensure wallet via TronLink and return address, TRX, resources."
    }

@tool
def trustlender_list_markets() -> Dict[str, Any]:
    """List JustLend markets with basic stats (symbol, collateral factor, supply/borrow rates, total borrows)."""
    client = _tron_client()
    comp = _get_comptroller(client)

    addrs = comp.functions.getAllMarkets()
    markets = []
    for addr in addrs:
        j = _get_jtoken(client, addr)
        sym = j.functions.symbol()
        s_rate = int(j.functions.supplyRatePerBlock())
        b_rate = int(j.functions.borrowRatePerBlock())
        exch = int(j.functions.exchangeRateStored())
        borrows = int(j.functions.totalBorrows())
        _, c_factor, _ = comp.functions.markets(addr)

        markets.append({
            "address": addr,
            "symbol": sym,
            "collateral_factor_mantissa": int(c_factor),
            "collateral_factor_pct": int(c_factor) / 1e16,  # 1e18 -> %
            "supply_rate_per_block": s_rate,
            "supply_apy_pct_approx": round(_per_block_to_apy(s_rate), 2),
            "borrow_rate_per_block": b_rate,
            "borrow_apy_pct_approx": round(_per_block_to_apy(b_rate), 2),
            "exchange_rate_mantissa": exch,
            "total_borrows_mantissa": borrows
        })
    return {"network": TRON_NETWORK, "unitroller": UNITROLLER, "count": len(markets), "markets": markets}


@tool
def trustlender_market_detail(symbol: str) -> Dict[str, Any]:
    """Detailed stats for a single market by symbol (case-insensitive), e.g. 'JUSDT'."""
    client = _tron_client()
    comp = _get_comptroller(client)

    target = None
    for addr in comp.functions.getAllMarkets():
        j = _get_jtoken(client, addr)
        sym = j.functions.symbol()
        if sym.lower() == symbol.lower():
            s_rate = int(j.functions.supplyRatePerBlock())
            b_rate = int(j.functions.borrowRatePerBlock())
            exch = int(j.functions.exchangeRateStored())
            borrows = int(j.functions.totalBorrows())
            _, c_factor, _ = comp.functions.markets(addr)
            target = {
                "address": addr,
                "symbol": sym,
                "collateral_factor_pct": int(c_factor) / 1e16,
                "supply_rate_per_block": s_rate,
                "supply_apy_pct_approx": round(_per_block_to_apy(s_rate), 2),
                "borrow_rate_per_block": b_rate,
                "borrow_apy_pct_approx": round(_per_block_to_apy(b_rate), 2),
                "exchange_rate_mantissa": exch,
                "total_borrows_mantissa": borrows
            }
            break

    if not target:
        return {"error": f"Market symbol '{symbol}' not found."}
    return {"network": TRON_NETWORK, "unitroller": UNITROLLER, "market": target}


@tool
def trustlender_user_position(address: str) -> Dict[str, Any]:
    """User-level position across markets + protocol-level liquidity/shortfall."""
    client = _tron_client()
    comp = _get_comptroller(client)

    positions = []
    for addr in comp.functions.getAllMarkets():
        j = _get_jtoken(client, addr)
        sym = j.functions.symbol()
        _, token_bal, borrow_bal, exchMant = j.functions.getAccountSnapshot(address)

        positions.append({
            "jtoken": addr,
            "symbol": sym,
            "token_balance_mantissa": int(token_bal),
            "borrow_balance_mantissa": int(borrow_bal),
            "exchange_rate_mantissa": int(exchMant),
        })

    _, liquidity, shortfall = comp.functions.getAccountLiquidity(address)
    return {
        "network": TRON_NETWORK,
        "address": address,
        "positions": positions,
        "liquidity_mantissa": int(liquidity),
        "shortfall_mantissa": int(shortfall)
    }

# ------------------------------------------------------------------------------
# LangChain tool-calling agent (kept simple — 1 tool, clear instruction)
#   We’ll embed this agent inside LangGraph nodes.
# ------------------------------------------------------------------------------

def build_tool_agent() -> AgentExecutor:
    llm = ChatOpenAI(model=MODEL, temperature=0.2, api_key=OPENAI_API_KEY)
    tools = [get_wallet_info]

    prompt = ChatPromptTemplate.from_messages([
        ("system",
            """
            You are SLATE, a TRON wallet assistant.
            You have access to the following:
            - profile: persistent memory of user facts (wallet_connected, wallet_address, trx_balance, etc.)

            You also have access to the following tools:
            - get_wallet_info           → ask frontend to connect wallet & push snapshot
            - trustlender_list_markets  → list JustLend markets
            - trustlender_market_detail → detail for a market
            - trustlender_user_position → user position across markets

            **RULES:**
            1. Always check the profile first for required facts (e.g., wallet_connected, wallet_address, trx_balance).
            2. If profile contains all the facts needed to answer the user’s question (e.g., trx_balance for balance queries), use those facts and respond directly without calling any tool.
            3. Only call get_wallet_info if:
            - profile is missing required facts (e.g., no trx_balance for a balance query), or
            - the user explicitly asks to refresh or update (e.g., 'refresh my balance').
            4. Keep answers concise and relevant to the user’s request. Respond with exactly one final message per user turn. Do not repeat or re-ask things you already know.
            5. For balance queries, explicitly check if profile.trx_balance exists and use it to respond unless a refresh is requested.
            6. If a JustLend tool result is enough, present a short, clear answer.
            """),
        ("system", "Current profile memory (JSON): {profile}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=True)

tool_agent = build_tool_agent()

# ------------------------------------------------------------------------------
# Memory extraction — dynamic, LLM-driven (not hardcoded regex)
#   Every user message is passed through this extractor; the result is merged
#   into {profile} and stored by LangGraph’s MemorySaver (per session_id).
# ------------------------------------------------------------------------------

class ProfileFacts(PydModel):
    facts: Dict[str, str] = PydField(default_factory=dict)
    forget: List[str] = PydField(default_factory=list)

def extract_facts(llm: ChatOpenAI, text: str, prior: Dict[str, str]) -> ProfileFacts:
    """
    Use LLM to pull ANY durable facts from the latest user message.
    We prefer structured output via function-calling; if that fails,
    we fall back to 'return JSON' parsing so the graph never crashes.
    """
    prompt = (
        "Extract durable profile facts from the user's latest message.\n"
        "Return a short JSON object with:\n"
        "  facts: {key: value, ...}  // name, location, wallet_connected, wallet_address, trx_balance, preferences, etc.\n"
        "  forget: [keys to delete]\n"
        "Only include stable facts you expect to be reused later.\n"
        f"Existing memory: {prior}\n\n"
        f"USER: {text}"
    )

    # 1) Preferred path: structured output via function-calling
    try:
        extractor = llm.with_structured_output(ProfileFacts, method="function_calling")
        print("🧠 [extract] Using structured output via function_calling")
        pf: ProfileFacts = extractor.invoke(prompt)
        print(f"🧠 [extract] Parsed (function_calling) -> facts={pf.facts} forget={pf.forget}")
        return pf
    except Exception as e:
        print(f"⚠️ [extract] function_calling structured output failed: {e}")

    # 2) Fallback path: ask for raw JSON and parse
    try:
        print("🧠 [extract] Falling back to raw JSON parse strategy")
        msg = llm.invoke(prompt + "\n\nReturn ONLY the JSON with keys 'facts' and 'forget'. No prose.")
        raw = msg.content.strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            js = json.loads(raw[start:end+1])
        else:
            js = {"facts": {}, "forget": []}
        pf = ProfileFacts(**js)
        print(f"🧠 [extract] Parsed (fallback) -> facts={pf.facts} forget={pf.forget}")
        return pf
    except Exception as e2:
        print(f"❌ [extract] Fallback JSON parse failed: {e2}")
        return ProfileFacts()  # never break the graph

# ------------------------------------------------------------------------------
# LangGraph state + nodes
#   We’ll use a two-step graph:
#     1) extract  → read user msg, update memory (profile)
#     2) assistant → run tool-agent with the new memory, produce reply & tool calls
# ------------------------------------------------------------------------------

class GraphState(PydModel):
    messages: List[Dict[str, str]] = PydField(default_factory=list)  # [{role, content}]
    profile: Dict[str, str] = PydField(default_factory=dict)

def node_extract(state: GraphState):
    llm = ChatOpenAI(model=MODEL, temperature=0.0, api_key=OPENAI_API_KEY)
    latest = next((m["content"] for m in reversed(state.messages) if m["role"] == "human"), "")
    if not latest:
        print("🧠 [extract] No human message found")
        return {}

    pf = extract_facts(llm, latest, state.profile)
    new_profile = dict(state.profile)
    for k in pf.forget:
        new_profile.pop(k, None)
    new_profile.update(pf.facts)

    print(f"🧠 [extract] Merged profile -> {new_profile}")  # <— extra log

    new_messages = list(state.messages)
    if pf.facts:
        remembered = ", ".join(f"{k}={v}" for k, v in pf.facts.items())
        new_messages.append({"role": "ai", "content": f"🧠 Noted for later: {remembered}"})

    return {"profile": new_profile, "messages": new_messages}


def node_assistant(state: GraphState):
    """Node 2 — call the tool agent with memory injected; surface function_calls."""
    # Rebuild LangChain’s chat_history format from our array of dicts
    chat_history = []
    for m in state.messages[:-1]:
        if m["role"] == "human":
            chat_history.append(("human", m["content"]))
        elif m["role"] == "ai":
            chat_history.append(("ai", m["content"]))
    latest_user = next((m["content"] for m in reversed(state.messages) if m["role"] == "human"), "")

    print(f"🧩 [assistant] profile={state.profile}")
    result = tool_agent.invoke({
        "input": latest_user,
        "chat_history": chat_history,
        "profile": state.profile,  # visible in the prompt
    })

    reply = result["output"]
    steps = result.get("intermediate_steps", [])
    print(f"🤖 [assistant] reply='{reply}'")
    print(f"🔧 [assistant] tool steps={len(steps)}")

    # Convert tool invocations into function_calls for the frontend
    function_calls = []
    for action, _obs in steps:
        if action.tool == "get_wallet_info":
            function_calls.append({"type": "wallet_info_request"})

    # Append reply
    msgs = list(state.messages) + [{"role": "ai", "content": reply}]
    # Save function_calls as a special synthetic ai message (so HTTP layer can find it)
    if function_calls:
        msgs.append({"role": "ai", "content": "__FUNCTION_CALLS__:" + str(function_calls)})

    return {"messages": msgs}

def build_graph():
    print("🧩 Building LangGraph...")
    g = StateGraph(GraphState)
    g.add_node("extract", node_extract)
    g.add_node("assistant", node_assistant)

    g.set_entry_point("extract")
    g.add_edge("extract", "assistant")
    g.add_edge("assistant", END)

    # MemorySaver = per-thread (session_id) checkpointing of state (messages + profile)
    checkpointer = MemorySaver()
    app_graph = g.compile(checkpointer=checkpointer)
    print("✅ Graph compiled with MemorySaver")
    return app_graph

graph = build_graph()

# ------------------------------------------------------------------------------
# Wallet callback endpoints (React posts here after popup/snapshot)
# ------------------------------------------------------------------------------

@app.post("/api/wallet/connected")
async def wallet_connected(evt: WalletConnected):
    s = sessions.setdefault(evt.session_id, {"chat_history": [], "profile": {}})
    s["wallet"] = {
        "address": evt.address,
        "network": evt.network,
        "node_host": evt.node_host,
        "connected_at": datetime.now().isoformat(),
    }
    # mirror to memory profile (so smalltalk can answer “am I connected?”)
    profile = s.setdefault("profile", {})
    profile["wallet_connected"] = "yes"
    profile["wallet_address"] = evt.address

    s["chat_history"].append({"role": "ai", "content": f"✅ Wallet connected: {evt.address} on {evt.network}"})
    print(f"🔗 [/wallet/connected] {evt.address} ({evt.network})")
    return {"ok": True}

@app.post("/api/wallet/details")
async def wallet_details(evt: WalletDetails):
    s = sessions.setdefault(evt.session_id, {"chat_history": [], "profile": {}})
    s["wallet_details"] = evt.dict()
    # mirror balance to profile memory
    profile = s.setdefault("profile", {})
    profile["trx_balance"] = evt.trx_balance

    s["chat_history"].append({"role": "ai", "content": f"📊 Wallet details updated for {evt.address}"})
    print(f"📥 [/wallet/details] stored snapshot for {evt.address}")
    return {"ok": True}

@app.post("/api/wallet/error")
async def wallet_error(evt: WalletError):
    s = sessions.setdefault(evt.session_id, {"chat_history": []})
    s["last_wallet_error"] = {"error": evt.error, "ts": datetime.now().isoformat()}
    s["chat_history"].append({"role": "ai", "content": f"❌ Wallet error: {evt.error}"})
    print(f"⚠️ [/wallet/error] {evt.error}")
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat()}

# ------------------------------------------------------------------------------
# /api/chat — drive the graph, return reply + function_calls (for your React)
# ------------------------------------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(msg: ChatMessage):
    print(f"\n💬 [CHAT] '{msg.message}'  (session={msg.session_id})")
    t0 = time.time()

    # Initialize server-side session (separate from graph’s memory)
    s = sessions.setdefault(msg.session_id, {"chat_history": [], "profile": {}})

    # Build graph input state: prior messages + this human turn
    state_in = GraphState(
        messages = s["chat_history"] + [{"role": "human", "content": msg.message}],
        profile  = s.get("profile", {})
    ).model_dump()

    # Run graph with thread_id = session_id  → MemorySaver will persist state
    result = graph.invoke(
        state_in,
        config={"configurable": {"thread_id": msg.session_id}}
    )

    # Unpack messages/profile from graph and store back into sessions
    s["profile"] = result.get("profile", s.get("profile", {}))
    new_messages: List[Dict[str, str]] = result["messages"]

    # Pull the last natural AI reply, and any staged function_calls
    reply = ""
    function_calls: List[Dict[str, Any]] = []
    for m in reversed(new_messages):
        if m["role"] == "ai" and m["content"].startswith("__FUNCTION_CALLS__:"):
            function_calls = eval(m["content"].split(":", 1)[1].strip())
            print(f"🧰 [CHAT] function_calls -> {function_calls}")
        elif m["role"] == "ai" and not reply:
            reply = m["content"]

    # Persist chat history (drop the synthetic function_calls line)
    s["chat_history"] = [m for m in new_messages if not m["content"].startswith("__FUNCTION_CALLS__:")]

    print(f"🧠 [CHAT] profile now: {s['profile']}")

    # UX pacing
    elapsed = time.time() - t0
    if elapsed < 1.5:
        await asyncio.sleep(1.5 - elapsed)

    return ChatResponse(
        reply=reply or "Okay.",
        function_calls=function_calls,
        session_id=msg.session_id,
        timestamp=datetime.now().isoformat(),
    )

# ------------------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
