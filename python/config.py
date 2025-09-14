"""
Configuration file for Python arbitrage monitoring
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Network Configuration
RPC_URL = os.getenv("SEPOLIA_RPC_URL", "https://eth-sepolia.g.alchemy.com/v2/0qBZbUmSupk6zy4Ig9GN5")
CONTRACT_ADDRESS = os.getenv("ARB_EXECUTOR_ADDRESS", "0x96888C4B6e569c74fDbDcc40cacf1127421F993c")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "0xce0bbf67acfb2d7038b39cdaed5dc84ef0b48a5e1ba268fa339ac2d1c47a45f8")

# Risk Management Parameters
MIN_PROFIT_THRESHOLD = 0.001  # ETH
MAX_SLIPPAGE = 0.03  # 3%
MAX_GAS_PRICE = 50  # gwei
MIN_LIQUIDITY = 10000  # USD

# Token Addresses (Sepolia)
TOKENS = {
    "WETH": "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
    "USDC": "0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8",
    "USDT": "0x7169D38820dfd117C3FA1f22a697dBA58d90BA06"
}

# Router Addresses (Sepolia)
ROUTERS = {
    "UNISWAP_V2": "0xC532A74256D3db4d4444457e8D5c9C7B6e1c3c6A",
    "SUSHISWAP": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"
}

# DEX API Endpoints
DEX_ENDPOINTS = {
    "uniswap_v2": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2",
    "sushiswap": "https://api.thegraph.com/subgraphs/name/sushiswap/exchange"
}

# Monitoring Configuration
MONITORING_INTERVAL = 30  # seconds
MAX_OPPORTUNITIES_PER_CYCLE = 10
CONFIDENCE_THRESHOLD = 0.7
