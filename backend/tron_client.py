"""
SLATE Backend - TRON Client and Utilities
========================================
Handles TRON network client creation and common blockchain-related helpers.
"""

import os
import time
import random
from tronpy import Tron
from tronpy.providers import HTTPProvider

# Rate limiting configuration (to avoid TronGrid 429 errors)
JUSTLEND_MAX_MARKETS = int(os.getenv("JUSTLEND_MAX_MARKETS", "4"))
JUSTLEND_PER_MARKET_DELAY_MS = int(os.getenv("JUSTLEND_PER_MARKET_DELAY_MS", "1000"))
JUSTLEND_RETRY_DELAY_MS = int(os.getenv("JUSTLEND_RETRY_DELAY_MS", "2000"))
JUSTLEND_MAX_RETRIES = int(os.getenv("JUSTLEND_MAX_RETRIES", "3"))

def create_tron_client() -> Tron:
    """
    Create TRON network client based on configured environment.
    Returns:
        Tron: Configured client for mainnet (with API key) or nile testnet
    """
    tron_network = os.getenv("TRON_NETWORK", "mainnet").lower()
    trongrid_api_key = os.getenv("TRONGRID_API_KEY")
    
    print(f"🌐 [TRON] Creating client for network: {tron_network}")
    
    if tron_network == "mainnet":
        print("🌐 [TRON] Using TronGrid mainnet with API key")
        client = Tron(provider=HTTPProvider(api_key=trongrid_api_key, timeout=20.0))
    else:
        print("🌐 [TRON] Using Nile testnet public endpoint")
        client = Tron(provider=HTTPProvider(endpoint_uri="https://nile.trongrid.io", timeout=20.0))
    
    print("✅ [TRON] Client created successfully")
    return client

def _resolve_unitroller() -> str:
    """Resolve JustLend Unitroller address based on network."""
    tron_network = os.getenv("TRON_NETWORK", "mainnet").lower()
    print(f"⚙️ [JUSTLEND] Resolving Unitroller address for network: {tron_network}")
    
    if tron_network == "mainnet":
        addr = os.getenv("JL_UNITROLLER_MAIN", "TGjYzgCyPobsNS9n6WcbdLVR9dH7mWqFx7")
        print(f"⚙️ [JUSTLEND] Using mainnet Unitroller: {addr}")
        return addr
    
    nile = os.getenv("JL_UNITROLLER_NILE")
    if not nile:
        print("⚠️ [ERROR] JL_UNITROLLER_NILE required for nile network")
        raise RuntimeError("JL_UNITROLLER_NILE is required when TRON_NETWORK=nile")
    
    print(f"⚙️ [JUSTLEND] Using nile Unitroller: {nile}")
    return nile

def _per_block_to_apy(rate_per_block: int) -> float:
    """
    Convert per-block interest rate to approximate APY.
    Args:
        rate_per_block: Interest rate per block in mantissa format (1e18)
    Returns:
        float: Approximate APY as percentage
    """
    blocks_year = 7_300_000
    r = float(rate_per_block) / 1e18
    apy = ((1 + r) ** blocks_year - 1) * 100.0
    print(f"⚙️ [CALC] Rate per block: {rate_per_block} → APY: {apy:.2f}%")
    return apy

def _sleep_ms(ms: int):
    """Sleep for specified milliseconds."""
    time.sleep(ms / 1000.0)

def _with_retries(fn, *, label: str, max_attempts: int = None, base_delay_ms: int = None):
    """
    Execute function with exponential backoff retry logic.
    Args:
        fn: Function to execute
        label: Description for logging
        max_attempts: Maximum retry attempts
        base_delay_ms: Base delay in milliseconds
    Returns:
        Result of successful function execution
    Raises:
        Exception: If all retry attempts fail
    """
    # Use configured values if not provided
    if max_attempts is None:
        max_attempts = JUSTLEND_MAX_RETRIES
    if base_delay_ms is None:
        base_delay_ms = JUSTLEND_RETRY_DELAY_MS // 4  # Base is 1/4 of retry delay
    
    attempt = 0
    while True:
        attempt += 1
        try:
            print(f"⚙️ [RETRY] {label} - Attempt {attempt}/{max_attempts}")
            result = fn()
            print(f"✅ [RETRY] {label} - Success on attempt {attempt}")
            return result
        except Exception as e:
            print(f"⚠️ [RETRY] {label} - Failed attempt {attempt}: {type(e).__name__}: {e}")
            if attempt >= max_attempts:
                print(f"❌ [RETRY] {label} - All {max_attempts} attempts failed")
                raise
            delay = int(base_delay_ms * (2 ** (attempt - 1)) * (1 + 0.25 * random.random()))
            print(f"⚙️ [RETRY] {label} - Waiting {delay}ms before retry...")
            _sleep_ms(delay)