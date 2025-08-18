"""
SLATE Backend - LLM Planning and Memory
======================================
LLM-based tool planning with LangChain memory management.
"""

import json
from datetime import datetime
from typing import Any, Dict, List
from openai import OpenAI

# LangChain imports for memory management
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage

# Tool specification - 6 tools (3 wallet + 3 justlend)
TOOL_SPEC = {
    # Wallet tools (frontend execution)
    "wallet_check_tronlink": {"where": "frontend", "args": {}, "description": "Check if TronLink extension is installed and available"},
    "wallet_connect": {"where": "frontend", "args": {}, "description": "Connect to TronLink wallet"},
    "wallet_fetch_balance": {"where": "frontend", "args": {}, "description": "Fetch wallet balance and account details"},
    
    # JustLend tools (backend execution)
    "trustlender_list_markets": {"where": "backend", "args": {"limit": "int"}, "description": "List JustLend markets with APY data"},
    "trustlender_market_detail": {"where": "backend", "args": {"symbol": "string"}, "description": "Get detailed information for specific market"},
    "trustlender_user_position": {"where": "backend", "args": {"address": "string"}, "description": "Get user's lending positions and liquidity"},
}

# Global memory storage for LangChain memories
memory_store: Dict[str, ConversationBufferWindowMemory] = {}

def get_or_create_memory(session_id: str) -> ConversationBufferWindowMemory:
    """Get or create LangChain memory for session"""
    if session_id not in memory_store:
        print(f"💾 [MEMORY] Creating new LangChain memory for session {session_id}")
        memory_store[session_id] = ConversationBufferWindowMemory(
            k=10,  # Keep last 10 exchanges
            memory_key="chat_history",
            return_messages=True
        )
    return memory_store[session_id]

def decide_widget(tool_used: str, tool_result: Dict, session_id: str) -> Dict[str, Any]:
    """
    Decide which widget to show based on tool used and results.
    
    Args:
        tool_used: Name of the tool that was executed
        tool_result: Result data from tool execution
        session_id: Session identifier for context
        
    Returns:
        Dict with widget type and data to display
    """
    print(f"🎨 [WIDGET] Deciding widget for tool: {tool_used}")
    
    # Default to idle widget
    widget_info = {"type": "idle", "data": None}
    
    if not tool_result or not isinstance(tool_result, dict):
        print("🎨 [WIDGET] No valid tool result, showing idle widget")
        return widget_info
    
    # Wallet tools -> show wallet widget with data
    if tool_used in ["wallet_connect", "wallet_fetch_balance"] and tool_result.get("ok"):
        widget_info = {
            "type": "wallet",
            "data": tool_result
        }
        print(f"🎨 [WIDGET] Showing wallet widget with address: {tool_result.get('address', 'unknown')}")
        
    elif tool_used == "wallet_check_tronlink":
        # Only show wallet widget if successful
        if tool_result.get("tronLinkPresent") and tool_result.get("tronWebInjected"):
            widget_info = {"type": "wallet", "data": tool_result}
            print("🎨 [WIDGET] Showing wallet widget - TronLink detected")
        else:
            print("🎨 [WIDGET] TronLink not available, showing idle widget")
    
    # JustLend tools -> show justlend widget with data
    elif tool_used == "trustlender_list_markets":
        if tool_result.get("success") and tool_result.get("markets"):
            widget_info = {
                "type": "justlend",
                "data": {"view": "list", "payload": tool_result}
            }
            print(f"🎨 [WIDGET] Showing JustLend markets widget with {len(tool_result.get('markets', []))} markets")
        else:
            print(f"🎨 [WIDGET] JustLend markets failed: {tool_result.get('error', 'unknown error')}")
            
    elif tool_used == "trustlender_market_detail":
        if tool_result.get("success") and tool_result.get("market"):
            widget_info = {
                "type": "justlend", 
                "data": {"view": "detail", "payload": tool_result}
            }
            symbol = tool_result.get("market", {}).get("symbol", "unknown")
            print(f"🎨 [WIDGET] Showing JustLend market detail widget for {symbol}")
        else:
            print(f"🎨 [WIDGET] JustLend market detail failed: {tool_result.get('error', 'unknown error')}")
            
    elif tool_used == "trustlender_user_position":
        if tool_result.get("success"):
            widget_info = {
                "type": "justlend",
                "data": {"view": "user", "payload": tool_result}
            }
            print(f"🎨 [WIDGET] Showing JustLend user position widget")
        else:
            print(f"🎨 [WIDGET] JustLend user position failed: {tool_result.get('error', 'unknown error')}")
    
    else:
        print(f"🎨 [WIDGET] No specific widget for tool: {tool_used}, showing idle")
    
    return widget_info

