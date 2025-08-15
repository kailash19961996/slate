"""
SLATE Backend (Mainnet, Read-Only) — LangGraph + Wallet memory + JustLend tools
- Uses TronGrid mainnet with TRONGRID_API_KEY
- Exposes 3 JustLend read-only tools and forwards their JSON to the frontend as function_calls
- Keeps the frontend contract: { reply, function_calls }
"""

import os
import time, random
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv
import json

# LangChain / LangGraph
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Tron / JustLend deps
from tronpy import Tron
from tronpy.providers import HTTPProvider

import math
from requests.exceptions import HTTPError
# ------------------------------------------------------------------------------
# Boot & globals
# ------------------------------------------------------------------------------

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPEN_AI_MODEL", "gpt-4o-mini")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set.")
print(f"🤖 Model: {MODEL}")

# 👉 Mainnet by default (read-only)
TRON_NETWORK = os.getenv("TRON_NETWORK", "mainnet").lower()   # 'mainnet' | 'nile'
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")
if TRON_NETWORK == "mainnet" and not TRONGRID_API_KEY:
    raise RuntimeError("TRONGRID_API_KEY is required when TRON_NETWORK=mainnet")
print(f"🌐 TRON network: {TRON_NETWORK}")

# Rate-limit tuning (env overrides allowed)
JL_LIST_LIMIT_DEFAULT = int(os.getenv("JL_LIST_LIMIT_DEFAULT", "6"))   # show first N markets
JL_PER_MARKET_DELAY_MS = int(os.getenv("JL_PER_MARKET_DELAY_MS", "250"))  # sleep between markets
JL_MAX_ATTEMPTS = int(os.getenv("JL_MAX_ATTEMPTS", "4"))               # retries per call
JL_BASE_DELAY_MS = int(os.getenv("JL_BASE_DELAY_MS", "250"))           # base backoff
JL_CACHE_TTL_SEC = int(os.getenv("JL_CACHE_TTL_SEC", "120"))           # cache markets for 2 min


# Unitroller (proxy) address for JustLend.
# NOTE: You can override with JL_UNITROLLER_MAIN in .env.
# The default below is a known mainnet Unitroller for JustLend DAO at time of writing.
JL_UNITROLLER_MAIN = os.getenv("JL_UNITROLLER_MAIN", "TGjYzgCyPobsNS9n6WcbdLVR9dH7mWqFx7")
# When switching to Nile, set JL_UNITROLLER_NILE accordingly.
JL_UNITROLLER_NILE = os.getenv("JL_UNITROLLER_NILE", "")

def _resolve_unitroller() -> str:
    if TRON_NETWORK == "mainnet":
        print(f"🏛️ [jl] Using MAINNET Unitroller={JL_UNITROLLER_MAIN}")
        return JL_UNITROLLER_MAIN
    if not JL_UNITROLLER_NILE:
        # Helpful error instead of 500 — but we’re mainnet-first now
        raise RuntimeError("JL_UNITROLLER_NILE is required if TRON_NETWORK=nile")
    print(f"🏛️ [jl] Using NILE Unitroller={JL_UNITROLLER_NILE}")
    return JL_UNITROLLER_NILE

