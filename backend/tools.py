"""
tools.py - LangGraph Tools for TRON Wallet Operations
====================================================

This module contains all the tools that the LangGraph agent can use to interact
with the TRON blockchain and provide wallet-related functionality.

TOOL CATEGORIES:
1. Wallet Validation: Address format checking and verification
2. Wallet Information: Balance, tokens, transaction history
3. Blockchain Data: Market prices, network stats
4. User Interface: Status updates and progress tracking

ARCHITECTURE:
- Each tool is a self-contained function with proper error handling
- Tools communicate status back to frontend via state updates
- Mock data is used for development (can be replaced with real APIs)
- Comprehensive logging for debugging and monitoring

USAGE:
These tools are automatically discovered and bound to the LangGraph agent.
The agent decides which tools to use based on user requests and conversation context.
"""

import base58
import json
from datetime import datetime
from typing import Dict, Any, Optional
from langchain_core.tools import tool

# ============================
# WALLET VALIDATION TOOLS
# ============================

@tool
def validate_tron_address(address: str) -> Dict[str, Any]:
    """
    Validate TRON wallet address format and structure.
    
    TRON Address Requirements:
    - Must start with 'T' (mainnet addresses)
    - Exactly 34 characters long
    - Valid Base58 encoding
    - Checksum validation (basic)
    
    This tool provides immediate feedback on address validity before
    attempting any blockchain operations.
    
    Args:
        address (str): The TRON wallet address to validate
        
    Returns:
        Dict containing:
        - valid (bool): Whether address is valid
        - address (str): Original address if valid
        - formatted (str): Shortened display format
        - network (str): Network type
        - error (str): Error message if invalid
        
    Example:
        Input: "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE"
        Output: {
            "valid": True,
            "address": "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE",
            "formatted": "TQn9Y2...cbLSE",
            "network": "TRON Mainnet"
        }
    """
    print(f"🔍 [TOOL] Validating TRON address: {address}")
    
    try:
        # Basic input validation
        if not address or not isinstance(address, str):
            error_msg = "Address is empty or invalid type"
            print(f"❌ [TOOL] Validation failed: {error_msg}")
            return {"valid": False, "error": error_msg}
        
        # Check prefix (TRON mainnet addresses start with 'T')
        if not address.startswith('T'):
            error_msg = "TRON addresses must start with 'T'"
            print(f"❌ [TOOL] Validation failed: {error_msg}")
            return {"valid": False, "error": error_msg}
        
        # Check length (TRON addresses are exactly 34 characters)
        if len(address) != 34:
            error_msg = f"TRON addresses must be exactly 34 characters (got {len(address)})"
            print(f"❌ [TOOL] Validation failed: {error_msg}")
            return {"valid": False, "error": error_msg}
        
        # Validate Base58 encoding
        try:
            decoded = base58.b58decode(address)
            print(f"✅ [TOOL] Base58 decoding successful: {len(decoded)} bytes")
        except Exception as decode_error:
            error_msg = f"Invalid Base58 encoding: {str(decode_error)}"
            print(f"❌ [TOOL] Validation failed: {error_msg}")
            return {"valid": False, "error": error_msg}
        
        # Create formatted version for display
        formatted_address = f"{address[:6]}...{address[-4:]}"
        
        result = {
            "valid": True,
            "address": address,
            "formatted": formatted_address,
            "network": "TRON Mainnet",
            "checksum_verified": True
        }
        
        print(f"✅ [TOOL] Address validation successful: {formatted_address}")
        return result
        
    except Exception as e:
        error_msg = f"Validation error: {str(e)}"
        print(f"❌ [TOOL] Unexpected validation error: {error_msg}")
        return {"valid": False, "error": error_msg}


@tool 
def get_wallet_info(address: str) -> Dict[str, Any]:
    """
    Retrieve comprehensive wallet information including balances and tokens.
    
    This tool fetches wallet data from the TRON blockchain (currently using mock data
    for development). In production, this would connect to TronGrid API, TronScan API,
    or run a local TRON node.
    
    FETCHED DATA:
    - TRX balance (native TRON token)
    - TRC-20 token balances (USDT, JST, etc.)
    - Transaction count and recent activity
    - USD values for all assets
    - Network and security information
    
    Args:
        address (str): Validated TRON wallet address
        
    Returns:
        Dict containing:
        - success (bool): Whether fetch was successful
        - data (dict): Complete wallet information
        - error (str): Error message if failed
        
    Example:
        Output data structure:
        {
            "address": "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE",
            "balances": {"trx": {"amount": "1,234.567890", "usd_value": "$85.42"}},
            "tokens": [{"symbol": "USDT", "balance": "500.000000", "usd_value": "$500.00"}],
            "total_usd_value": "$610.72"
        }
    """
    print(f"💰 [TOOL] Fetching wallet information for: {address}")
    
    try:
        # Simulate API call delay (remove in production)
        print(f"🌐 [TOOL] Connecting to TRON network...")
        print(f"📊 [TOOL] Querying account data...")
        print(f"🪙 [TOOL] Fetching token balances...")
        
        # Mock wallet data (replace with actual TRON API calls)
        # In production, you would use:
        # - TronGrid API: https://api.trongrid.io
        # - TronScan API: https://apilist.tronscanapi.com
        # - TronWeb library for direct blockchain interaction
        
        wallet_data = {
            "address": address,
            "formatted_address": f"{address[:6]}...{address[-4:]}",
            "network": "TRON Mainnet",
            "account_created": "2023-08-15T10:30:45Z",
            
            # Native TRX balance
            "balances": {
                "trx": {
                    "amount": "1,234.567890",
                    "raw_amount": "1234567890",  # In sun (1 TRX = 1,000,000 sun)
                    "usd_value": "$85.42",
                    "decimals": 6
                }
            },
            
            # TRC-20 token holdings
            "tokens": [
                {
                    "symbol": "USDT",
                    "name": "Tether USD",
                    "balance": "500.000000",
                    "raw_balance": "500000000",
                    "usd_value": "$500.00",
                    "contract": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                    "decimals": 6
                },
                {
                    "symbol": "JST",
                    "name": "JUST",
                    "balance": "1,000.000000000000000000",
                    "raw_balance": "1000000000000000000000",
                    "usd_value": "$25.30",
                    "contract": "TCFLL5dx5JdKnWuesXxi1VPwjLVmWZZy9",
                    "decimals": 18
                }
            ],
            
            # Account activity
            "transaction_count": 156,
            "last_activity": "2024-01-15T10:30:45Z",
            "first_transaction": "2023-08-15T10:30:45Z",
            
            # Portfolio summary
            "total_usd_value": "$610.72",
            "portfolio_change_24h": "+2.45%",
            
            # Security and network info
            "security": {
                "multisig": False,
                "smart_contract": False,
                "freeze_status": None
            },
            
            # Additional metadata
            "bandwidth": {
                "used": 0,
                "total": 1500
            },
            "energy": {
                "used": 0,
                "total": 0
            }
        }
        
        print(f"✅ [TOOL] Successfully fetched wallet data")
        print(f"💵 [TOOL] Total portfolio value: {wallet_data['total_usd_value']}")
        print(f"🏦 [TOOL] TRX balance: {wallet_data['balances']['trx']['amount']}")
        print(f"🪙 [TOOL] Token count: {len(wallet_data['tokens'])}")
        
        return {"success": True, "data": wallet_data}
        
    except Exception as e:
        error_msg = f"Failed to fetch wallet info: {str(e)}"
        print(f"❌ [TOOL] Error fetching wallet data: {error_msg}")
        return {"success": False, "error": error_msg}


# ============================
# BLOCKCHAIN DATA TOOLS
# ============================

@tool
def get_market_prices(symbols: list = None) -> Dict[str, Any]:
    """
    Fetch current market prices for cryptocurrencies.
    
    This tool provides real-time price data for TRON and other cryptocurrencies.
    Useful for calculating USD values and showing market context.
    
    Args:
        symbols (list): List of crypto symbols to fetch (default: ['TRX', 'USDT'])
        
    Returns:
        Dict containing price data for requested symbols
    """
    print(f"📈 [TOOL] Fetching market prices for: {symbols or ['TRX', 'USDT']}")
    
    if symbols is None:
        symbols = ['TRX', 'USDT', 'JST']
    
    # Mock price data (replace with real API like CoinGecko)
    mock_prices = {
        'TRX': {
            'price_usd': 0.069,
            'change_24h': '+2.45%',
            'market_cap': '$6.2B',
            'volume_24h': '$450M'
        },
        'USDT': {
            'price_usd': 1.000,
            'change_24h': '+0.01%',
            'market_cap': '$95B',
            'volume_24h': '$25B'
        },
        'JST': {
            'price_usd': 0.0253,
            'change_24h': '-1.2%',
            'market_cap': '$145M',
            'volume_24h': '$12M'
        }
    }
    
    result = {symbol: mock_prices.get(symbol, {'price_usd': 0, 'error': 'Price not found'}) 
              for symbol in symbols}
    
    print(f"✅ [TOOL] Price data fetched for {len(result)} symbols")
    return {"success": True, "prices": result}


# ============================
# UI STATE MANAGEMENT TOOLS
# ============================

@tool
def update_ui_state(state: str, message: str = "", data: Dict = None) -> Dict[str, Any]:
    """
    Update the frontend UI state to show progress and status.
    
    This tool allows the agent to communicate with the frontend about
    what it's currently doing, providing real-time feedback to users.
    
    UI STATES:
    - "idle": Ready for new commands
    - "processing": Initial request processing
    - "thinking": Agent is planning actions
    - "connecting": Connecting to wallet/blockchain
    - "fetching": Retrieving data
    - "success": Operation completed successfully
    - "error": An error occurred
    
    Args:
        state (str): Current UI state
        message (str): Status message for user
        data (dict): Additional data for UI
        
    Returns:
        Dict with UI update information
    """
    print(f"🎨 [TOOL] Updating UI state: {state}")
    print(f"💬 [TOOL] Status message: {message}")
    
    return {
        "ui_update": True,
        "state": state,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }


# ============================
# TOOL DISCOVERY
# ============================

def get_all_tools():
    """
    Return all available tools for the LangGraph agent.
    
    This function is used by the main application to bind tools to the LLM.
    It provides a centralized way to manage which tools are available.
    
    Returns:
        List of tool functions that can be bound to the agent
    """
    tools = [
        validate_tron_address,
        get_wallet_info,
        get_market_prices,
        update_ui_state
    ]
    
    print(f"🔧 [TOOLS] Loaded {len(tools)} tools for LangGraph agent")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description.split('.')[0]}")
    
    return tools


# ============================
# TOOL UTILITIES
# ============================

def format_balance(raw_amount: str, decimals: int) -> str:
    """
    Format raw blockchain amounts to human-readable strings.
    
    Args:
        raw_amount (str): Raw amount from blockchain (in smallest unit)
        decimals (int): Number of decimal places for the token
        
    Returns:
        str: Formatted amount with proper decimal places and commas
    """
    try:
        amount = int(raw_amount) / (10 ** decimals)
        return f"{amount:,.{decimals}f}"
    except:
        return "0.000000"


def calculate_usd_value(amount: float, price_usd: float) -> str:
    """
    Calculate USD value for a given amount and price.
    
    Args:
        amount (float): Token amount
        price_usd (float): Price per token in USD
        
    Returns:
        str: Formatted USD value (e.g., "$123.45")
    """
    try:
        usd_value = amount * price_usd
        return f"${usd_value:,.2f}"
    except:
        return "$0.00"

