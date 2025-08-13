import os
from tronpy import Tron
from tronpy.providers import HTTPProvider
from dotenv import load_dotenv

load_dotenv()
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")
if not TRONGRID_API_KEY:
    raise RuntimeError("Missing TRONGRID_API_KEY in environment/.env")

# You can omit endpoint_uri; it defaults to https://api.trongrid.io
client = Tron(
    provider=HTTPProvider(
        # endpoint_uri="https://nile.trongrid.io", # (for nile net)
        api_key=TRONGRID_API_KEY,   # or a list: ["key1","key2"] for rotation
        timeout=20.0
    )
)

# quick sanity check before heavy calls
print("Latest block:", client.get_latest_block_number())
# print("Latest block (Nile):", client.get_latest_block_number())

UNITROLLER = "TGjYzgCyPobsNS9n6WcbdLVR9dH7mWqFx7"
JUSDT      = "TXJgMdjVX5dKiQaUi9QobwNxtSQaFqccvd"

comptroller_abi = [
    {
        "name": "getAllMarkets",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "address[]"}],
        "stateMutability": "view",
        "constant": True,
    },
    {
        "name": "markets",
        "type": "function",
        "inputs": [{"name": "jToken", "type": "address"}],
        "outputs": [
            {"name": "isListed", "type": "bool"},
            {"name": "collateralFactorMantissa", "type": "uint256"},
            {"name": "isComped", "type": "bool"},
        ],
        "stateMutability": "view",
        "constant": True,
    },
    {
        "name": "getAccountLiquidity",
        "type": "function",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [
            {"name": "error", "type": "uint256"},
            {"name": "liquidity", "type": "uint256"},
            {"name": "shortfall", "type": "uint256"},
        ],
        "stateMutability": "view",
        "constant": True,
    },
]

jtoken_abi = [
    {
        "name": "symbol",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "constant": True,
    },
    {
        "name": "supplyRatePerBlock",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "constant": True,
    },
    {
        "name": "borrowRatePerBlock",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "constant": True,
    },
    {
        "name": "exchangeRateStored",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "constant": True,
    },
    {
        "name": "totalBorrows",
        "type": "function",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "constant": True,
    },
    {
        "name": "getAccountSnapshot",
        "type": "function",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [
            {"name": "", "type": "uint256"},
            {"name": "", "type": "uint256"},
            {"name": "", "type": "uint256"},
            {"name": "", "type": "uint256"},
        ],
        "stateMutability": "view",
        "constant": True,
    },
]

comp = client.get_contract(UNITROLLER)
comp.abi = comptroller_abi
j = client.get_contract(JUSDT)
j.abi = jtoken_abi

# 1) All markets
markets = comp.functions.getAllMarkets()
print("Markets:", markets)
print(f"-------------------------------------------------------------------------------")

# 2) Market stats
sym = j.functions.symbol()
s_rate = j.functions.supplyRatePerBlock()
b_rate = j.functions.borrowRatePerBlock()
exch = j.functions.exchangeRateStored()
borrows = j.functions.totalBorrows()
print(sym, int(s_rate), int(b_rate), int(exch), int(borrows))
print(f"-------------------------------------------------------------------------------")

# 3) Collateral factor
is_listed, c_factor, _ = comp.functions.markets(JUSDT)
print("CollateralFactorMantissa:", int(c_factor))
print(f"-------------------------------------------------------------------------------")

# 4) User snapshot & liquidity
WALLET = "TQ2xa671EEwqyU4N8FWUoHTnY2aQNJeF2J"
err, token_bal, borrow_bal, exchMant = j.functions.getAccountSnapshot(WALLET)
print("User tokenBal:", int(token_bal), "borrowBal:", int(borrow_bal))
print(f"-------------------------------------------------------------------------------")

err, liquidity, shortfall = comp.functions.getAccountLiquidity(WALLET)
print("Liquidity:", int(liquidity), "Shortfall:", int(shortfall))
print(f"-------------------------------------------------------------------------------")
