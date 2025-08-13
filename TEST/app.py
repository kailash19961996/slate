"""
LangGraph Multi-Tool Agent (FastAPI)
------------------------------------
• 5 real-world tools (calculator, web_search, weather, fx_rate, crypto_price)
• Dynamic tool discovery (semantic search over tool descriptions)
• Slightly complex workflow: normal chat ↔ tool use (may chain multiple tools)
• Visual trace output: step list + Mermaid sequence diagram (client can render)

Run:
  uvicorn app:app --reload --port 8000

Env:
  OPENAI_API_KEY=sk-...

Install:
  pip install -U fastapi uvicorn pydantic requests langchain langgraph langchain-openai tiktoken python-dotenv

Test:
  curl -X POST http://localhost:8000/agent/chat -H 'Content-Type: application/json' \
       -d '{"text":"what\'s the weather in London and convert 20 EUR to USD as well","session_id":"demo1"}'

Client renders `mermaid` and `events` to show the flow visually.
"""




from __future__ import annotations


from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


import os
import time
import math
import json
import uuid
import textwrap
from typing import Any, Dict, List, Optional, Tuple

import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field

from langchain.schema import HumanMessage, SystemMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# -------------------------
# Utilities
# -------------------------

def safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        return float(x)
    except Exception:
        return default

# -------------------------
# Tool Implementations (5 real‑world tools)
# -------------------------

@tool("calculator", return_direct=False)
def calculator(expr: str) -> str:
    """Evaluate a simple math expression safely. Supports +,-,*,/,**,(), power.
    Example: "(2+3)*4" -> "20".
    """
    allowed = set("0123456789+-*/(). eE%**) ")
    # Tiny sanitizer (still keep it minimal). Remove disallowed chars.
    expr_clean = "".join(ch for ch in expr if ch in allowed)
    try:
        # Limit builtins
        result = eval(expr_clean, {"__builtins__": {"abs": abs, "round": round, "math": math}}, {})
        return str(result)
    except Exception as e:
        return f"Calculator error: {e}"

@tool("web_search", return_direct=False)
def web_search(query: str, k: int = 3) -> str:
    """Lightweight web search via DuckDuckGo HTML endpoint (no API key). Returns top K titles+links.
    Real‑world: swap with Google/SerpAPI for reliability.
    """
    try:
        url = "https://duckduckgo.com/html/"
        resp = requests.post(url, data={"q": query}, timeout=10)
        html = resp.text
        # Ultra-light parse
        results: List[Tuple[str, str]] = []
        for frag in html.split("result__a"):
            if "href=\"" in frag:
                link = frag.split("href=\"")[1].split("\"")[0]
                title = frag.split(">")[1].split("<")[0]
                if link.startswith("http"):
                    results.append((title, link))
            if len(results) >= k:
                break
        if not results:
            return "No results"
        return json.dumps([{"title": t, "url": u} for t, u in results], ensure_ascii=False)
    except Exception as e:
        return f"Search error: {e}"

@tool("get_weather", return_direct=False)
def get_weather(city: str) -> str:
    """Get current weather (°C) via Open‑Meteo geocoding + forecast (no API key). Input: city name.
    Returns a short JSON with temperature and description if available.
    """
    try:
        geo = requests.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}, timeout=10).json()
        if not geo.get("results"):
            return json.dumps({"city": city, "error": "not found"})
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        forecast = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=10).json()
        cw = forecast.get("current_weather", {})
        return json.dumps({"city": geo["results"][0]["name"], "temp_c": cw.get("temperature"), "windspeed": cw.get("windspeed")})
    except Exception as e:
        return json.dumps({"city": city, "error": str(e)})

@tool("fx_rate", return_direct=False)
def fx_rate(base: str, quote: str, amount: Optional[float] = None) -> str:
    """Get a foreign exchange rate via exchangerate.host (no key). If amount provided, also convert.
    Example: base=EUR, quote=USD, amount=20 -> {rate, converted}
    """
    try:
        url = f"https://api.exchangerate.host/latest?base={base.upper()}&symbols={quote.upper()}"
        data = requests.get(url, timeout=10).json()
        rate = data.get("rates", {}).get(quote.upper())
        if rate is None:
            return json.dumps({"error": "rate not found"})
        out: Dict[str, Any] = {"base": base.upper(), "quote": quote.upper(), "rate": rate}
        if amount is not None:
            out["amount"] = amount
            out["converted"] = amount * rate
        return json.dumps(out)
    except Exception as e:
        return json.dumps({"error": str(e)})