def update_conversation_memory(session_id: str, user_message: str, ai_response: str = "", tool_used: str = "", tool_result: Dict = None):
    """Update LangChain conversation memory with enhanced context"""
    memory = get_or_create_memory(session_id)
    
    # Add user message
    memory.chat_memory.add_user_message(user_message)
    
    # Add AI response if provided
    if ai_response:
        # Include tool info and contextual data in AI response for future reference
        full_response = ai_response
        if tool_used:
            full_response += f" [Used tool: {tool_used}]"
            
            # Add contextual data summary for future questions
            if tool_result and isinstance(tool_result, dict):
                if tool_used == "wallet_fetch_balance" and tool_result.get("ok"):
                    snapshot = tool_result.get("snapshot", {})
                    if snapshot.get("core", {}).get("trx"):
                        full_response += f" [Context: User has {snapshot['core']['trx']:.2f} TRX balance"
                        if snapshot.get("address"):
                            full_response += f" on address {snapshot['address'][:8]}..."
                        if snapshot.get("network"):
                            full_response += f" on {snapshot['network']} network"
                        full_response += "]"
                        
                elif tool_used == "wallet_connect" and tool_result.get("ok"):
                    if tool_result.get("address"):
                        full_response += f" [Context: Connected to wallet {tool_result['address'][:8]}..."
                        if tool_result.get("network"):
                            full_response += f" on {tool_result['network']} network"
                        full_response += "]"
                        
                elif tool_used == "trustlender_list_markets" and tool_result.get("success"):
                    markets = tool_result.get("markets", [])
                    if markets:
                        market_info = []
                        for m in markets[:3]:  # Store top 3 for context
                            symbol = m.get("symbol", "")
                            supply_apy = m.get("supply_apy_pct_approx", 0)
                            borrow_apy = m.get("borrow_apy_pct_approx", 0)
                            market_info.append(f"{symbol}(Supply:{supply_apy}%/Borrow:{borrow_apy}%)")
                        full_response += f" [Context: Available markets: {', '.join(market_info)}]"
                        
                elif tool_used == "trustlender_market_detail" and tool_result.get("success"):
                    market = tool_result.get("market", {})
                    if market:
                        symbol = market.get("symbol", "")
                        supply_apy = market.get("supply_apy_pct_approx", 0)
                        borrow_apy = market.get("borrow_apy_pct_approx", 0)
                        collateral = market.get("collateral_factor_pct", 0)
                        full_response += f" [Context: {symbol} market - Supply APY: {supply_apy}%, Borrow APY: {borrow_apy}%, Collateral: {collateral}%]"
                        
                elif tool_used == "trustlender_user_position" and tool_result.get("success"):
                    positions = tool_result.get("positions", [])
                    active_positions = [p for p in positions if p.get("token_balance_mantissa", 0) > 0 or p.get("borrow_balance_mantissa", 0) > 0]
                    if active_positions:
                        pos_info = [f"{p.get('symbol', '')}" for p in active_positions[:3]]
                        full_response += f" [Context: User has positions in: {', '.join(pos_info)}]"
                        
        memory.chat_memory.add_ai_message(full_response)
    
    print(f"💾 [MEMORY] Updated LangChain memory with enhanced context for session {session_id}")

