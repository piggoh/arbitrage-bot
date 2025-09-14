# monitor.py
import time
from web3 import Web3

rpc_url = "https://eth-mainnet.g.alchemy.com/v2/0qBZbUmSupk6zy4Ig9GN5"
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

def get_price(router, amount_in=1):
    """Fetch WETH → USDC price from a router"""
    try:
        amt_in = w3.to_wei(amount_in, "ether")
        path = [TOKENS["WETH"], TOKENS["USDC"]]
        amounts = router.functions.getAmountsOut(amt_in, path).call()
        return amounts[1] / 1e6  # USDC decimals = 6
    except:
        return None

while True:
    uni_price = get_price(uni)
    sushi_price = get_price(sushi)
    gas = w3.eth.gas_price / 1e9  # Gwei

    print(f"💹 Uniswap: {uni_price:,.2f} USDC | 🍣 SushiSwap: {sushi_price:,.2f} USDC | ⛽ {gas:.1f} gwei")

    # Arbitrage check
    if abs(uni_price - sushi_price) > 5:  # Example threshold = $5
        if uni_price > sushi_price:
            print(f"🚀 Buy Sushi @ {sushi_price:.2f}, Sell Uni @ {uni_price:.2f}")
        else:
            print(f"🚀 Buy Uni @ {uni_price:.2f}, Sell Sushi @ {sushi_price:.2f}")

    time.sleep(10)
