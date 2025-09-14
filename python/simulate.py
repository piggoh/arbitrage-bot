from web3 import Web3

# -------------------------
# Setup
# -------------------------
rpc_url = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(rpc_url))
print("Connected:", w3.is_connected())

# Routers
UNISWAP_ROUTER = Web3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
SUSHISWAP_ROUTER = Web3.to_checksum_address("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")

router_abi = [
    {
        "name": "getAmountsOut",
        "outputs": [{"type": "uint256[]", "name": ""}],
        "inputs": [
            {"type": "uint256", "name": "amountIn"},
            {"type": "address[]", "name": "path"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

uni = w3.eth.contract(address=UNISWAP_ROUTER, abi=router_abi)
sushi = w3.eth.contract(address=SUSHISWAP_ROUTER, abi=router_abi)

TOKENS = {
    "WETH": Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    "USDC": Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
}

# -------------------------
# Helpers
# -------------------------
def get_price(router, amount_in):
    path = [TOKENS["WETH"], TOKENS["USDC"]]
    return router.functions.getAmountsOut(amount_in, path).call()[1]

# -------------------------
# Arbitrage check
# -------------------------
amount_in = w3.to_wei(1, "ether")  # 1 WETH

uni_out = get_price(uni, amount_in)
sushi_out = get_price(sushi, amount_in)

print(f"💹 Uniswap (raw): {uni_out/1e6:.2f} USDC")
print(f"🍣 SushiSwap (raw): {sushi_out/1e6:.2f} USDC")

# Slippage assumptions
SLIPPAGE = {
    "Uniswap": 0.005,   # 1.5%
    "SushiSwap": 0.005  # 0.5%
}

# Adjusted after slippage
uni_adj = uni_out * (1 - SLIPPAGE["Uniswap"])
sushi_adj = sushi_out * (1 - SLIPPAGE["SushiSwap"])

print(f"💹 Uniswap (after slippage): {uni_adj/1e6:.2f} USDC")
print(f"🍣 SushiSwap (after slippage): {sushi_adj/1e6:.2f} USDC")

# Decide trade direction
if sushi_adj > uni_adj:
    print("🚀 Buy on Uni, Sell on Sushi")
    buy_price, sell_price = uni_adj, sushi_adj
else:
    print("🚀 Buy on Sushi, Sell on Uni")
    buy_price, sell_price = sushi_adj, uni_adj

# -------------------------
# Economics
# -------------------------
price_diff = sell_price - buy_price

# Gas assumption (typical swap ~150k gas)
gas_est = 150_000
gas_price = w3.eth.gas_price
gas_cost_eth = gas_est * gas_price / 1e18

# Convert gas to USDC using WETH→USDC rate
eth_price_usdc = buy_price / 1e18
gas_cost_usdc = gas_cost_eth * eth_price_usdc

print(f"🔀 Price difference (after slippage): {price_diff/1e6:.4f} USDC")
print(f"⛽ Gas cost: {gas_cost_usdc:.4f} USDC (approx)")

potential_profit = (price_diff / 1e6) - gas_cost_usdc
print(f"📊 Potential Profit (after slippage): {potential_profit:.4f} USDC")




# from web3 import Web3

# # -------------------------
# # Setup
# # -------------------------
# rpc_url = "http://127.0.0.1:8545"
# w3 = Web3(Web3.HTTPProvider(rpc_url))
# print("Connected:", w3.is_connected())

# account = w3.eth.accounts[0]

# UNISWAP_ROUTER = Web3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
# SUSHISWAP_ROUTER = Web3.to_checksum_address("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")

# router_abi = [
#     {
#         "name": "swapExactTokensForTokens",
#         "outputs": [{"type": "uint256[]", "name": ""}],
#         "inputs": [
#             {"type": "uint256", "name": "amountIn"},
#             {"type": "uint256", "name": "amountOutMin"},
#             {"type": "address[]", "name": "path"},
#             {"type": "address", "name": "to"},
#             {"type": "uint256", "name": "deadline"}
#         ],
#         "stateMutability": "nonpayable",
#         "type": "function"
#     },
#     {
#         "name": "getAmountsOut",
#         "outputs": [{"type": "uint256[]", "name": ""}],
#         "inputs": [
#             {"type": "uint256", "name": "amountIn"},
#             {"type": "address[]", "name": "path"}
#         ],
#         "stateMutability": "view",
#         "type": "function"
#     }
# ]

# uni = w3.eth.contract(address=UNISWAP_ROUTER, abi=router_abi)
# sushi = w3.eth.contract(address=SUSHISWAP_ROUTER, abi=router_abi)

# TOKENS = {
#     "WETH": Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
#     "USDC": Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
# }

# # -------------------------
# # Helpers
# # -------------------------
# def get_price(router, amount_in):
#     path = [TOKENS["WETH"], TOKENS["USDC"]]
#     return router.functions.getAmountsOut(amount_in, path).call()[1]

# # -------------------------
# # Simulate arbitrage
# # -------------------------
# amount_in = w3.to_wei(1, "ether")  # 1 WETH

# uni_out = get_price(uni, amount_in)
# sushi_out = get_price(sushi, amount_in)

# print(f"💹 Uniswap → {uni_out/1e6:.2f} USDC")
# print(f"🍣 SushiSwap → {sushi_out/1e6:.2f} USDC")

# # Which side is cheaper to buy
# if sushi_out > uni_out:
#     print("🚀 Buy on Uni, Sell on Sushi")
#     buy_router, sell_router = uni, sushi
#     buy_price, sell_price = uni_out, sushi_out
# else:
#     print("🚀 Buy on Sushi, Sell on Uni")
#     buy_router, sell_router = sushi, uni
#     buy_price, sell_price = sushi_out, uni_out

# # -------------------------
# # Calculate arbitrage economics
# # -------------------------
# price_diff = sell_price - buy_price
# slippage_pct = (price_diff / buy_price) * 100

# print(f"🔀 Price difference: {price_diff/1e6:.4f} USDC")
# print(f"📉 Slippage %: {slippage_pct:.4f}%")

# # -------------------------
# # Gas estimation
# # -------------------------
# try:
#     tx = buy_router.functions.swapExactTokensForTokens(
#         amount_in,
#         0,  # no slippage protection here
#         [TOKENS["WETH"], TOKENS["USDC"]],
#         account,
#         9999999999
#     ).build_transaction({
#         "from": account,
#         "gas": 500000,
#         "gasPrice": w3.eth.gas_price,
#         "nonce": w3.eth.get_transaction_count(account),
#     })

#     gas_est = w3.eth.estimate_gas(tx)
#     gas_price = w3.eth.gas_price
#     gas_cost_eth = gas_est * gas_price / 1e18
#     gas_cost_usd = gas_cost_eth * (buy_price / 1e18)  # WETH→USDC reference

#     print(f"⛽ Gas estimated: {gas_est}")
#     print(f"⛽ Gas price: {gas_price / 1e9:.2f} gwei")
#     print(f"💰 Gas cost: {gas_cost_usd:.4f} USDC (approx)")

#     # -------------------------
#     # Profitability Check
#     # -------------------------
#     potential_profit = (price_diff / 1e6) - gas_cost_usd
#     print(f"📊 Potential Profit: {potential_profit:.4f} USDC")

# except Exception as e:
#     print("Simulation error:", e)