def plan_with_llm(client_llm: OpenAI, session_id: str, user_text: str, model: str) -> List[Dict[str, Any]]:
    """
    Use LLM to dynamically plan function calls based on user intent.
    
    Args:
        client_llm: OpenAI client instance
        session_id: User session identifier
        user_text: User's message to analyze
        model: OpenAI model to use
        
    Returns:
        List of function call dictionaries with type and args
    """
    print(f"📋 [PLANNING] Starting plan generation for session: {session_id}")
    print(f"📋 [PLANNING] User message: {user_text}")
    
    # Get LangChain memory for context  
    memory = get_or_create_memory(session_id)
    memory_context = memory.load_memory_variables({})
    chat_history = memory_context.get('chat_history', [])
    print(f"📋 [PLANNING] Memory context: {len(chat_history)} previous messages")
    
    # Extract relevant context from memory for better planning
    recent_context = ""
    if chat_history:
        recent_messages = chat_history[-4:]  # Last 4 messages for better context
        recent_context = "\nRecent conversation context:\n"
        for msg in recent_messages:
            if hasattr(msg, 'content'):
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                content = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
                recent_context += f"{role}: {content}\n"
        print(f"📋 [PLANNING] Using recent context from {len(recent_messages)} messages")

    system = (
        "You are a tool planner for a wallet + DeFi assistant.\n"
        "Return ONLY valid JSON (no prose). Your output must be a JSON array\n"
        "of function call objects. Each item must be of the form:\n"
        '{"type": "<one of: ' + ", ".join(TOOL_SPEC.keys()) + '>", "args": {...optional...}}\n'
        "Available tools:\n"
        "\nWallet tools (frontend):\n"
        "- wallet_check_tronlink: Check if TronLink extension is installed\n"
        "- wallet_connect: Connect to TronLink wallet\n"
        "- wallet_fetch_balance: Fetch wallet balance and account details\n"
        "\nJustLend tools (backend):\n"
        "- trustlender_list_markets: List JustLend markets (requires limit arg)\n"
        "- trustlender_market_detail: Get market details (requires symbol arg)\n"
        "- trustlender_user_position: Get user positions (requires address arg)\n"
        "\nUse conversation memory from session_profile to avoid redundant operations."
    )
    
    print(f"📋 [PLANNING] Available tools: {list(TOOL_SPEC.keys())}")

    user_payload = {
        "user_message": user_text,
        "conversation_history": recent_context,  # Use improved context
        "examples": [
            {"ask": "Do I have TronLink installed?", "function_calls": [{"type": "wallet_check_tronlink"}]},
            {"ask": "Connect my wallet", "function_calls": [{"type": "wallet_check_tronlink"}, {"type": "wallet_connect"}]},
            {"ask": "What's my TRX balance?", "function_calls": [{"type": "wallet_check_tronlink"}, {"type": "wallet_connect"}, {"type": "wallet_fetch_balance"}]},
            {"ask": "List JustLend markets", "function_calls": [{"type": "trustlender_list_markets", "args": {"limit": 6}}]},
            {"ask": "Show details for JUSDT market", "function_calls": [{"type": "trustlender_market_detail", "args": {"symbol": "JUSDT"}}]},
            {"ask": "What's my position?", "function_calls": [{"type": "trustlender_user_position", "args": {"address": "TxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxX"}}]},
        ],
    }

    try:
        print("🧠 [LLM] Sending planning request to OpenAI...")
        
        resp = client_llm.chat.completions.create(
            model=model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
        )
        
        content = (resp.choices[0].message.content or "").strip()
        print(f"🧠 [LLM] Raw response: {content}")
        
        # Strip ```json fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            if lines and lines[0].startswith("```"):
                content = "\n".join(lines[1:])
            if content.endswith("```"):
                content = content[: -3]
        
        print(f"🧠 [LLM] Cleaned response: {content}")

        # Accept either a JSON array or {"function_calls":[...]}
        parsed = json.loads(content)
        print(f"📋 [PLANNING] Parsed JSON: {parsed}")
        
        if isinstance(parsed, dict) and "function_calls" in parsed:
            parsed = parsed["function_calls"]
        if not isinstance(parsed, list):
            print("⚠️ [PLANNING] Response not a list, returning empty plan")
            return []

        # Sanitize / validate
        calls: List[Dict[str, Any]] = []
        for i, item in enumerate(parsed):
            print(f"📋 [PLANNING] Validating item {i}: {item}")
            
            if not isinstance(item, dict):
                print(f"⚠️ [PLANNING] Item {i} not a dict, skipping")
                continue
                
            t = item.get("type")
            if t not in TOOL_SPEC:
                print(f"⚠️ [PLANNING] Unknown tool type '{t}', skipping")
                continue
                
            args = item.get("args") or {}
            calls.append({"type": t, "args": args})
            print(f"✅ [PLANNING] Added call: {t} with args: {args}")
        
        print(f"📋 [PLANNING] Final plan: {calls}")
        return calls
        
    except Exception as e:
        print(f"❌ [PLANNING] LLM planning failed: {type(e).__name__}: {e}")
        return []