@tool("crypto_price", return_direct=False)
def crypto_price(symbol: str, vs: str = "usd") -> str:
    """Get a crypto spot price from CoinGecko (no key). symbol like 'btc', 'eth', 'trx'.
    """
    try:
        ids_map = {"btc": "bitcoin", "eth": "ethereum", "trx": "tron", "usdt": "tether"}
        coin_id = ids_map.get(symbol.lower(), symbol.lower())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={vs}"
        data = requests.get(url, timeout=10).json()
        price = data.get(coin_id, {}).get(vs.lower())
        if price is None:
            return json.dumps({"error": "price not found"})
        return json.dumps({"symbol": symbol.lower(), "vs": vs.lower(), "price": price})
    except Exception as e:
        return json.dumps({"error": str(e)})

ALL_TOOLS = [calculator, web_search, get_weather, fx_rate, crypto_price]

# Tool catalog for semantic search
TOOL_CATALOG = [
    {
        "name": "calculator",
        "description": "Do math like add/subtract/multiply/divide; useful for numbers or formulas.",
        "schema": {"expr": "string math expression"},
    },
    {
        "name": "web_search",
        "description": "Search the web for up-to-date info, news, or links when knowledge is missing.",
        "schema": {"query": "string"},
    },
    {
        "name": "get_weather",
        "description": "Get current temperature and wind for a city using Open-Meteo.",
        "schema": {"city": "string"},
    },
    {
        "name": "fx_rate",
        "description": "Get FX rate and convert an amount between currencies like EUR→USD.",
        "schema": {"base": "string", "quote": "string", "amount": "number?"},
    },
    {
        "name": "crypto_price",
        "description": "Get live crypto price like BTC, ETH, TRX in a fiat currency.",
        "schema": {"symbol": "string", "vs": "string?"},
    },
]

# -------------------------
# Dynamic Tool Discovery (semantic search over tool descriptions)
# -------------------------

def find_relevant_tools(user_query: str, k: int = 3) -> List[str]:
    """Return top-k tool names based on embedding similarity; fallback to keyword rank."""
    try:
        emb = OpenAIEmbeddings(model="text-embedding-3-small")
        qv = emb.embed_query(user_query)
        scored: List[Tuple[float, str]] = []
        for t in TOOL_CATALOG:
            tv = emb.embed_query(t["description"])  # quick & simple
            # cosine similarity
            num = sum(a*b for a, b in zip(qv, tv))
            den = math.sqrt(sum(a*a for a in qv)) * math.sqrt(sum(b*b for b in tv))
            sim = num/den if den else 0.0
            scored.append((sim, t["name"]))
        scored.sort(reverse=True)
        return [name for _, name in scored[:k]]
    except Exception:
        # Fallback: naive keyword heuristics
        q = user_query.lower()
        ranking = []
        if any(w in q for w in ["weather", "temperature", "wind", "rain", "forecast"]):
            ranking.append("get_weather")
        if any(w in q for w in ["price", "btc", "eth", "trx", "crypto"]):
            ranking.append("crypto_price")
        if any(w in q for w in ["eur", "usd", "gbp", "rate", "convert", "fx", "currency"]):
            ranking.append("fx_rate")
        if any(w in q for w in ["search", "news", "google", "find", "link"]):
            ranking.append("web_search")
        if any(w in q for w in ["sum", "add", "minus", "multiply", "+", "-", "*", "/", "**", "calc"]):
            ranking.append("calculator")
        # Ensure at least web_search as last resort
        if "web_search" not in ranking:
            ranking.append("web_search")
        return ranking[:k]

# Expose a tool to let the LLM ask for relevant tools
@tool("search_available_tools", return_direct=False)
def search_available_tools(user_request: str, top_k: int = 3) -> str:
    """LLM uses this to discover which tools are likely helpful for the current question."""
    names = find_relevant_tools(user_request, k=top_k)
    details = [t for t in TOOL_CATALOG if t["name"] in names]
    return json.dumps(details, ensure_ascii=False)

