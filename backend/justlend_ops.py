"""
SLATE Backend - JustLend Operations
==================================
Provides read-only operations for the JustLend DeFi protocol.
"""

from typing import Any, Dict
from tronpy import Tron
from tron_client import (
    create_tron_client, 
    _resolve_unitroller, 
    _per_block_to_apy, 
    _with_retries, 
    _sleep_ms,
    JUSTLEND_MAX_MARKETS,
    JUSTLEND_PER_MARKET_DELAY_MS
)

COMPTROLLER_ABI = [
    {"name":"getAllMarkets","type":"function","inputs":[],"outputs":[{"name":"","type":"address[]"}],"stateMutability":"view","constant":True},
    {"name":"markets","type":"function","inputs":[{"name":"jToken","type":"address"}],
     "outputs":[{"name":"isListed","type":"bool"},{"name":"collateralFactorMantissa","type":"uint256"},{"name":"isComped","type":"bool"}],
     "stateMutability":"view","constant":True},
    {"name":"getAccountLiquidity","type":"function","inputs":[{"name":"account","type":"address"}],
     "outputs":[{"name":"error","type":"uint256"},{"name":"liquidity","type":"uint256"},{"name":"shortfall","type":"uint256"}],
     "stateMutability":"view","constant":True},
]

JTOKEN_ABI = [
    {"name":"symbol","type":"function","inputs":[],"outputs":[{"name":"","type":"string"}],"stateMutability":"view","constant":True},
    {"name":"supplyRatePerBlock","type":"function","inputs":[],"outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","constant":True},
    {"name":"borrowRatePerBlock","type":"function","inputs":[],"outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","constant":True},
    {"name":"exchangeRateStored","type":"function","inputs":[],"outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","constant":True},
    {"name":"totalBorrows","type":"function","inputs":[],"outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","constant":True},
    {"name":"getAccountSnapshot","type":"function","inputs":[{"name":"account","type":"address"}],
     "outputs":[{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"}],
     "stateMutability":"view","constant":True},
]

def _get_comptroller(client: Tron):
    """Get JustLend Comptroller contract with ABI loaded."""
    unitroller_addr = _resolve_unitroller()
    print(f"⚙️ [JUSTLEND] Loading Comptroller contract: {unitroller_addr}")
    c = client.get_contract(unitroller_addr)
    c.abi = COMPTROLLER_ABI
    print("✅ [JUSTLEND] Comptroller contract loaded")
    return c

def _get_jtoken(client: Tron, addr: str):
    """Get JToken contract with ABI loaded."""
    print(f"⚙️ [JUSTLEND] Loading JToken contract: {addr}")
    j = client.get_contract(addr)
    j.abi = JTOKEN_ABI
    print("✅ [JUSTLEND] JToken contract loaded")
    return j

def list_markets(limit: int = None) -> Dict[str, Any]:
    """
    Fetch JustLend market data with detailed information.
    Args:
        limit: Maximum number of markets to return (uses env config if None)
    Returns:
        Dict containing market data with network info or error details
    """
    if limit is None:
        limit = JUSTLEND_MAX_MARKETS
    
    print(f"⚙️ [JUSTLEND] Fetching markets list (limit: {limit})")
    try:
        client = create_tron_client()
        comp = _get_comptroller(client)
        print("⚙️ [JUSTLEND] Getting all market addresses...")
        addrs = _with_retries(lambda: comp.functions.getAllMarkets(), label="getAllMarkets")
        addrs = (addrs or [])[:limit]
        print(f"⚙️ [JUSTLEND] Processing {len(addrs)} markets with {JUSTLEND_PER_MARKET_DELAY_MS}ms delays...")
        
        markets = []
        for i, addr in enumerate(addrs, 1):
            print(f"⚙️ [JUSTLEND] Processing market {i}/{len(addrs)}: {addr}")
            try:
                # Add delay between market calls to avoid rate limiting
                if i > 1:  # No delay for first market
                    print(f"⚙️ [JUSTLEND] Waiting {JUSTLEND_PER_MARKET_DELAY_MS}ms before next market...")
                    _sleep_ms(JUSTLEND_PER_MARKET_DELAY_MS)
                
                j = _get_jtoken(client, addr)
                sym = _with_retries(lambda: j.functions.symbol(), label=f"getSymbol({addr})")
                print(f"⚙️ [JUSTLEND] Market symbol: {sym}")
                
                s_rate = _with_retries(lambda: int(j.functions.supplyRatePerBlock()), label=f"supplyRatePerBlock({sym})")
                b_rate = _with_retries(lambda: int(j.functions.borrowRatePerBlock()), label=f"borrowRatePerBlock({sym})")
                exch  = _with_retries(lambda: int(j.functions.exchangeRateStored()), label=f"exchangeRateStored({sym})")
                bor   = _with_retries(lambda: int(j.functions.totalBorrows()), label=f"totalBorrows({sym})")
                _, c_factor, _ = _with_retries(lambda: comp.functions.markets(addr), label=f"markets({sym})")
                
                market_data = {
                    "address": addr,
                    "symbol": sym,
                    "collateral_factor_pct": int(c_factor) / 1e16,
                    "supply_rate_per_block": s_rate,
                    "supply_apy_pct_approx": round(_per_block_to_apy(s_rate), 2),
                    "borrow_rate_per_block": b_rate,
                    "borrow_apy_pct_approx": round(_per_block_to_apy(b_rate), 2),
                    "exchange_rate_mantissa": exch,
                    "total_borrows_mantissa": bor
                }
                markets.append(market_data)
                print(f"✅ [JUSTLEND] Market {sym}: Supply APY {market_data['supply_apy_pct_approx']}%, Borrow APY {market_data['borrow_apy_pct_approx']}%")
                
            except Exception as e:
                print(f"⚠️ [JUSTLEND] Failed to process market {addr}: {e}")
                # Continue with other markets instead of failing completely
                continue
        
        result = {
            "success": True,
            "network": _resolve_unitroller().split('/')[-1],
            "unitroller": _resolve_unitroller(),
            "count": len(markets),
            "requested_limit": limit,
            "markets": markets
        }
        print(f"✅ [JUSTLEND] Successfully fetched {len(markets)} out of {len(addrs)} markets")
        return result
        
    except Exception as e:
        print(f"❌ [JUSTLEND] Error fetching markets: {e}")
        # Return error in a structured format for summarizer
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "network": "unknown",
            "count": 0,
            "markets": []
        }

def market_detail(symbol: str) -> Dict[str, Any]:
    """
    Fetch detailed information for a specific JustLend market by symbol.
    Args:
        symbol: The symbol of the market (e.g., "JUSDT")
    Returns:
        Dict containing market details or error information
    """
    print(f"⚙️ [JUSTLEND] Fetching market detail for symbol: {symbol}")
    try:
        client = create_tron_client()
        comp = _get_comptroller(client)
        all_markets = _with_retries(lambda: comp.functions.getAllMarkets(), label="getAllMarkets for detail")
        
        for i, addr in enumerate(all_markets):
            # Add delay between market checks to avoid rate limiting
            if i > 0:
                print(f"⚙️ [JUSTLEND] Waiting {JUSTLEND_PER_MARKET_DELAY_MS}ms before checking next market...")
                _sleep_ms(JUSTLEND_PER_MARKET_DELAY_MS)
            
            j = _get_jtoken(client, addr)
            sym = _with_retries(lambda: j.functions.symbol(), label=f"getSymbol({addr})")
            
            if sym.lower() == symbol.lower():
                srate = _with_retries(lambda: int(j.functions.supplyRatePerBlock()), label=f"supplyRatePerBlock({sym})")
                brate = _with_retries(lambda: int(j.functions.borrowRatePerBlock()), label=f"borrowRatePerBlock({sym})")
                exch  = _with_retries(lambda: int(j.functions.exchangeRateStored()), label=f"exchangeRateStored({sym})")
                bor   = _with_retries(lambda: int(j.functions.totalBorrows()), label=f"totalBorrows({sym})")
                _, c_factor, _ = _with_retries(lambda: comp.functions.markets(addr), label=f"markets({sym})")
                
                result = {
                    "success": True,
                    "network": _resolve_unitroller().split('/')[-1],
                    "unitroller": _resolve_unitroller(),
                    "market": {
                        "address": addr,
                        "symbol": sym,
                        "collateral_factor_pct": int(c_factor) / 1e16,
                        "supply_rate_per_block": srate,
                        "supply_apy_pct_approx": round(_per_block_to_apy(srate), 2),
                        "borrow_rate_per_block": brate,
                        "borrow_apy_pct_approx": round(_per_block_to_apy(brate), 2),
                        "exchange_rate_mantissa": exch,
                        "total_borrows_mantissa": bor
                    }
                }
                print(f"✅ [JUSTLEND] Successfully fetched detail for {sym}")
                return result
        
        # Market not found
        print(f"⚠️ [JUSTLEND] Market symbol '{symbol}' not found.")
        return {
            "success": False,
            "error": f"Market symbol '{symbol}' not found on {_resolve_unitroller().split('/')[-1]}.",
            "error_type": "MarketNotFound",
            "network": _resolve_unitroller().split('/')[-1],
            "symbol_requested": symbol
        }
        
    except Exception as e:
        print(f"❌ [JUSTLEND] Error fetching market detail: {e}")
        # Return error in structured format for summarizer
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "network": "unknown",
            "symbol_requested": symbol
        }