def summarize_with_llm(client_llm: OpenAI, question: str, tool: str, tool_result: Dict[str, Any], session_id: str, model: str) -> str:
    """
    Generate the final user-facing response using LLM.
    
    This is the ONLY place where user-facing text is created.
    No templates or canned responses - purely AI-generated.
    
    Args:
        client_llm: OpenAI client instance
        question: Original user question
        tool: Tool that was executed
        tool_result: Result data from tool execution
        session_id: Session identifier for memory context
        model: OpenAI model to use
        
    Returns:
        str: Natural language response for the user
    """
    print(f"\n📄 [SUMMARIZE] Starting response generation")
    print(f"📄 [SUMMARIZE] Question: {question}")
    print(f"📄 [SUMMARIZE] Tool: {tool}")
    print(f"📄 [SUMMARIZE] Result keys: {list(tool_result.keys()) if isinstance(tool_result, dict) else 'Not a dict'}")
    
    # Get LangChain memory for context
    memory_context = ""
    if session_id:
        memory = get_or_create_memory(session_id)
        memory_vars = memory.load_memory_variables({})
        chat_history = memory_vars.get('chat_history', [])
        
        if chat_history:
            recent_messages = chat_history[-4:]  # Last 4 messages for context
            memory_context = "\nRecent conversation context:\n"
            for msg in recent_messages:
                if hasattr(msg, 'content'):
                    role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                    content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    memory_context += f"{role}: {content}\n"
    
    # Meta-guidance for LLM (not canned responses)
    system = (
        "You are a concise, accurate assistant for a blockchain wallet & DeFi app. "
        "Write directly to the user in a conversational tone. "
        "If tool='no_tool', respond naturally to the user's message without needing tool results. "
        "If tool results are provided, ground your answer in them. "
        "Use conversation memory to provide context-aware responses. "
        "If 'tool_result' contains an error, explain clearly and suggest next steps. "
        "Be helpful but concise. Return plain text only."
    )

    user_content = (
        "question:\n"
        f"{question}\n\n"
        "tool:\n"
        f"{tool}\n\n"
        "tool_result (JSON):\n"
        f"{tool_result}\n\n"
        f"{memory_context}"
    )
    
    print("🧠 [SUMMARIZE] Sending request to OpenAI...")

    try:
        # Generate response using Chat Completions
        resp = client_llm.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
        
        response_text = (resp.choices[0].message.content or "").strip()
        print(f"📄 [SUMMARIZE] Generated response: {response_text}")
        
        return response_text
        
    except Exception as e:
        print(f"❌ [SUMMARIZE] Error generating response: {e}")
        return "I encountered an error processing your request. Please try again."
