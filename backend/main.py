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

            **RULES:**
            1. Always check the profile first for required facts (e.g., wallet_connected, wallet_address, trx_balance).
            2. If profile contains all the facts needed to answer the user’s question (e.g., trx_balance for balance queries), use those facts and respond directly without calling any tool.
            3. Only call get_wallet_info if:
            - profile is missing required facts (e.g., no trx_balance for a balance query), or
            - the user explicitly asks to refresh or update (e.g., 'refresh my balance').
            4. Keep answers concise and relevant to the user’s request.
            5. Respond with exactly one final message per user turn. Do not repeat or re-ask things you already know.
            6. For balance queries, explicitly check if profile.trx_balance exists and use it to respond unless a refresh is requested.
            """),
        ("system", "Current profile memory (JSON): {profile}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=True)

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