app = FastAPI(title="SLATE Backend", version="10.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory session store for demos
sessions: Dict[str, Dict[str, Any]] = {}

# ------------------------------------------------------------------------------
# Frontend contract models
# ------------------------------------------------------------------------------

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
    network: str = "mainnet"
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
# Minimal ABIs (enough for listing/detail/position)
# ------------------------------------------------------------------------------

COMPTROLLER_ABI = [
    {"name":"getAllMarkets","type":"function","inputs":[],"outputs":[{"name":"","type":"address[]"}],"stateMutability":"view","constant":True},
    {"name":"markets","type":"function","inputs":[{"name":"jToken","type":"address"}],
     "outputs":[{"name":"isListed","type":"bool"},{"name":"collateralFactorMantissa","type":"uint256"},{"name":"isComped","type":"bool"}],
     "stateMutability":"view","constant":True},
    {"name":"getAccountLiquidity","type":"function","inputs":[{"name":"account","type":"address"}],
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

# ------------------------------------------------------------------------------
# Tron client + helpers
# ------------------------------------------------------------------------------

def _tron_client() -> Tron:
    """Create a Tron client for the configured network."""
    if TRON_NETWORK == "mainnet":
        print("🔌 [tron] TronGrid mainnet provider (read-only)")
        # Uses API key header automatically
        return Tron(provider=HTTPProvider(api_key=TRONGRID_API_KEY, timeout=20.0))
    print("🔌 [tron] Nile public fullnode (dev)")
    return Tron(provider=HTTPProvider(endpoint_uri="https://nile.trongrid.io", timeout=20.0))

def _get_comptroller(client: Tron):
    unitroller = _resolve_unitroller()
    c = client.get_contract(unitroller)
    c.abi = COMPTROLLER_ABI
    return c

def _get_jtoken(client: Tron, addr: str):
    j = client.get_contract(addr)
    j.abi = JTOKEN_ABI
    return j

def _per_block_to_apy(rate_per_block: int) -> float:
    """Approximate APY from per-block rate. ~7.3M blocks/year (~3s blocks)."""
    blocks_year = 7_300_000
    r = float(rate_per_block) / 1e18
    return ((1 + r) ** blocks_year - 1) * 100.0

def _sleep_ms(ms: int): time.sleep(ms / 1000.0)

def _with_retries(fn, *, label: str, max_attempts: int, base_delay_ms: int):
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            print(f"⏳ [retry] {label} attempt {attempt}/{max_attempts} -> {type(e).__name__} {code or ''}: {e}")
            if attempt >= max_attempts:
                raise
            # exponential backoff + jitter
            delay = int(base_delay_ms * (2 ** (attempt - 1)) * (1 + 0.25 * random.random()))
            print(f"… sleeping {delay}ms")
            _sleep_ms(delay)

# Simple in‑memory cache
_MARKETS_CACHE: Tuple[float, dict] | None = None  # (ts, payload)
def _cache_get() -> dict | None:
    global _MARKETS_CACHE
    if not _MARKETS_CACHE: return None
    ts, payload = _MARKETS_CACHE
    if (time.time() - ts) <= JL_CACHE_TTL_SEC:
        print("🗄️ [cache] serving cached markets payload")
        return payload
    return None

def _cache_set(payload: dict):
    global _MARKETS_CACHE
    _MARKETS_CACHE = (time.time(), payload)

# ------------------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------------------

@tool
def get_wallet_info(user_request: str) -> Dict[str, Any]:
    """Ask the frontend to ensure TronLink is connected and return a fresh wallet snapshot."""
    print("🛠️ [tool] get_wallet_info:", user_request)
    return {"type": "wallet_info_request", "message": "Connect/ensure wallet via TronLink."}

@tool
def trustlender_list_markets(limit: int | None = None) -> Dict[str, Any]:
    """
    List JustLend markets on MAINNET with throttling, retries, and caching.

    Params:
      - limit (optional): only fetch the first N markets (defaults via JL_LIST_LIMIT_DEFAULT).
    """
    print("🛠️ [tool] trustlender_list_markets (begin)")

    # 0) Serve from cache if fresh and limit is None or >= cached size
    if limit is None: limit = JL_LIST_LIMIT_DEFAULT
    cached = _cache_get()
    if cached and (limit <= cached.get("count", 0)):
        # Shallow copy so we can slice without mutating cache
        out = dict(cached)
        out["markets"] = out["markets"][:limit]
        out["count"] = len(out["markets"])
        print(f"✅ [tool] served {out['count']} markets from cache")
        return out

    try:
        client = _tron_client()
        comp = _get_comptroller(client)

        # 1) Get market addresses (with retry)
        addrs = _with_retries(
            lambda: comp.functions.getAllMarkets(),
            label="getAllMarkets",
            max_attempts=JL_MAX_ATTEMPTS,
            base_delay_ms=JL_BASE_DELAY_MS
        )
        print(f"📜 [jl] getAllMarkets -> {len(addrs)} markets (mainnet)")

        # 2) Limit for demo / throttle
        if isinstance(limit, int) and limit > 0:
            addrs = addrs[:limit]
        else:
            limit = len(addrs)
        print(f"🔎 [jl] fetching first {limit} markets")

        markets = []
        for i, addr in enumerate(addrs, start=1):
            print(f"➡️ [jl] market {i}/{limit}: {addr}")
            try:
                j = _with_retries(
                    lambda: _get_jtoken(client, addr),
                    label=f"get_contract {addr}",
                    max_attempts=JL_MAX_ATTEMPTS,
                    base_delay_ms=JL_BASE_DELAY_MS
                )
                sym = _with_retries(lambda: j.functions.symbol(),
                                    label=f"symbol {addr}",
                                    max_attempts=JL_MAX_ATTEMPTS,
                                    base_delay_ms=JL_BASE_DELAY_MS)
                s_rate = int(_with_retries(lambda: j.functions.supplyRatePerBlock(),
                                           label=f"supplyRate {sym}",
                                           max_attempts=JL_MAX_ATTEMPTS,
                                           base_delay_ms=JL_BASE_DELAY_MS))
                b_rate = int(_with_retries(lambda: j.functions.borrowRatePerBlock(),
                                           label=f"borrowRate {sym}",
                                           max_attempts=JL_MAX_ATTEMPTS,  # <-- typos fixed below in note
                                           base_delay_ms=JL_BASE_DELAY_MS))
                exch  = int(_with_retries(lambda: j.functions.exchangeRateStored(),
                                          label=f"exchangeRate {sym}",
                                          max_attempts=JL_MAX_ATTEMPTS,
                                          base_delay_ms=JL_BASE_DELAY_MS))
                bor   = int(_with_retries(lambda: j.functions.totalBorrows(),
                                          label=f"totalBorrows {sym}",
                                          max_attempts=JL_MAX_ATTEMPTS,
                                          base_delay_ms=JL_BASE_DELAY_MS))
                _, c_factor, _ = _with_retries(lambda: comp.functions.markets(addr),
                                               label=f"markets {sym}",
                                               max_attempts=JL_MAX_ATTEMPTS,
                                               base_delay_ms=JL_BASE_DELAY_MS)

                entry = {
                    "address": addr,
                    "symbol": sym,
                    "collateral_factor_mantissa": int(c_factor),
                    "collateral_factor_pct": int(c_factor) / 1e16,
                    "supply_rate_per_block": s_rate,
                    "supply_apy_pct_approx": round(_per_block_to_apy(s_rate), 2),
                    "borrow_rate_per_block": b_rate,
                    "borrow_apy_pct_approx": round(_per_block_to_apy(b_rate), 2),
                    "exchange_rate_mantissa": exch,
                    "total_borrows_mantissa": bor
                }
                markets.append(entry)
                print(f"✅ [jl] ok {sym} | supply≈{entry['supply_apy_pct_approx']}% borrow≈{entry['borrow_apy_pct_approx']}%")
            except Exception as inner:
                print(f"⚠️ [jl] market failed {addr}: {type(inner).__name__}: {inner}")

            # 3) Throttle between markets to avoid 429s
            _sleep_ms(JL_PER_MARKET_DELAY_MS)

        out = {
            "network": "mainnet",
            "unitroller": JL_UNITROLLER_MAIN,
            "count": len(markets),
            "markets": markets
        }

        # 4) Fill cache with the **full** list if we managed to fetch all markets
        #    (or at least more than we had before). Simple policy: cache whatever we got.
        _cache_set({
            "network": "mainnet",
            "unitroller": JL_UNITROLLER_MAIN,
            "count": len(markets),
            "markets": list(markets)  # store full slice we fetched
        })

        print(f"✅ [tool] trustlender_list_markets done — returned {len(markets)} rows")
        return out

    except Exception as e:
        print("❌ [tool] trustlender_list_markets error:", repr(e))
        return {"error": f"{type(e).__name__}: {e}"}


@tool
def trustlender_market_detail(symbol: str) -> Dict[str, Any]:
    """Detailed stats for a single JustLend market by symbol (e.g., JUSDT)."""
    print("🛠️ [tool] trustlender_market_detail:", symbol)
    try:
        client = _tron_client()
        comp = _get_comptroller(client)
        target = None
        for addr in comp.functions.getAllMarkets():
            j = _get_jtoken(client, addr)
            sym = j.functions.symbol()
            if sym.lower() == symbol.lower():
                srate = int(j.functions.supplyRatePerBlock())
                brate = int(j.functions.borrowRatePerBlock())
                exch  = int(j.functions.exchangeRateStored())
                bor   = int(j.functions.totalBorrows())
                _, c_factor, _ = comp.functions.markets(addr)
                target = {
                    "address": addr,
                    "symbol": sym,
                    "collateral_factor_pct": int(c_factor) / 1e16,
                    "supply_rate_per_block": srate,
                    "supply_apy_pct_approx": round(_per_block_to_apy(srate), 2),
                    "borrow_rate_per_block": brate,
                    "borrow_apy_pct_approx": round(_per_block_to_apy(brate), 2),
                    "exchange_rate_mantissa": exch,
                    "total_borrows_mantissa": bor
                }
                break
        if not target:
            print("⚠️ [tool] symbol not found:", symbol)
            return {"error": f"Market symbol '{symbol}' not found on {TRON_NETWORK}.", "network": TRON_NETWORK}
        print("✅ [tool] market_detail:", target["symbol"])
        return {"network": TRON_NETWORK, "unitroller": _resolve_unitroller(), "market": target}
    except Exception as e:
        print("❌ [tool] trustlender_market_detail error:", repr(e))
        return {"error": f"{type(e).__name__}: {e}", "network": TRON_NETWORK}

@tool
def trustlender_user_position(address: str) -> Dict[str, Any]:
    """User-level position across markets + account liquidity/shortfall."""
    print("🛠️ [tool] trustlender_user_position:", address)
    try:
        client = _tron_client()
        comp = _get_comptroller(client)
        positions = []
        for addr in comp.functions.getAllMarkets():
            try:
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
            except Exception as inner:
                print(f"⚠️ [jl] snapshot decode failed for {addr}: {inner}")
        _, liquidity, shortfall = comp.functions.getAccountLiquidity(address)
        out = {
            "network": TRON_NETWORK,
            "address": address,
            "positions": positions,
            "liquidity_mantissa": int(liquidity),
            "shortfall_mantissa": int(shortfall)
        }
        print(f"✅ [tool] user_position -> n={len(positions)} liq={out['liquidity_mantissa']} short={out['shortfall_mantissa']}")
        return out
    except Exception as e:
        print("❌ [tool] trustlender_user_position error:", repr(e))
        return {"error": f"{type(e).__name__}: {e}", "network": TRON_NETWORK}

# ------------------------------------------------------------------------------
# Agent (profile-aware; passes tool results to UI)
# ------------------------------------------------------------------------------

def build_tool_agent() -> AgentExecutor:
    llm = ChatOpenAI(model=MODEL, temperature=0.2, api_key=OPENAI_API_KEY)
    tools = [get_wallet_info, trustlender_list_markets, trustlender_market_detail, trustlender_user_position]

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """
         You are SLATE, a TRON wallet + JustLend assistant (MAINNET, read-only).
         TOOLS:
           - get_wallet_info           → ask frontend to connect wallet & push snapshot
           - trustlender_list_markets  → list JustLend markets
           - trustlender_market_detail → details for a market (symbol)
           - trustlender_user_position → user-level position
         RULES:
         1) Check the profile JSON before calling tools; if facts exist, answer directly.
         2) Only call get_wallet_info when wallet facts are missing or user asked to refresh.
         3) After any JustLend tool, summarize clearly.
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
# Memory extraction (durable facts)
# ------------------------------------------------------------------------------

from pydantic import BaseModel as PydModel, Field as PydField

class ProfileFacts(PydModel):
    facts: Dict[str, str] = PydField(default_factory=dict)
    forget: List[str] = PydField(default_factory=list)

def extract_facts(llm: ChatOpenAI, text: str, prior: Dict[str, str]) -> ProfileFacts:
    prompt = (
        "Extract durable profile facts from the user's latest message.\n"
        "Return JSON: {facts:{}, forget:[]} where facts can include wallet_connected, wallet_address, trx_balance, preferences, etc.\n"
        f"Existing memory: {prior}\n\nUSER: {text}"
    )
    try:
        extractor = llm.with_structured_output(ProfileFacts, method="function_calling")
        print("🧠 [extract] Using structured output via function_calling")
        pf: ProfileFacts = extractor.invoke(prompt)
        print(f"🧠 [extract] Parsed -> facts={pf.facts} forget={pf.forget}")
        return pf
    except Exception as e:
        print(f"⚠️ [extract] structured output failed: {e}")
    try:
        print("🧠 [extract] Fallback raw JSON parse")
        msg = llm.invoke(prompt + "\nReturn ONLY the JSON with keys 'facts' and 'forget'.")
        raw = msg.content.strip()
        start = raw.find("{"); end = raw.rfind("}")
        js = json.loads(raw[start:end+1]) if (start != -1 and end != -1) else {"facts": {}, "forget": []}
        pf = ProfileFacts(**js)
        print(f"🧠 [extract] Parsed (fallback) -> facts={pf.facts} forget={pf.forget}")
        return pf
    except Exception as e2:
        print(f"❌ [extract] Fallback JSON parse failed: {e2}")
        return ProfileFacts()

# ------------------------------------------------------------------------------
# LangGraph
# ------------------------------------------------------------------------------

class GraphState(PydModel):
    messages: List[Dict[str, str]] = PydField(default_factory=list)
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
    print(f"🧠 [extract] Merged profile -> {new_profile}")
    new_messages = list(state.messages)
    if pf.facts:
        remembered = ", ".join(f"{k}={v}" for k, v in pf.facts.items())
        new_messages.append({"role": "ai", "content": f"🧠 Noted for later: {remembered}"})
    return {"profile": new_profile, "messages": new_messages}

def node_assistant(state: GraphState):
    chat_history = []
    for m in state.messages[:-1]:
        chat_history.append(("human", m["content"]) if m["role"] == "human" else ("ai", m["content"]))
    latest_user = next((m["content"] for m in reversed(state.messages) if m["role"] == "human"), "")
    print(f"🧩 [assistant] profile={state.profile}")
    result = tool_agent.invoke({"input": latest_user, "chat_history": chat_history, "profile": state.profile})
    reply = result["output"]
    steps = result.get("intermediate_steps", [])
    print(f"🤖 [assistant] reply='{reply}'")
    print(f"🔧 [assistant] tool steps={len(steps)}")

    function_calls = []
    for action, obs in steps:
        if action.tool == "get_wallet_info":
            function_calls.append({"type": "wallet_info_request"})
        elif action.tool in ("trustlender_list_markets","trustlender_market_detail","trustlender_user_position"):
            function_calls.append({"type": action.tool, "args": action.tool_input, "result": obs})

    msgs = list(state.messages) + [{"role": "ai", "content": reply}]
    if function_calls:
        msgs.append({"role": "ai", "content": "__FUNCTION_CALLS__:" + str(function_calls)})
    return {"messages": msgs}

def build_graph():
    print("🧩 Building LangGraph…")
    g = StateGraph(GraphState)
    g.add_node("extract", node_extract)
    g.add_node("assistant", node_assistant)
    g.set_entry_point("extract")
    g.add_edge("extract", "assistant")
    g.add_edge("assistant", END)
    app_graph = g.compile(checkpointer=MemorySaver())
    print("✅ Graph compiled with MemorySaver")
    return app_graph

graph = build_graph()

# ------------------------------------------------------------------------------
# Wallet callbacks (frontend posts here after popup/snapshot)
# ------------------------------------------------------------------------------

@app.post("/api/wallet/connected")
async def wallet_connected(evt: WalletConnected):
    s = sessions.setdefault(evt.session_id, {"chat_history": [], "profile": {}})
    s["wallet"] = {"address": evt.address, "network": evt.network, "node_host": evt.node_host, "connected_at": datetime.now().isoformat()}
    profile = s.setdefault("profile", {})
    profile["wallet_connected"] = "yes"; profile["wallet_address"] = evt.address
    s["chat_history"].append({"role": "ai", "content": f"✅ Wallet connected: {evt.address} on {evt.network}"})
    print(f"🔗 [/wallet/connected] (REFRESH) address={evt.address} network={evt.network} node={evt.node_host}")
    return {"ok": True}

@app.post("/api/wallet/details")
async def wallet_details(evt: WalletDetails):
    s = sessions.setdefault(evt.session_id, {"chat_history": [], "profile": {}})
    s["wallet_details"] = evt.dict()
    profile = s.setdefault("profile", {})
    profile["trx_balance"] = evt.trx_balance
    profile["trx_balance_updated_at"] = datetime.now().isoformat()
    s["chat_history"].append({"role": "ai", "content": f"📊 Wallet details updated for {evt.address}"})
    print(f"📥 [/wallet/details] (REFRESH) stored snapshot for {evt.address} trx={evt.trx_balance}")
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
# /api/chat — drives the graph, returns reply + function_calls
# ------------------------------------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(msg: ChatMessage):
    print(f"\n💬 [CHAT] '{msg.message}'  (session={msg.session_id})")
    t0 = time.time()

    s = sessions.setdefault(msg.session_id, {"chat_history": [], "profile": {}})
    state_in = {
        "messages": s["chat_history"] + [{"role": "human", "content": msg.message}],
        "profile": s.get("profile", {})
    }

    result = graph.invoke(state_in, config={"configurable": {"thread_id": msg.session_id}})
    s["profile"] = result.get("profile", s.get("profile", {}))
    new_messages: List[Dict[str, str]] = result["messages"]

    reply = ""
    function_calls: List[Dict[str, Any]] = []
    for m in reversed(new_messages):
        if m["role"] == "ai" and m["content"].startswith("__FUNCTION_CALLS__:"):
            function_calls = eval(m["content"].split(":", 1)[1].strip())
            print(f"🧰 [CHAT] function_calls -> {function_calls}")
        elif m["role"] == "ai" and not reply:
            reply = m["content"]

    s["chat_history"] = [m for m in new_messages if not m["content"].startswith("__FUNCTION_CALLS__:")]
    print(f"🧠 [CHAT] profile now: {s['profile']}")

    elapsed = time.time() - t0
    if elapsed < 1.0:
        await asyncio.sleep(1.0 - elapsed)

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