DISCOVERY_TOOL = [search_available_tools]

# -------------------------
# LangGraph State & Nodes
# -------------------------

class AgentState(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    discovered_tools: List[str] = Field(default_factory=list)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
llm_base = ChatOpenAI(model=MODEL_NAME, temperature=0, api_key=OPENAI_API_KEY)

# Node 1: Planner/Assistant with ONLY the discovery tool
planner_llm = llm_base.bind_tools(DISCOVERY_TOOL)

# Node 2: Executor/Assistant with ALL tools
executor_llm = llm_base.bind_tools(ALL_TOOLS)

SYSTEM_PROMPT = (
    "You are an orchestrator AI. First, decide if tools are needed.\n"
    "If the user asks a question requiring fresh facts, calculations, prices, weather, or conversions:\n"
    "  1) Call search_available_tools with the user's request to see tool options.\n"
    "  2) Then call the most relevant tool(s). You may chain multiple tool calls.\n"
    "If no tools are needed, reply normally.\n"
    "Always return a concise, friendly answer."
)


def planner_node(state: AgentState) -> AgentState:
    msgs = [SystemMessage(content=SYSTEM_PROMPT)] + [HumanMessage(content=m["content"]) for m in state.messages]
    res = planner_llm.invoke(msgs)
    state.messages.append({"role": "assistant", "content": res.content})
    # Log tool call if any
    if res.tool_calls:
        for tc in res.tool_calls:
            state.trace.append({"type": "tool_call", "who": "planner", "tool": tc["name"], "args": tc["args"]})
            tool_result = None
            if tc["name"] == "search_available_tools":
                tool_result = search_available_tools.invoke(tc["args"])  # direct call
                # Update discovered tools list
                try:
                    details = json.loads(tool_result)
                    state.discovered_tools = [d["name"] for d in details]
                except Exception:
                    state.discovered_tools = []
            else:
                tool_result = "(unknown discovery tool)"
            state.trace.append({"type": "tool_result", "who": "planner", "tool": tc["name"], "result": tool_result})
            state.messages.append({"role": "tool", "name": tc["name"], "content": tool_result})
    return state


def executor_node(state: AgentState) -> AgentState:
    # Include a system hint listing discovered tools to bias the model
    hint = "\nDiscovered tools available now: " + ", ".join(state.discovered_tools or [t["name"] for t in TOOL_CATALOG])
    msgs = [SystemMessage(content=SYSTEM_PROMPT + hint)]
    # Rehydrate prior conversational messages and the planner output
    for m in state.messages:
        if m.get("role") == "tool":
            # Skip raw tool messages in the prompt; they were added right after tool use
            continue
        role = m.get("role", "user")
        if role == "assistant":
            msgs.append(SystemMessage(content=m.get("content", "")))
        else:
            msgs.append(HumanMessage(content=m.get("content", "")))
    res = executor_llm.invoke(msgs)
    state.messages.append({"role": "assistant", "content": res.content})
    if res.tool_calls:
        # Execute tool calls sequentially; allow multiple
        for tc in res.tool_calls:
            name = tc["name"]
            args = tc.get("args", {})
            state.trace.append({"type": "tool_call", "who": "executor", "tool": name, "args": args})
            # Dispatch
            try:
                tool_obj = next(t for t in ALL_TOOLS if t.name == name)
                result = tool_obj.invoke(args)
            except StopIteration:
                result = f"Unknown tool: {name}"
            except Exception as e:
                result = f"Tool error: {e}"
            state.trace.append({"type": "tool_result", "who": "executor", "tool": name, "result": result})
            state.messages.append({"role": "tool", "name": name, "content": result})
        # After tools, let the model summarize final answer (no more tool bindings)
        final = llm_base.invoke([
            SystemMessage(content="Summarize the results for the user in simple, friendly language."),
            HumanMessage(content=json.dumps({"trace": state.trace[-6:], "last_tool_results": [m for m in state.messages if m.get("role") == "tool"][-3:]})),
        ])
        state.messages.append({"role": "assistant", "content": final.content})
    return state


def should_continue(state: AgentState) -> str:
    """Simple controller: if we saw any executor tool calls, we already summarized; end. Otherwise end."""
    return END

# Wire the graph
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.set_entry_point("planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", END)

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)

