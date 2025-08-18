"""
SLATE Backend Models
===================
Pydantic models for request/response validation and type safety.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    """User chat message input"""
    message: str
    session_id: str = Field(default="default")

class ChatResponse(BaseModel):
    """Chat API response with function calls and widget info"""
    reply: str
    function_calls: List[Dict[str, Any]] = Field(default_factory=list)
    widget: Dict[str, Any] = Field(default_factory=dict)  # Widget info decided by summarizer
    session_id: str
    timestamp: str

class WalletConnected(BaseModel):
    """Wallet connection event data"""
    session_id: str
    address: str
    network: str = "mainnet"
    node_host: str = "unknown"

class WalletError(BaseModel):
    """Wallet error event data"""
    session_id: str
    error: str

class WalletDetails(BaseModel):
    """Wallet details/balance data"""
    session_id: str
    address: str
    trx_balance: str
    extra: Dict[str, Any] = {}
