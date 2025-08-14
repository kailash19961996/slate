"""
state_manager.py - LangGraph State Management and Workflow Control
================================================================

This module defines the state structure and workflow logic for the TRON wallet
agent. It manages the conversation flow, tracks progress through wallet operations,
and coordinates between the agent, tools, and frontend UI.

STATE ARCHITECTURE:
The agent state tracks multiple aspects of the conversation:
1. Message History: Complete conversation between user and agent
2. Wallet Information: Address, validation status, balance data
3. Operation Progress: Current step, UI state, error handling
4. User Context: Session info, preferences, pending inputs

WORKFLOW STATES:
- idle: Ready for new commands
- processing: Analyzing user request
- requesting_input: Waiting for user to provide information
- validating: Checking wallet address format
- connecting: Establishing blockchain connection
- fetching: Retrieving wallet data
- calculating: Computing portfolio values
- displaying: Showing results to user
- error: Handling errors and recovery

UI STATE SYNCHRONIZATION:
The state manager ensures the frontend always knows what the agent is doing
by sending real-time updates through WebSocket connections.
"""

from typing import Any, Dict, List, Optional, TypedDict, Literal
from datetime import datetime
import json

# ============================
# STATE TYPE DEFINITIONS
# ============================

class AgentState(TypedDict):
    """
    Complete state structure for the LangGraph TRON wallet agent.
    
    This state is passed between all nodes in the LangGraph workflow
    and maintains complete context throughout the conversation.
    """
    
    # ---- CONVERSATION TRACKING ----
    messages: List[Dict[str, Any]]  # Complete message history
    session_id: str                 # Unique session identifier
    
    # ---- WALLET INFORMATION ----
    wallet_address: Optional[str]   # Current wallet address being processed
    wallet_validated: bool          # Whether address has been validated
    wallet_info: Optional[Dict[str, Any]]  # Complete wallet data from blockchain
    
    # ---- OPERATION PROGRESS ----
    current_step: str              # Current workflow step
    ui_state: str                  # Current UI state for frontend
    needs_user_input: bool         # Whether waiting for user input
    pending_input_type: Optional[str]  # Type of input needed
    
    # ---- ERROR HANDLING ----
    error_message: Optional[str]   # Current error message
    retry_count: int              # Number of retries for current operation
    last_error_step: Optional[str] # Step where last error occurred
    
    # ---- CONTEXT AND METADATA ----
    user_intent: Optional[str]     # Detected user intention
    operation_start_time: Optional[str]  # When current operation started
    tools_used: List[str]         # Tools used in current operation
    
    # ---- FRONTEND COMMUNICATION ----
    ui_updates: List[Dict[str, Any]]  # Queue of UI updates to send
    function_calls: List[Dict[str, Any]]  # Function calls for frontend widgets


# ============================
# STATE INITIALIZATION
# ============================

def create_initial_state(session_id: str) -> AgentState:
    """
    Create a fresh agent state for a new conversation session.
    
    This function initializes all state variables with safe defaults
    and prepares the agent for its first user interaction.
    
    Args:
        session_id (str): Unique identifier for this conversation session
        
    Returns:
        AgentState: Fully initialized state ready for conversation
    """
    print(f"🎯 [STATE] Creating initial state for session: {session_id}")
    
    initial_state: AgentState = {
        # Conversation tracking
        "messages": [],
        "session_id": session_id,
        
        # Wallet information
        "wallet_address": None,
        "wallet_validated": False,
        "wallet_info": None,
        
        # Operation progress
        "current_step": "idle",
        "ui_state": "idle",
        "needs_user_input": False,
        "pending_input_type": None,
        
        # Error handling
        "error_message": None,
        "retry_count": 0,
        "last_error_step": None,
        
        # Context and metadata
        "user_intent": None,
        "operation_start_time": None,
        "tools_used": [],
        
        # Frontend communication
        "ui_updates": [],
        "function_calls": []
    }
    
    # Add initial UI state update
    initial_ui_update = {
        "type": "ui_state_change",
        "state": "idle",
        "message": "SLATE is ready to help with your TRON wallet",
        "timestamp": datetime.now().isoformat()
    }
    initial_state["ui_updates"].append(initial_ui_update)
    
    print(f"✅ [STATE] Initial state created successfully")
    return initial_state


# ============================
# STATE UPDATE FUNCTIONS
# ============================