def user_position(address: str) -> Dict[str, Any]:
    """
    Fetch user's lending positions and liquidity on JustLend.
    Args:
        address: The user's wallet address
    Returns:
        Dict containing user's positions and liquidity/shortfall or error information
    """
    print(f"⚙️ [JUSTLEND] Fetching user position for address: {address}")
    try:
        client = create_tron_client()
        comp = _get_comptroller(client)
        positions = []
        all_markets = _with_retries(lambda: comp.functions.getAllMarkets(), label="getAllMarkets for user position")
        
        for i, addr in enumerate(all_markets):
            # Add delay between market calls to avoid rate limiting
            if i > 0:
                print(f"⚙️ [JUSTLEND] Waiting {JUSTLEND_PER_MARKET_DELAY_MS}ms before checking next market...")
                _sleep_ms(JUSTLEND_PER_MARKET_DELAY_MS)
            
            try:
                j = _get_jtoken(client, addr)
                sym = _with_retries(lambda: j.functions.symbol(), label=f"getSymbol({addr})")
                _, token_bal, borrow_bal, exchMant = _with_retries(lambda: j.functions.getAccountSnapshot(address), label=f"getAccountSnapshot({sym})")
                
                positions.append({
                    "jtoken": addr,
                    "symbol": sym,
                    "token_balance_mantissa": int(token_bal),
                    "borrow_balance_mantissa": int(borrow_bal),
                    "exchange_rate_mantissa": int(exchMant),
                })
            except Exception as e:
                print(f"⚠️ [JUSTLEND] Failed to get position for market {addr}: {e}")
                # Continue with other markets
                continue
        
        _, liquidity, shortfall = _with_retries(lambda: comp.functions.getAccountLiquidity(address), label=f"getAccountLiquidity({address})")
        
        result = {
            "success": True,
            "network": _resolve_unitroller().split('/')[-1],
            "address": address,
            "positions": positions,
            "liquidity_mantissa": int(liquidity),
            "shortfall_mantissa": int(shortfall)
        }
        print(f"✅ [JUSTLEND] Successfully fetched user position for {address}")
        return result
        
    except Exception as e:
        print(f"❌ [JUSTLEND] Error fetching user position: {e}")
        # Return error in structured format for summarizer
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "network": "unknown",
            "address": address
        }