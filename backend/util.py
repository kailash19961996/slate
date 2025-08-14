"""
SLATE Backend Utilities
Utility functions for validation, formatting, and common operations
"""

import json
import re
import base58
from typing import Any, Dict, Optional, Union
from datetime import datetime
import hashlib


def safe_json_parse(json_string: str, default: Any = None) -> Any:
    """Safely parse JSON string, returning default value on error"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float, returning default on error"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int, returning default on error"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def validate_address(address: str) -> bool:
    """
    Validate TRON wallet address format
    TRON addresses start with 'T' and are 34 characters long
    """
    if not address or not isinstance(address, str):
        return False
    
    # Basic format check
    if not address.startswith('T') or len(address) != 34:
        return False
    
    # Check if it's valid base58
    try:
        base58.b58decode(address)
        return True
    except:
        return False


def format_tron_address(address: str) -> str:
    """Format TRON address for display (show first 6 and last 4 characters)"""
    if not address or len(address) < 10:
        return address
    return f"{address[:6]}...{address[-4:]}"


def format_balance(balance: Union[str, float, int], decimals: int = 6) -> str:
    """Format balance for display with proper decimal places"""
    try:
        balance_float = float(balance)
        return f"{balance_float:,.{decimals}f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return "0"


def format_currency(amount: Union[str, float, int], currency: str = "USD") -> str:
    """Format amount as currency"""
    try:
        amount_float = float(amount)
        if currency.upper() == "USD":
            return f"${amount_float:,.2f}"
        else:
            return f"{amount_float:,.2f} {currency}"
    except (ValueError, TypeError):
        return f"0 {currency}"


def validate_tron_amount(amount: str) -> tuple[bool, float]:
    """
    Validate TRON amount string and return (is_valid, parsed_amount)
    """
    try:
        parsed = float(amount)
        if parsed < 0:
            return False, 0.0
        if parsed > 1000000000:  # Reasonable upper limit
            return False, 0.0
        return True, parsed
    except (ValueError, TypeError):
        return False, 0.0


def generate_transaction_id() -> str:
    """Generate a unique transaction ID"""
    timestamp = str(int(datetime.now().timestamp() * 1000))
    random_part = hashlib.sha256(timestamp.encode()).hexdigest()[:8]
    return f"tx_{timestamp}_{random_part}"


def calculate_transaction_fee(amount: float, fee_rate: float = 0.01) -> float:
    """Calculate transaction fee based on amount and fee rate"""
    return max(amount * fee_rate, 1.0)  # Minimum 1 TRX fee


def validate_json_rpc_response(response: Dict[str, Any]) -> bool:
    """Validate JSON-RPC response format"""
    return (
        isinstance(response, dict) and
        "result" in response and
        "error" not in response
    )


def extract_error_message(error: Any) -> str:
    """Extract readable error message from various error types"""
    if isinstance(error, dict):
        if "message" in error:
            return str(error["message"])
        elif "error" in error:
            return str(error["error"])
    
    if hasattr(error, "message"):
        return str(error.message)
    
    return str(error)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def is_valid_url(url: str) -> bool:
    """Basic URL validation"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def normalize_token_symbol(symbol: str) -> str:
    """Normalize token symbol to uppercase"""
    return symbol.strip().upper() if symbol else ""


def parse_token_amount(amount_str: str, decimals: int = 6) -> Optional[int]:
    """
    Parse token amount string to smallest unit (like wei for ETH)
    Returns None if parsing fails
    """
    try:
        amount_float = float(amount_str)
        return int(amount_float * (10 ** decimals))
    except (ValueError, TypeError):
        return None


def format_token_amount(amount_int: int, decimals: int = 6) -> str:
    """
    Format token amount from smallest unit to human readable
    """
    try:
        amount_float = amount_int / (10 ** decimals)
        return format_balance(amount_float, decimals)
    except (ValueError, TypeError, ZeroDivisionError):
        return "0"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def get_time_ago(timestamp: Union[str, datetime, int]) -> str:
    """Get human readable time ago string"""
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, int):
            dt = datetime.fromtimestamp(timestamp)
        else:
            dt = timestamp
        
        now = datetime.now()
        diff = now - dt
        
        seconds = int(diff.total_seconds())
        
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
    except:
        return "unknown"


def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitize user input by removing dangerous characters and limiting length"""
    if not isinstance(input_str, str):
        return ""
    
    # Remove dangerous characters
    sanitized = re.sub(r'[<>"\']', '', input_str)
    
    # Limit length
    return sanitized[:max_length].strip()


def batch_process(items: list, batch_size: int = 10):
    """Generator to process items in batches"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on failure"""
    import time
    
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
                break
        raise last_exception
    
    return wrapper


# Predefined constants
TRON_NETWORK_CONFIGS = {
    "mainnet": {
        "name": "TRON Mainnet",
        "chainId": "0x2b6653dc",
        "rpcUrl": "https://api.trongrid.io",
        "explorerUrl": "https://tronscan.org"
    },
    "nile": {
        "name": "TRON Nile Testnet", 
        "chainId": "0xcd8690dc",
        "rpcUrl": "https://nile.trongrid.io",
        "explorerUrl": "https://nile.tronscan.org"
    },
    "shasta": {
        "name": "TRON Shasta Testnet",
        "chainId": "0x94a9059e",
        "rpcUrl": "https://api.shasta.trongrid.io", 
        "explorerUrl": "https://shasta.tronscan.org"
    }
}

SUPPORTED_TOKENS = {
    "TRX": {"name": "TRON", "decimals": 6, "symbol": "TRX"},
    "USDT": {"name": "Tether USD", "decimals": 6, "symbol": "USDT"},
    "USDC": {"name": "USD Coin", "decimals": 6, "symbol": "USDC"},
    "JST": {"name": "JUST", "decimals": 18, "symbol": "JST"},
    "SUN": {"name": "SUN", "decimals": 18, "symbol": "SUN"},
    "BTT": {"name": "BitTorrent", "decimals": 18, "symbol": "BTT"}
}


def get_token_info(symbol: str) -> Optional[Dict[str, Any]]:
    """Get token information by symbol"""
    normalized_symbol = normalize_token_symbol(symbol)
    return SUPPORTED_TOKENS.get(normalized_symbol)


def get_network_config(network: str = "mainnet") -> Dict[str, str]:
    """Get network configuration"""
    return TRON_NETWORK_CONFIGS.get(network.lower(), TRON_NETWORK_CONFIGS["mainnet"])
