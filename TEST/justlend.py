# justlend_read.py
from tronpy import Tron

client = Tron()  # defaults to https://api.trongrid.io

UNITROLLER = "Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # fill me
JUSDT      = "Tyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"

comptroller_abi = [
    {"name":"getAllMarkets","type":"Function","inputs":[],"outputs":[{"type":"address[]"}]},
    {"name":"markets","type":"Function","inputs":[{"name":"jToken","type":"address"}],
     "outputs":[{"type":"bool"},{"type":"uint256"},{"type":"bool"}]},
    {"name":"getAccountLiquidity","type":"Function","inputs":[{"name":"account","type":"address"}],
     "outputs":[{"type":"uint256"},{"type":"uint256"},{"type":"uint256"}]},
]

jtoken_abi = [
    {"name":"symbol","type":"Function","inputs":[],"outputs":[{"type":"string"}]},
    {"name":"supplyRatePerBlock","type":"Function","inputs":[],"outputs":[{"type":"uint256"}]},
    {"name":"borrowRatePerBlock","type":"Function","inputs":[],"outputs":[{"type":"uint256"}]},
    {"name":"exchangeRateStored","type":"Function","inputs":[],"outputs":[{"type":"uint256"}]},
    {"name":"totalBorrows","type":"Function","inputs":[],"outputs":[{"type":"uint256"}]},
    {"name":"getAccountSnapshot","type":"Function","inputs":[{"name":"account","type":"address"}],
     "outputs":[{"type":"uint256"},{"type":"uint256"},{"type":"uint256"},{"type":"uint256"}]},
]

comp = client.get_contract(UNITROLLER, abi=comptroller_abi)
j = client.get_contract(JUSDT, abi=jtoken_abi)

# 1) All markets
markets = comp.functions.getAllMarkets()
print("Markets:", markets)

# 2) Market stats
sym = j.functions.symbol()
s_rate = j.functions.supplyRatePerBlock()
b_rate = j.functions.borrowRatePerBlock()
exch = j.functions.exchangeRateStored()
borrows = j.functions.totalBorrows()
print(sym, int(s_rate), int(b_rate), int(exch), int(borrows))

# 3) Collateral factor
is_listed, c_factor, _ = comp.functions.markets(JUSDT)
print("CollateralFactorMantissa:", int(c_factor))

# 4) User snapshot & liquidity
WALLET = "Tzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
err, token_bal, borrow_bal, exchMant = j.functions.getAccountSnapshot(WALLET)
print("User tokenBal:", int(token_bal), "borrowBal:", int(borrow_bal))

err, liquidity, shortfall = comp.functions.getAccountLiquidity(WALLET)
print("Liquidity:", int(liquidity), "Shortfall:", int(shortfall))
