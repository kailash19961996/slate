"""
SLATE Backend - LangGraph Agent Orchestrator
Main orchestrator that handles all agent interactions and sends responses to frontend
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from dotenv import load_dotenv
import os

# Import our modules
from util import safe_json_parse, format_tron_address, validate_address
from prompt import SYSTEM_PROMPTS, get_wallet_prompt
from tools import get_all_tools, WalletConnectionTool

# Load environment variables
load_dotenv()

app = FastAPI(
    title="SLATE Backend API",
    description="AI-powered blockchain agent with LangGraph orchestration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# LangGraph State & Models
# -------------------------

class AgentState(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    user_context: Dict[str, Any] = Field(default_factory=dict)  # Store wallet info, etc.
    pending_requests: List[Dict[str, Any]] = Field(default_factory=list)  # Store incomplete requests
    session_id: str = ""

class ChatMessage(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ChatResponse(BaseModel):
    reply: str
    function_calls: List[Dict[str, Any]] = Field(default_factory=list)
    needs_user_input: bool = False
    user_input_prompt: Optional[str] = None
    trace: List[Dict[str, Any]] = Field(default_factory=list)

# -------------------------
# WebSocket Manager
# -------------------------

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(message)
            except:
                self.disconnect(session_id)

    async def send_function_call(self, session_id: str, function_data: Dict[str, Any]):
        """Send function call to frontend for rendering"""
        message = {
            "type": "function_call",
            "data": {
                "id": f"{datetime.now().timestamp()}",
                **function_data
            }
        }
        await self.send_personal_message(json.dumps(message), session_id)

manager = ConnectionManager()

# -------------------------
# LangGraph Agent Setup
# -------------------------

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

llm = ChatOpenAI(model=MODEL_NAME, temperature=0, api_key=OPENAI_API_KEY)

# Get all available tools
ALL_TOOLS = get_all_tools()
tool_bound_llm = llm.bind_tools(ALL_TOOLS)

def agent_node(state: AgentState) -> AgentState:
    """Main agent node that processes user messages and decides on actions"""
    
    # Build system prompt with context
    system_content = SYSTEM_PROMPTS["main_agent"]
    if state.user_context.get("wallet_address"):
        system_content += f"\n\nUser's wallet address: {state.user_context['wallet_address']}"
        system_content += "\nYou have access to wallet information and can help with balance checks and transactions."
    
    # Add information about pending requests
    if state.pending_requests:
        system_content += f"\n\nPending requests requiring user input: {json.dumps(state.pending_requests)}"
    
    # Build message history
    messages = [SystemMessage(content=system_content)]
    
    # Add conversation history
    for msg in state.messages:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg.get("role") == "assistant":
            messages.append(SystemMessage(content=msg["content"]))
    
    # Get LLM response
    response = tool_bound_llm.invoke(messages)
    
    # Add assistant response to messages
    state.messages.append({
        "role": "assistant", 
        "content": response.content,
        "timestamp": datetime.now().isoformat()
    })
    
    # Process tool calls if any
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})
            
            # Log tool call in trace
            state.trace.append({
                "type": "tool_call",
                "tool": tool_name,
                "args": tool_args,
                "timestamp": datetime.now().isoformat()
            })
            
            # Execute tool
            try:
                tool_obj = next(t for t in ALL_TOOLS if t.name == tool_name)
                
                # Special handling for wallet connection tool
                if tool_name == "request_wallet_connection":
                    # Check if we already have wallet address
                    if state.user_context.get("wallet_address"):
                        result = f"Wallet already connected: {state.user_context['wallet_address']}"
                    else:
                        # Request wallet address from user
                        state.pending_requests.append({
                            "type": "wallet_address",
                            "prompt": "Please provide your wallet address to connect:",
                            "tool_call_id": tool_call.get("id", str(uuid.uuid4()))
                        })
                        result = "Requesting wallet address from user..."
                
                else:
                    # Execute other tools normally
                    result = tool_obj.invoke(tool_args)
                
                # Log tool result
                state.trace.append({
                    "type": "tool_result",
                    "tool": tool_name,
                    "result": str(result)[:500],  # Truncate long results
                    "timestamp": datetime.now().isoformat()
                })
                
                # Add tool result to messages
                state.messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": str(result)
                })
                
            except Exception as e:
                error_msg = f"Error executing tool {tool_name}: {str(e)}"
                state.trace.append({
                    "type": "tool_error",
                    "tool": tool_name,
                    "error": error_msg
                })
                state.messages.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": error_msg
                })
    
    return state

def should_continue(state: AgentState) -> str:
    """Determine if we should continue processing or end"""
    return END

# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)

# Add memory for conversation persistence
memory = MemorySaver()
agent_graph = workflow.compile(checkpointer=memory)

# -------------------------
# API Endpoints
# -------------------------

@app.get("/")
async def root():
    return {"message": "SLATE Backend API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    """Process a chat message through the LangGraph agent"""
    try:
        # Create initial state
        initial_state = {
            "messages": [{"role": "user", "content": message.message}],
            "trace": [],
            "user_context": {},
            "pending_requests": [],
            "session_id": message.session_id
        }
        
        # Run the agent
        config = {"configurable": {"thread_id": message.session_id}}
        result = agent_graph.invoke(initial_state, config=config)
        
        # Extract response
        assistant_messages = [msg for msg in result["messages"] if msg.get("role") == "assistant"]
        reply = assistant_messages[-1]["content"] if assistant_messages else "I'm here to help!"
        
        # Check for pending requests
        needs_input = len(result["pending_requests"]) > 0
        input_prompt = result["pending_requests"][0]["prompt"] if needs_input else None
        
        # Generate function calls based on the conversation
        function_calls = await generate_function_calls(message.message, result)
        
        return ChatResponse(
            reply=reply,
            function_calls=function_calls,
            needs_user_input=needs_input,
            user_input_prompt=input_prompt,
            trace=result["trace"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.post("/api/wallet/connect")
async def connect_wallet(data: dict):
    """Handle wallet connection with address"""
    session_id = data.get("session_id")
    wallet_address = data.get("wallet_address")
    
    if not session_id or not wallet_address:
        raise HTTPException(status_code=400, detail="Missing session_id or wallet_address")
    
    # Validate address format
    if not validate_address(wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address format")
    
    # Update agent state with wallet info
    config = {"configurable": {"thread_id": session_id}}
    current_state = agent_graph.get_state(config)
    
    if current_state:
        # Update user context
        current_state.values["user_context"]["wallet_address"] = wallet_address
        current_state.values["user_context"]["connected_at"] = datetime.now().isoformat()
        
        # Clear pending wallet requests
        current_state.values["pending_requests"] = [
            req for req in current_state.values["pending_requests"] 
            if req.get("type") != "wallet_address"
        ]
        
        # Trigger wallet info function call
        await manager.send_function_call(session_id, {
            "type": "wallet_connected",
            "data": {
                "address": wallet_address,
                "formatted_address": format_tron_address(wallet_address),
                "status": "connected"
            }
        })
        
        # TODO: Add actual wallet balance fetch here
        await manager.send_function_call(session_id, {
            "type": "wallet_balance",
            "data": {
                "address": wallet_address,
                "balance": "1,234.56 TRX",  # Mock data for now
                "usd_value": "$85.42",
                "tokens": [
                    {"symbol": "USDT", "balance": "500.00", "value": "$500.00"},
                    {"symbol": "JST", "balance": "1000.00", "value": "$25.30"}
                ]
            }
        })
    
    return {"status": "success", "address": wallet_address}

async def generate_function_calls(user_message: str, agent_result: Dict) -> List[Dict[str, Any]]:
    """Generate function calls based on the conversation and agent result"""
    function_calls = []
    message_lower = user_message.lower()
    
    # Check if wallet connection was requested and completed
    if "wallet" in message_lower and "connect" in message_lower:
        if agent_result["user_context"].get("wallet_address"):
            function_calls.append({
                "type": "wallet_info",
                "data": {
                    "address": agent_result["user_context"]["wallet_address"],
                    "status": "connected"
                }
            })
    
    return function_calls

# -------------------------
# WebSocket Endpoint
# -------------------------

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data.get("type") == "chat":
                # Process chat message
                chat_message = ChatMessage(
                    message=message_data["message"],
                    session_id=session_id
                )
                
                # Get response from agent
                response = await chat_endpoint(chat_message)
                
                # Send AI response
                await manager.send_personal_message(json.dumps({
                    "type": "ai_response",
                    "data": {
                        "message": response.reply,
                        "timestamp": datetime.now().isoformat(),
                        "needs_user_input": response.needs_user_input,
                        "user_input_prompt": response.user_input_prompt
                    }
                }), session_id)
                
                # Send function calls with delay
                for i, func_call in enumerate(response.function_calls):
                    await asyncio.sleep(0.5 + i * 0.3)
                    await manager.send_function_call(session_id, func_call)
            
            elif message_data.get("type") == "wallet_address":
                # Handle wallet address input
                await connect_wallet({
                    "session_id": session_id,
                    "wallet_address": message_data["wallet_address"]
                })
                
                # Send confirmation
                await manager.send_personal_message(json.dumps({
                    "type": "ai_response",
                    "data": {
                        "message": f"Great! I've connected to your wallet. Let me fetch your balance and information.",
                        "timestamp": datetime.now().isoformat()
                    }
                }), session_id)
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"WebSocket error for {session_id}: {e}")
        manager.disconnect(session_id)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )