"""
SLATE Backend Tools
LangGraph tools for blockchain operations and wallet management
"""

import json
import requests
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from langchain.tools import tool
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from util import (
    validate_address, format_tron_address, format_balance, 
    format_currency, safe_float, safe_json_parse,
    get_token_info, get_network_config
)


# -------------------------
# Tool Input Models
# -------------------------

class WalletConnectionInput(BaseModel):
    """Input for wallet connection tool"""
    wallet_address: str = Field(description="TRON wallet address to connect")


class BalanceCheckInput(BaseModel):
    """Input for balance checking tool"""
    wallet_address: str = Field(description="TRON wallet address to check balance")
    include_tokens: bool = Field(default=True, description="Include token balances")


class PriceCheckInput(BaseModel):
    """Input for price checking tool"""
    symbol: str = Field(description="Cryptocurrency symbol (e.g., TRX, BTC, ETH)")
    vs_currency: str = Field(default="usd", description="Currency to compare against")


class TransactionCheckInput(BaseModel):
    """Input for transaction status checking"""
    tx_hash: str = Field(description="Transaction hash to check")


class MarketAnalysisInput(BaseModel):
    """Input for market analysis tool"""
    symbols: List[str] = Field(description="List of cryptocurrency symbols to analyze")
    timeframe: str = Field(default="24h", description="Timeframe for analysis")


# -------------------------
# Core Tools
# -------------------------

@tool("request_wallet_connection", return_direct=False)
def request_wallet_connection(wallet_address: str) -> str:
    """
    Request wallet connection with a TRON address.
    This tool validates the address and initiates the connection process.
    """
    # Validate address format
    if not validate_address(wallet_address):
        return json.dumps({
            "error": "Invalid wallet address format",
            "message": "TRON addresses must start with 'T' and be 34 characters long",
            "valid": False
        })
    
    # Return success response - actual connection handled by main agent
    return json.dumps({
        "address": wallet_address,
        "formatted_address": format_tron_address(wallet_address),
        "valid": True,
        "message": f"Wallet address validated: {format_tron_address(wallet_address)}",
        "next_step": "connect_to_wallet"
    })


@tool("check_wallet_balance", return_direct=False)
def check_wallet_balance(wallet_address: str, include_tokens: bool = True) -> str:
    """
    Check the balance of a TRON wallet address.
    Returns TRX balance and optionally token balances.
    """
    if not validate_address(wallet_address):
        return json.dumps({"error": "Invalid wallet address"})
    
    try:
        # Mock data for now - in production, this would call TRON API
        trx_balance = 1234.567890  # Sample TRX balance
        usd_value = trx_balance * 0.068  # Sample price
        
        result = {
            "address": wallet_address,
            "formatted_address": format_tron_address(wallet_address),
            "trx_balance": format_balance(trx_balance),
            "trx_balance_raw": trx_balance,
            "usd_value": format_currency(usd_value),
            "last_updated": datetime.now().isoformat()
        }
        
        if include_tokens:
            # Mock token data
            result["tokens"] = [
                {
                    "symbol": "USDT",
                    "name": "Tether USD",
                    "balance": "500.000000",
                    "usd_value": "$500.00",
                    "contract": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
                },
                {
                    "symbol": "JST", 
                    "name": "JUST",
                    "balance": "1000.000000000000000000",
                    "usd_value": "$25.30",
                    "contract": "TCFLL5dx5ZJdKnWuesXxi1VPwjLVmWZZy9"
                }
            ]
            result["token_count"] = len(result["tokens"])
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "error": "Failed to fetch balance",
            "message": str(e),
            "address": wallet_address
        })


@tool("get_crypto_price", return_direct=False)
def get_crypto_price(symbol: str, vs_currency: str = "usd") -> str:
    """
    Get current cryptocurrency price from CoinGecko API.
    Supports major cryptocurrencies including TRX.
    """
    try:
        # Map common symbols to CoinGecko IDs
        symbol_map = {
            "TRX": "tron",
            "BTC": "bitcoin", 
            "ETH": "ethereum",
            "USDT": "tether",
            "JST": "just",
            "SUN": "sun-token",
            "BTT": "bittorrent"
        }
        
        coin_id = symbol_map.get(symbol.upper(), symbol.lower())
        
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": vs_currency.lower(),
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true"
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if coin_id not in data:
            return json.dumps({
                "error": "Price not found",
                "symbol": symbol,
                "message": f"Price data for {symbol} not available"
            })
        
        price_data = data[coin_id]
        
        result = {
            "symbol": symbol.upper(),
            "price": price_data.get(vs_currency.lower()),
            "currency": vs_currency.upper(),
            "change_24h": price_data.get(f"{vs_currency.lower()}_24h_change"),
            "market_cap": price_data.get(f"{vs_currency.lower()}_market_cap"),
            "volume_24h": price_data.get(f"{vs_currency.lower()}_24h_vol"),
            "last_updated": datetime.now().isoformat()
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "error": "Failed to fetch price",
            "symbol": symbol,
            "message": str(e)
        })


@tool("check_transaction_status", return_direct=False)
def check_transaction_status(tx_hash: str) -> str:
    """
    Check the status of a TRON transaction.
    Returns transaction details and confirmation status.
    """
    try:
        # Mock transaction data - in production, would call TRON API
        if not tx_hash or len(tx_hash) != 64:
            return json.dumps({
                "error": "Invalid transaction hash",
                "message": "Transaction hash must be 64 characters long"
            })
        
        # Simulate transaction lookup
        result = {
            "tx_hash": tx_hash,
            "status": "confirmed",
            "confirmations": 47,
            "block_number": 58123456,
            "from_address": "TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE",
            "to_address": "TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH",
            "amount": "100.000000",
            "token": "TRX",
            "fee": "1.100000",
            "timestamp": "2024-01-15T10:30:45Z",
            "success": True
        }
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "error": "Failed to check transaction",
            "tx_hash": tx_hash,
            "message": str(e)
        })


@tool("analyze_defi_opportunities", return_direct=False)
def analyze_defi_opportunities(wallet_address: str = None) -> str:
    """
    Analyze DeFi opportunities on TRON network.
    Optionally analyze based on user's current holdings.
    """
    try:
        # Mock DeFi data
        opportunities = [
            {
                "protocol": "JustLend",
                "type": "lending",
                "asset": "TRX",
                "apy": "4.23",
                "tvl": "$45.2M",
                "risk_level": "low",
                "description": "Earn interest by lending TRX"
            },
            {
                "protocol": "JustLend",
                "type": "lending", 
                "asset": "USDT",
                "apy": "8.15",
                "tvl": "$123.5M",
                "risk_level": "low",
                "description": "Earn interest by lending USDT"
            },
            {
                "protocol": "JustSwap",
                "type": "liquidity_pool",
                "asset": "TRX/USDT",
                "apy": "12.45",
                "tvl": "$67.8M", 
                "risk_level": "medium",
                "description": "Provide liquidity to TRX/USDT pool"
            },
            {
                "protocol": "SUN.io",
                "type": "yield_farming",
                "asset": "SUN",
                "apy": "25.67",
                "tvl": "$23.1M",
                "risk_level": "high",
                "description": "Stake SUN tokens for rewards"
            }
        ]
        
        result = {
            "total_opportunities": len(opportunities),
            "opportunities": opportunities,
            "disclaimer": "DeFi investments carry risks. Always do your own research.",
            "last_updated": datetime.now().isoformat()
        }
        
        if wallet_address and validate_address(wallet_address):
            result["personalized"] = True
            result["wallet_address"] = format_tron_address(wallet_address)
            # In production, would filter opportunities based on user's holdings
        
        return json.dumps(result)
        
    except Exception as e:
        return json.dumps({
            "error": "Failed to analyze DeFi opportunities",
            "message": str(e)
        })


@tool("get_market_overview", return_direct=False)
def get_market_overview(timeframe: str = "24h") -> str:
    """
    Get comprehensive cryptocurrency market overview.
    Includes market cap, trends, and top movers.
    """
    try:
        # Mock market data
        overview = {
            "total_market_cap": "$1.68T",
            "total_volume_24h": "$45.2B",
            "btc_dominance": 42.3,
            "eth_dominance": 18.7,
            "market_change_24h": 2.1,
            "fear_greed_index": 65,
            "fear_greed_label": "Greed",
            "top_gainers": [
                {"symbol": "SOL", "change": 8.5, "price": "$85.42"},
                {"symbol": "MATIC", "change": 12.1, "price": "$0.95"},
                {"symbol": "ADA", "change": 5.8, "price": "$0.48"}
            ],
            "top_losers": [
                {"symbol": "AVAX", "change": -3.2, "price": "$28.15"},
                {"symbol": "DOT", "change": -2.8, "price": "$6.85"},
                {"symbol": "LINK", "change": -1.5, "price": "$14.22"}
            ],
            "tron_ecosystem": {
                "trx_price": "$0.068",
                "trx_change_24h": 1.2,
                "total_accounts": "123.5M",
                "total_transactions": "6.8B",
                "defi_tvl": "$345.2M"
            },
            "timeframe": timeframe,
            "last_updated": datetime.now().isoformat()
        }
        
        return json.dumps(overview)
        
    except Exception as e:
        return json.dumps({
            "error": "Failed to fetch market overview",
            "message": str(e)
        })


@tool("explain_blockchain_concept", return_direct=False)
def explain_blockchain_concept(concept: str) -> str:
    """
    Explain blockchain and cryptocurrency concepts in simple terms.
    Educational tool for user learning.
    """
    explanations = {
        "wallet": "A cryptocurrency wallet is like a digital bank account that stores your public and private keys. The public key (address) is like your account number - safe to share. The private key is like your password - never share it!",
        
        "transaction": "A blockchain transaction is a transfer of cryptocurrency from one wallet to another. It's recorded on the blockchain and verified by network validators. Once confirmed, it's permanent and cannot be reversed.",
        
        "defi": "DeFi (Decentralized Finance) allows you to earn interest, trade, and borrow without traditional banks. Smart contracts automatically execute agreements, but they carry risks like smart contract bugs and impermanent loss.",
        
        "staking": "Staking means locking up your cryptocurrency to help secure the network. In return, you earn rewards (like interest). The longer you stake, the more you typically earn, but your funds are locked during this time.",
        
        "liquidity": "Liquidity refers to how easily you can buy or sell an asset. High liquidity means you can trade quickly at stable prices. Low liquidity can lead to price slippage when trading.",
        
        "gas": "Gas fees are the cost of processing transactions on a blockchain. They vary based on network congestion. On TRON, you can use Energy and Bandwidth to reduce costs.",
        
        "smart_contract": "Smart contracts are self-executing programs on the blockchain. They automatically execute when conditions are met, eliminating the need for intermediaries but requiring careful code review.",
        
        "yield_farming": "Yield farming involves providing liquidity to DeFi protocols to earn rewards. It can be profitable but carries risks like impermanent loss, smart contract risks, and market volatility."
    }
    
    concept_lower = concept.lower()
    explanation = explanations.get(concept_lower, f"I don't have a specific explanation for '{concept}' yet, but I'd be happy to help you understand other blockchain concepts!")
    
    return json.dumps({
        "concept": concept,
        "explanation": explanation,
        "category": "educational",
        "timestamp": datetime.now().isoformat()
    })


# -------------------------
# Advanced Tools
# -------------------------

class WalletConnectionTool(BaseTool):
    name = "wallet_connection_tool"
    description = "Comprehensive wallet connection and management tool"
    
    def _run(self, wallet_address: str, operation: str = "connect") -> str:
        """Execute wallet operations"""
        
        if operation == "connect":
            return request_wallet_connection(wallet_address)
        elif operation == "balance":
            return check_wallet_balance(wallet_address)
        elif operation == "disconnect":
            return json.dumps({
                "status": "disconnected",
                "message": "Wallet disconnected successfully"
            })
        else:
            return json.dumps({
                "error": "Unknown operation",
                "available_operations": ["connect", "balance", "disconnect"]
            })


def get_all_tools() -> List[BaseTool]:
    """Return all available tools for the LangGraph agent"""
    return [
        request_wallet_connection,
        check_wallet_balance,
        get_crypto_price,
        check_transaction_status,
        analyze_defi_opportunities,
        get_market_overview,
        explain_blockchain_concept,
        WalletConnectionTool()
    ]


# Tool categories for better organization
TOOL_CATEGORIES = {
    "wallet": [
        "request_wallet_connection",
        "check_wallet_balance",
        "wallet_connection_tool"
    ],
    "market": [
        "get_crypto_price",
        "get_market_overview"
    ],
    "transactions": [
        "check_transaction_status"
    ],
    "defi": [
        "analyze_defi_opportunities"
    ],
    "educational": [
        "explain_blockchain_concept"
    ]
}


def get_tools_by_category(category: str) -> List[str]:
    """Get tool names by category"""
    return TOOL_CATEGORIES.get(category.lower(), [])


def get_tool_by_name(tool_name: str) -> Optional[BaseTool]:
    """Get specific tool by name"""
    all_tools = get_all_tools()
    for tool in all_tools:
        if tool.name == tool_name:
            return tool
    return None
