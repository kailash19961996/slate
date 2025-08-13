# Phase 4 — LangGraph: a tiny tool‑using agent loop (with memory)
# Phase 5 — Plug in your tools (wallet/DeFi)


from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_AI_MODEL = os.getenv("OPEN_AI_MODEL")


from typing import TypedDict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver  # swap to SqliteSaver for disk

# --- tools ---
@tool
def get_wallet_balance(address: str) -> dict:
    """Return balances for a TRON address. (Stub for now.)"""
    # TODO: call TronWeb/TronPy to fetch TRC-20 balances
    return {"address": address, "USDT": "123.45", "TRX": "678.90"}

@tool
def list_lending_markets() -> list:
    """Return currently supported markets with sample APRs. (Stub)"""
    return [
        {"symbol": "USDT", "supply_apr": 0.045, "borrow_apr": 0.075},
        {"symbol": "TRX",  "supply_apr": 0.032, "borrow_apr": 0.060},
    ]

@tool
def simulate_yield(symbol: str, amount: float, days: int) -> dict:
    """Very rough projection. Replace with protocol rates."""
    apr = 0.04 if symbol == "USDT" else 0.03
    est = amount * apr * (days/365)
    return {"symbol": symbol, "amount": amount, "days": days, "est_earnings": round(est, 2)}

@tool
def add(a: float, b: float) -> float:
    """Return a+b."""
    return a + b

tools = [add]

# bind tools to model (enables function calling)
llm = ChatOpenAI(
    model=OPEN_AI_MODEL,
    api_key=OPENAI_API_KEY,
).bind_tools(tools)

# --- state ---
class State(TypedDict):
    messages: List[BaseMessage]

# --- nodes ---
def agent_node(state: State):
    """Call the LLM; it may decide to call a tool."""
    resp = llm.invoke(state["messages"])
    return {"messages": state["messages"] + [resp]}

def tool_node(state: State):
    """Execute any tool calls emitted by the last AI message."""
    last = state["messages"][-1]
    tool_msgs: List[ToolMessage] = []
    if hasattr(last, "tool_calls") and last.tool_calls:
        for tc in last.tool_calls:
            name = tc["name"]
            args = tc["args"] or {}
            # dispatch by tool name
            result = next(t for t in tools if t.name == name).invoke(args)
            tool_msgs.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
    return {"messages": state["messages"] + tool_msgs}

def should_continue(state: State):
    """If the AI requested tools, go to tools; else end."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"

# --- graph wiring ---
graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
graph.add_edge("tools", "agent")

# memory/checkpointing (per thread_id)
memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# --- run a thread (acts like conversation memory) ---
cfg = {"configurable": {"thread_id": "kailash-demo"}}

result = app.invoke({"messages": [HumanMessage(content="Add 12.3 and 4.7 then say thanks.")]}, config=cfg)
for m in result["messages"]:
    if isinstance(m, AIMessage):
        print("AI:", m.content)

# continue same thread, memory preserved in the checkpoint:
result2 = app.invoke({"messages": [HumanMessage(content="Great. Now add 5 and 6.")]} , config=cfg)
for m in result2["messages"]:
    if isinstance(m, AIMessage):
        print("AI:", m.content)

# continue same thread, memory preserved in the checkpoint:
result3 = app.invoke({"messages": [HumanMessage(content="great lets get details for uyavcuadcviaudbciu wallet and list lending markets details")]} , config=cfg)
for m in result3["messages"]:
    if isinstance(m, AIMessage):
        print("AI:", m.content)
