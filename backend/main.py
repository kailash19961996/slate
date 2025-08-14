"""
main.py - Enhanced SLATE Backend with TronLink Integration
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from dotenv import load_dotenv
import os
from fastapi import Request
from langchain_core.tools import tool

load_dotenv()
app = FastAPI(title="SLATE Backend", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_AI_MODEL = os.getenv("OPEN_AI_MODEL", "gpt-4o-mini")
sessions = {}

print(f"🔑 [CONFIG] OpenAI API Key configured: {'Yes' if OPENAI_API_KEY else 'No'}")
print(f"🤖 [CONFIG] Model: {OPEN_AI_MODEL}")

@tool
def connect_tronlink_wallet(user_request: str) -> Dict[str, Any]:
    """Tool for TronLink wallet connection."""
    return {
        "type": "wallet_connection_request",
        "message": "Connect your TronLink wallet!",
        "frontend_action": "show_wallet_widget"
    }

@tool
def request_wallet_details(spec: str) -> Dict[str, Any]:
    """Ask the frontend to fetch wallet details (TRX, tokens, etc.)."""
    return {
        "type": "wallet_details_request",
        "message": "Fetch wallet details from the browser wallet.",
        "fields": ["trx_balance"]  # extend as needed (e.g., tokens)
    }
def create_agent():
    print("🤖 [AGENT] Creating agent...")
    if OPENAI_API_KEY:
        print("✅ [AGENT] OpenAI API key found, creating LangGraph agent")
        try:
            llm = ChatOpenAI(model=OPEN_AI_MODEL, temperature=0.2, api_key=OPENAI_API_KEY)
            tools = [connect_tronlink_wallet, request_wallet_details]
            print(f"🛠️ [AGENT] Loaded {len(tools)} tools")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are SLATE. If user asks to CONNECT a wallet → call connect_tronlink_wallet. \
                If user asks for WALLET DETAILS/BALANCE/ADDRESS → call request_wallet_details. \
                The frontend will execute these and report results."),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ])
            
            agent = create_tool_calling_agent(llm, tools, prompt)
            executor = AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=True)
            print("✅ [AGENT] Agent created successfully")
            return executor
        except Exception as e:
            print(f"❌ [AGENT] Error creating agent: {str(e)}")
            return None
        else:
            print("⚠️ [AGENT] No OpenAI API key, using mock responses")
            return None

agent_executor = create_agent()

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
    trx_balance: str  # e.g., "12.345678 TRX"
    extra: Dict[str, Any] = {}

@app.post("/api/wallet/details")
async def wallet_details(evt: WalletDetails):
    s = sessions.setdefault(evt.session_id, {"chat_history": []})
    s["wallet_details"] = evt.dict()
    s["chat_history"].append(("ai", f"📊 Wallet details updated for {evt.address}"))
    return {"ok": True}

@app.post("/api/wallet/connected")
async def wallet_connected(evt: WalletConnected):
    s = sessions.setdefault(evt.session_id, {"chat_history": []})
    s["wallet"] = {
        "address": evt.address,
        "network": evt.network,
        "node_host": evt.node_host,
        "connected_at": datetime.now().isoformat(),
    }
    # optional: let the bot acknowledge next turn
    s["chat_history"].append(("ai", f"✅ Wallet connected: {evt.address} on {evt.network}"))
    return {"ok": True}

@app.post("/api/wallet/error")
async def wallet_error(evt: WalletError):
    s = sessions.setdefault(evt.session_id, {"chat_history": []})
    s["last_wallet_error"] = {"error": evt.error, "ts": datetime.now().isoformat()}
    # optional: bot can mention failure next turn
    s["chat_history"].append(("ai", f"❌ Wallet connection failed: {evt.error}"))
    return {"ok": True}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    print(f"\n💬 [CHAT] New message received: '{message.message}'")
    print(f"👤 [CHAT] Session ID: {message.session_id}")
    start_time = time.time()
    
    try:
        if message.session_id not in sessions:
            sessions[message.session_id] = {"chat_history": []}
            print(f"🆕 [CHAT] New session created: {message.session_id}")
        
        session = sessions[message.session_id]
        print(f"📚 [CHAT] Chat history length: {len(session['chat_history'])}")
        
        if agent_executor:
            print("🚀 [CHAT] Using LangGraph agent")
            result = agent_executor.invoke({
                "input": message.message,
                "chat_history": session["chat_history"]
            })
            
            reply = result["output"]
            function_calls = []
            
            print(f"🤖 [CHAT] Agent reply: {reply}")
            print(f"🔧 [CHAT] Intermediate steps: {len(result.get('intermediate_steps', []))}")
            
            for action, observation in result.get("intermediate_steps", []):
                print(f"🛠️ [CHAT] Tool used: {action.tool}")
                if action.tool == "connect_tronlink_wallet":
                    function_calls.append({
                        "type": "wallet_connection_request",
                        "data": observation
                    })
                    print("💳 [CHAT] Wallet connection tool triggered")
                if action.tool == "request_wallet_details":
                    function_calls.append({
                    "type": "wallet_details_request",
                    "data": observation
                     })
                    print("📊 [CHAT] Wallet details tool triggered")
            
            session["chat_history"].extend([("human", message.message), ("ai", reply)])
        else:
            print("⚠️ [CHAT] Using mock response (no agent)")
            reply = "MOCK: Hello! I'm SLATE. How can I help you?"
            function_calls = []
        
        # Ensure 2-second minimum thinking time
        elapsed = time.time() - start_time
        if elapsed < 2.0:
            sleep_time = 2.0 - elapsed
            print(f"⏳ [CHAT] Adding {sleep_time:.2f}s delay for thinking animation")
            await asyncio.sleep(sleep_time)
        
        total_time = time.time() - start_time
        print(f"✅ [CHAT] Response ready (total time: {total_time:.2f}s, function_calls: {len(function_calls)})")
        
        return ChatResponse(
            reply=reply,
            function_calls=function_calls,
            session_id=message.session_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"❌ [CHAT] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        elapsed = time.time() - start_time
        if elapsed < 2.0:
            await asyncio.sleep(2.0 - elapsed)
        
        return ChatResponse(
            reply=f"Error: {str(e)}",
            function_calls=[],
            session_id=message.session_id,
            timestamp=datetime.now().isoformat()
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)