# -------------------------
# Mermaid Diagram Builder
# -------------------------

def trace_to_mermaid(events: List[Dict[str, Any]], session_id: str) -> str:
    """Build a Mermaid sequence diagram string from trace events."""
    lines = ["sequenceDiagram", f"    participant U as User ({session_id})", "    participant P as Planner", "    participant E as Executor", "    participant T as Tools"]
    for ev in events:
        if ev["type"] == "tool_call" and ev["who"] == "planner":
            lines.append(f"    P->>T: {ev['tool']}({json.dumps(ev.get('args', {}))[:80]})")
        elif ev["type"] == "tool_result" and ev["who"] == "planner":
            lines.append(f"    T-->>P: {ev['tool']} result")
        elif ev["type"] == "tool_call" and ev["who"] == "executor":
            lines.append(f"    E->>T: {ev['tool']}({json.dumps(ev.get('args', {}))[:80]})")
        elif ev["type"] == "tool_result" and ev["who"] == "executor":
            lines.append(f"    T-->>E: {ev['tool']} result")
    return "\n".join(lines)

# -------------------------
# FastAPI
# -------------------------

class ChatIn(BaseModel):
    text: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ChatOut(BaseModel):
    reply: str
    events: List[Dict[str, Any]]
    mermaid: str

app = FastAPI(title="LangGraph Multi-Tool Agent")

@app.post("/agent/chat", response_model=ChatOut)
def chat(inp: ChatIn):
    # Build state and stream once per request; checkpoint per session_id
    state = {"messages": [{"role": "user", "content": inp.text}], "trace": []}
    _ = list(app_graph.stream(state, config={"configurable": {"thread_id": inp.session_id}}))
    # Extract final assistant reply
    messages: List[Dict[str, Any]] = app_graph.get_state({"configurable": {"thread_id": inp.session_id}}).values.get("messages", [])
    # last non-tool assistant message
    reply = next((m["content"] for m in reversed(messages) if m.get("role") == "assistant"), "(no reply)")
    # Pull trace from working memory (we also appended during nodes)
    # If not present (first run), create empty
    # LangGraph memory stores in checkpoint; our state already holds trace in nodes
    # So we reconstruct by scanning messages tagged as tool events in this simple demo
    # But we have 'trace' inside the compiled state if we capture it from nodes:
    # For simplicity, regenerate from last run (memory saver stores). We'll just store in a side channel:
    # In this demo, we return a lightweight events list extracted from the last tool results in messages is tricky,
    # so we return an empty list if not found.
    # Instead, attach trace to the last node run via ephemeral attribute in messages (already done in nodes).

    # Recompute: find last tool events captured
    # For demo simplicity, keep a small rolling trace attached to the last tool messages
    events: List[Dict[str, Any]] = []
    # We don't have direct persisted state here, but nodes appended into a local 'trace'.
    # For this HTTP scope, we return a minimal recent timeline by looking for JSON fragments in tool messages.
    # To keep it deterministic, we will build events anew: whenever the executor/planner called tools, they appended to state.trace
    # Since we don't have that local state here, quick workaround: embed in response within node functions.
    # We'll store the recent trace in LangGraph checkpoint under key 'trace'.
    # For now, return an empty events; clients can still show a textual reply. (Optional improvement: store trace in memory store.)

    # However, we can get the last step's snapshot via app_graph.get_state; it contains 'trace' because our State model includes it.
    snapshot = app_graph.get_state({"configurable": {"thread_id": inp.session_id}})
    events = snapshot.values.get("trace", []) if snapshot else []

    mermaid = trace_to_mermaid(events, inp.session_id)
    return ChatOut(reply=reply, events=events, mermaid=mermaid)

@app.get("/agent/tools")
def list_tools():
    return {"tools": TOOL_CATALOG}

@app.get("/healthz")
def health():
    return {"ok": True}