def update_ui_state(state: AgentState, new_ui_state: str, message: str = "", data: Dict = None) -> AgentState:
    """
    Update the UI state and queue a frontend notification.
    
    This function changes the agent's UI state and prepares a message
    to be sent to the frontend via WebSocket.
    
    Args:
        state (AgentState): Current agent state
        new_ui_state (str): New UI state (idle, processing, thinking, etc.)
        message (str): Status message to display to user
        data (Dict): Additional data for the UI update
        
    Returns:
        AgentState: Updated state with new UI state and queued update
    """
    print(f"🎨 [STATE] UI state change: {state['ui_state']} -> {new_ui_state}")
    print(f"💬 [STATE] Status message: {message}")
    
    # Update the state
    state["ui_state"] = new_ui_state
    
    # Create UI update message
    ui_update = {
        "type": "ui_state_change",
        "state": new_ui_state,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    
    # Queue the update for frontend
    state["ui_updates"].append(ui_update)
    
    return state


def add_message(state: AgentState, role: str, content: str, metadata: Dict = None) -> AgentState:
    """
    Add a new message to the conversation history.
    
    Args:
        state (AgentState): Current agent state
        role (str): Message role ('user', 'assistant', 'system')
        content (str): Message content
        metadata (Dict): Additional message metadata
        
    Returns:
        AgentState: Updated state with new message
    """
    print(f"💬 [STATE] Adding {role} message: {content[:50]}...")
    
    message = {
        "id": f"{role}_{len(state['messages'])}_{datetime.now().timestamp()}",
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    
    state["messages"].append(message)
    return state


def update_wallet_info(state: AgentState, address: str = None, validated: bool = None, 
                      wallet_data: Dict = None) -> AgentState:
    """
    Update wallet-related information in the state.
    
    Args:
        state (AgentState): Current agent state
        address (str): Wallet address
        validated (bool): Whether address is validated
        wallet_data (Dict): Complete wallet information
        
    Returns:
        AgentState: Updated state with wallet information
    """
    if address is not None:
        print(f"🏦 [STATE] Setting wallet address: {address[:10]}...")
        state["wallet_address"] = address
    
    if validated is not None:
        print(f"✅ [STATE] Wallet validation status: {validated}")
        state["wallet_validated"] = validated
    
    if wallet_data is not None:
        print(f"💰 [STATE] Updating wallet data (portfolio: {wallet_data.get('total_usd_value', 'unknown')})")
        state["wallet_info"] = wallet_data
    
    return state


def set_error(state: AgentState, error_message: str, step: str = None) -> AgentState:
    """
    Record an error in the state and prepare error UI update.
    
    Args:
        state (AgentState): Current agent state
        error_message (str): Error description
        step (str): Step where error occurred
        
    Returns:
        AgentState: Updated state with error information
    """
    print(f"❌ [STATE] Error occurred: {error_message}")
    if step:
        print(f"📍 [STATE] Error at step: {step}")
    
    state["error_message"] = error_message
    state["retry_count"] += 1
    
    if step:
        state["last_error_step"] = step
    
    # Update UI to show error
    state = update_ui_state(state, "error", f"Error: {error_message}")
    
    return state


def clear_error(state: AgentState) -> AgentState:
    """
    Clear error state and reset error counters.
    
    Args:
        state (AgentState): Current agent state
        
    Returns:
        AgentState: State with cleared error information
    """
    print(f"🧹 [STATE] Clearing error state")
    
    state["error_message"] = None
    state["retry_count"] = 0
    state["last_error_step"] = None
    
    return state


def add_function_call(state: AgentState, function_type: str, data: Dict) -> AgentState:
    """
    Add a function call for the frontend to render as a widget.
    
    Args:
        state (AgentState): Current agent state
        function_type (str): Type of function call (wallet_connected, wallet_balance, etc.)
        data (Dict): Data for the widget
        
    Returns:
        AgentState: Updated state with new function call
    """
    print(f"🎨 [STATE] Adding function call: {function_type}")
    
    function_call = {
        "id": f"func_{len(state['function_calls'])}_{datetime.now().timestamp()}",
        "type": function_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    state["function_calls"].append(function_call)
    return state


def track_tool_usage(state: AgentState, tool_name: str) -> AgentState:
    """
    Track which tools have been used in the current operation.
    
    Args:
        state (AgentState): Current agent state
        tool_name (str): Name of the tool being used
        
    Returns:
        AgentState: Updated state with tool usage tracking
    """
    print(f"🔧 [STATE] Tool used: {tool_name}")
    
    if tool_name not in state["tools_used"]:
        state["tools_used"].append(tool_name)
    
    return state


# ============================
# STATE QUERY FUNCTIONS
# ============================

def has_wallet_address(state: AgentState) -> bool:
    """Check if a wallet address has been provided."""
    return state["wallet_address"] is not None and len(state["wallet_address"]) > 0


def is_wallet_validated(state: AgentState) -> bool:
    """Check if the current wallet address has been validated."""
    return state["wallet_validated"] and has_wallet_address(state)


def has_wallet_info(state: AgentState) -> bool:
    """Check if wallet information has been fetched."""
    return state["wallet_info"] is not None


def is_in_error_state(state: AgentState) -> bool:
    """Check if the agent is currently in an error state."""
    return state["error_message"] is not None


def needs_retry(state: AgentState, max_retries: int = 3) -> bool:
    """Check if an operation should be retried."""
    return is_in_error_state(state) and state["retry_count"] < max_retries


def get_conversation_context(state: AgentState, last_n: int = 5) -> List[Dict[str, Any]]:
    """Get the last N messages for context."""
    return state["messages"][-last_n:] if len(state["messages"]) > last_n else state["messages"]


# ============================
# WORKFLOW STEP MANAGEMENT
# ============================

def advance_step(state: AgentState, new_step: str) -> AgentState:
    """
    Advance to the next step in the workflow.
    
    Args:
        state (AgentState): Current agent state
        new_step (str): Next workflow step
        
    Returns:
        AgentState: Updated state with new current step
    """
    old_step = state["current_step"]
    print(f"➡️ [STATE] Workflow step: {old_step} -> {new_step}")
    
    state["current_step"] = new_step
    
    # If starting a new operation, record the start time
    if old_step == "idle" and new_step != "idle":
        state["operation_start_time"] = datetime.now().isoformat()
        print(f"⏰ [STATE] Operation started at: {state['operation_start_time']}")
    
    return state


def reset_to_idle(state: AgentState) -> AgentState:
    """
    Reset the agent to idle state, ready for new operations.
    
    Args:
        state (AgentState): Current agent state
        
    Returns:
        AgentState: State reset to idle configuration
    """
    print(f"🏁 [STATE] Resetting to idle state")
    
    # Clear operation-specific data
    state["current_step"] = "idle"
    state["needs_user_input"] = False
    state["pending_input_type"] = None
    state["operation_start_time"] = None
    state["tools_used"] = []
    
    # Clear any pending UI updates and function calls
    state["ui_updates"] = []
    state["function_calls"] = []
    
    # Clear errors
    state = clear_error(state)
    
    # Set UI back to idle
    state = update_ui_state(state, "idle", "Ready for your next request")
    
    return state


# ============================
# FRONTEND MESSAGE PREPARATION
# ============================

def prepare_frontend_updates(state: AgentState) -> List[Dict[str, Any]]:
    """
    Prepare all pending updates to send to the frontend.
    
    This function consolidates UI updates and function calls into
    a format ready for WebSocket transmission.
    
    Args:
        state (AgentState): Current agent state
        
    Returns:
        List of update messages for frontend
    """
    updates = []
    
    # Add UI state updates
    for ui_update in state["ui_updates"]:
        updates.append({
            "type": "ui_state_update",
            "data": ui_update
        })
    
    # Add function calls
    for func_call in state["function_calls"]:
        updates.append({
            "type": "function_call",
            "data": func_call
        })
    
    if updates:
        print(f"📤 [STATE] Prepared {len(updates)} frontend updates")
    
    return updates


def clear_pending_updates(state: AgentState) -> AgentState:
    """
    Clear all pending UI updates and function calls after sending.
    
    Args:
        state (AgentState): Current agent state
        
    Returns:
        AgentState: State with cleared pending updates
    """
    update_count = len(state["ui_updates"]) + len(state["function_calls"])
    
    if update_count > 0:
        print(f"🧹 [STATE] Clearing {update_count} sent updates")
    
    state["ui_updates"] = []
    state["function_calls"] = []
    
    return state


# ============================
# STATE DEBUGGING
# ============================

def print_state_summary(state: AgentState) -> None:
    """
    Print a summary of the current state for debugging.
    
    Args:
        state (AgentState): Current agent state
    """
    print(f"\n📊 [STATE SUMMARY] Session: {state['session_id']}")
    print(f"   Current Step: {state['current_step']}")
    print(f"   UI State: {state['ui_state']}")
    print(f"   Messages: {len(state['messages'])}")
    print(f"   Wallet Address: {state['wallet_address'][:10] + '...' if state['wallet_address'] else 'None'}")
    print(f"   Validated: {state['wallet_validated']}")
    print(f"   Has Wallet Info: {has_wallet_info(state)}")
    print(f"   Error: {state['error_message'] or 'None'}")
    print(f"   Pending Updates: {len(state['ui_updates']) + len(state['function_calls'])}")
    print(f"   Tools Used: {state['tools_used']}")
    print("─" * 50)

