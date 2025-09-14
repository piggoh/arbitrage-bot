#!/usr/bin/env python3
"""
Arbitrage Monitor - Python integration for advanced arbitrage detection
"""

import requests
import json
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from web3 import Web3
import asyncio
import aiohttp
import json
import os
from decimal import Decimal
from config import TOKENS  # Import token addresses

# Router ABIs (minimal for price checking)
ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

@dataclass
class ArbitrageOpportunity:
    token_a: str
    token_b: str
    amount_in: int
    expected_profit: int
    gas_cost: int
    net_profit: int
    router1: str
    router2: str
    reverse_order: bool
    confidence_score: float

class ArbitrageMonitor:
    def __init__(self, rpc_url: str, contract_address: str, private_key: str):
        # Initialize Web3 with HTTP provider
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Verify connection
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to RPC endpoint: {rpc_url}")
            
        self.contract_address = contract_address
        self.private_key = private_key
        
        # Risk management parameters
        self.min_profit_threshold = 0.001  # ETH
        self.max_slippage = 0.03  # 3%
        self.max_gas_price = 50  # gwei
        self.min_liquidity = 10000  # USD
        

        # Router addresses (Sepolia testnet)
        self.routers = {
            'uniswap': '0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3',  # Uniswap V2 Router
            'sushiswap': '0xeaBcE3E74EF41FB40024a21Cc2ee2F5dDc615791'  # Sushiswap Router (Factory address used as router)
        }
        
        print("Initialized price monitoring for:")
        print(f"Uniswap V2 Router: {self.routers['uniswap']}")
        print(f"Sushiswap Router: {self.routers['sushiswap']}")
    
    async def get_token_prices(self, token_addresses: List[str]) -> Dict[str, float]:
        """Fetch current token prices from multiple DEXs"""
        prices = {}
        
        # Get prices using router contracts
        amount_in = Web3.to_wei(1, 'ether')
        
        for token_address in token_addresses:
            # Get Uniswap price
            try:
                path = [self.w3.to_checksum_address(addr) for addr in [token_address, token_addresses[0]]]
                uni_router = self._get_router_contract(self.routers['uniswap'])
                amounts = uni_router.functions.getAmountsOut(amount_in, path).call()
                prices[f"uniswap_v2_{token_address}"] = {
                    'price': amounts[1] / amount_in,
                    'liquidity': 1.0,  # Simplified
                    'symbol': token_address[-4:]
                }
            except Exception as e:
                print(f"Error getting Uniswap price for {token_address}: {e}")
            
            # Get Sushiswap price
            try:
                sushi_router = self._get_router_contract(self.routers['sushiswap'])
                amounts = sushi_router.functions.getAmountsOut(amount_in, path).call()
                prices[f"sushiswap_{token_address}"] = {
                    'price': amounts[1] / amount_in,
                    'liquidity': 1.0,  # Simplified
                    'symbol': token_address[-4:]
                }
            except Exception as e:
                print(f"Error getting Sushiswap price for {token_address}: {e}")
        
        return prices
    
    async def _fetch_dex_price(self, router_contract, path: List[str], amount_in: int) -> float:
        """Fetch price from a specific DEX router"""
        try:
            amounts = router_contract.functions.getAmountsOut(amount_in, path).call()
            return amounts[1] / amount_in
        except Exception as e:
            print(f"Error fetching price: {e}")
            return 0.0
    
    def calculate_arbitrage_opportunity(self, token_a: str, token_b: str, 
                                       amount_in: int, prices: Dict[str, float]) -> Optional[ArbitrageOpportunity]:
        """Calculate arbitrage opportunity between two DEXs"""
        
        # Get prices from different DEXs
        uniswap_a_price = prices.get(f"uniswap_v2_{token_a}", {}).get('price', 0)
        uniswap_b_price = prices.get(f"uniswap_v2_{token_b}", {}).get('price', 0)
        sushiswap_a_price = prices.get(f"sushiswap_{token_a}", {}).get('price', 0)
        sushiswap_b_price = prices.get(f"sushiswap_{token_b}", {}).get('price', 0)
        
        if not all([uniswap_a_price, uniswap_b_price, sushiswap_a_price, sushiswap_b_price]):
            return None
        
        # Calculate exchange rates
        uniswap_rate = uniswap_b_price / uniswap_a_price if uniswap_a_price > 0 else 0
        sushiswap_rate = sushiswap_b_price / sushiswap_a_price if sushiswap_a_price > 0 else 0
        
        if uniswap_rate == 0 or sushiswap_rate == 0:
            return None
        
        # Calculate potential profit
        # Strategy: Buy on DEX with lower rate, sell on DEX with higher rate
        if uniswap_rate > sushiswap_rate:
            # Buy on SushiSwap, sell on Uniswap
            amount_out_sushi = amount_in * sushiswap_rate
            amount_out_uni = amount_out_sushi / uniswap_rate
            profit = amount_out_uni - amount_in
            router1, router2 = "sushiswap", "uniswap_v2"
            reverse_order = True
        else:
            # Buy on Uniswap, sell on SushiSwap
            amount_out_uni = amount_in * uniswap_rate
            amount_out_sushi = amount_out_uni / sushiswap_rate
            profit = amount_out_sushi - amount_in
            router1, router2 = "uniswap_v2", "sushiswap"
            reverse_order = True
        
        if profit <= 0:
            return None
        
        # Calculate gas costs
        gas_cost = self._estimate_gas_cost()
        
        # Calculate net profit
        net_profit = profit - gas_cost
        
        if net_profit < self.min_profit_threshold:
            return None
        
        # Calculate confidence score based on liquidity and price differences
        confidence = self._calculate_confidence_score(token_a, token_b, prices, profit)
        
        return ArbitrageOpportunity(
            token_a=token_a,
            token_b=token_b,
            amount_in=amount_in,
            expected_profit=profit,
            gas_cost=gas_cost,
            net_profit=net_profit,
            router1=router1,
            router2=router2,
            reverse_order=reverse_order,
            confidence_score=confidence
        )
    
    def _estimate_gas_cost(self) -> int:
        """Estimate gas cost for arbitrage execution"""
        # Typical gas usage for arbitrage: ~200,000 gas
        gas_limit = 200000
        gas_price = self.w3.eth.gas_price
        
        # Convert to ETH
        gas_cost_wei = gas_limit * gas_price
        gas_cost_eth = self.w3.from_wei(gas_cost_wei, 'ether')
        
        return int(gas_cost_eth * 1e18)  # Return in wei
    
    def _calculate_confidence_score(self, token_a: str, token_b: str, 
                                  prices: Dict[str, float], profit: int) -> float:
        """Calculate confidence score for the arbitrage opportunity"""
        # Get liquidity information
        uniswap_liquidity_a = prices.get(f"uniswap_v2_{token_a}", {}).get('liquidity', 0)
        sushiswap_liquidity_a = prices.get(f"sushiswap_{token_a}", {}).get('liquidity', 0)
        
        # Calculate liquidity score (0-1)
        total_liquidity = uniswap_liquidity_a + sushiswap_liquidity_a
        liquidity_score = min(total_liquidity / self.min_liquidity, 1.0)
        
        # Calculate profit score (0-1)
        profit_score = min(profit / (self.min_profit_threshold * 1e18 * 10), 1.0)
        
        # Weighted confidence score
        confidence = (liquidity_score * 0.6) + (profit_score * 0.4)
        
        return confidence
    
    def assess_risk(self, opportunity: ArbitrageOpportunity) -> Dict[str, any]:
        """Comprehensive risk assessment for an arbitrage opportunity"""
        risks = {
            'slippage_risk': 'low',
            'liquidity_risk': 'low',
            'gas_risk': 'low',
            'timing_risk': 'medium',
            'overall_risk': 'low'
        }
        
        # Slippage risk assessment
        if opportunity.expected_profit < opportunity.gas_cost * 2:
            risks['slippage_risk'] = 'high'
        elif opportunity.expected_profit < opportunity.gas_cost * 3:
            risks['slippage_risk'] = 'medium'
        
        # Gas risk assessment
        current_gas_price = self.w3.eth.gas_price
        if current_gas_price > self.max_gas_price * 1e9:  # Convert gwei to wei
            risks['gas_risk'] = 'high'
        
        # Overall risk assessment
        high_risks = sum(1 for risk in risks.values() if risk == 'high')
        medium_risks = sum(1 for risk in risks.values() if risk == 'medium')
        
        if high_risks > 0:
            risks['overall_risk'] = 'high'
        elif medium_risks > 1:
            risks['overall_risk'] = 'medium'
        
        return risks
    
    def _get_router_contract(self, router_address: str):
        """Get router contract instance"""
        return self.w3.eth.contract(
            address=self.w3.to_checksum_address(router_address),
            abi=ROUTER_ABI
        )

    async def get_current_prices(self, token_pair: tuple) -> tuple:
        """Get current prices from Uniswap V2 and Sushiswap for a token pair"""
        try:
            token_a, token_b = token_pair
            amount_in = Web3.to_wei(1, 'ether')  # Price check with 1 ETH
            path = [self.w3.to_checksum_address(addr) for addr in [token_a, token_b]]

            # --- Uniswap ---
            uni_router_address = self.routers['uniswap']
            uni_router = self.w3.eth.contract(
                address=self.w3.to_checksum_address(uni_router_address),
                abi=UNISWAP_ROUTER_ABI
            )
            uni_amounts = uni_router.functions.getAmountsOut(amount_in, path).call()
            uni_decimals = 6 if token_b.lower() in [TOKENS["USDC"].lower(), TOKENS["USDT"].lower()] else 18
            uni_price = uni_amounts[1] / (10 ** uni_decimals)

            # --- Sushiswap ---
            sushi_router_address = self.routers['sushiswap']
            sushi_router = self.w3.eth.contract(
                address=self.w3.to_checksum_address(sushi_router_address),
                abi=UNISWAP_ROUTER_ABI  # Sushi uses the same ABI
            )
            sushi_amounts = sushi_router.functions.getAmountsOut(amount_in, path).call()
            sushi_decimals = 6 if token_b.lower() in [TOKENS["USDC"].lower(), TOKENS["USDT"].lower()] else 18
            sushi_price = sushi_amounts[1] / (10 ** sushi_decimals)

            token_a_symbol = "WETH"
            token_b_symbol = "USDC" if token_b.lower() == TOKENS["USDC"].lower() else "USDT"

            print(f"Uniswap Price: 1 {token_a_symbol} = {uni_price:.2f} {token_b_symbol}")
            print(f"Sushiswap Price: 1 {token_a_symbol} = {sushi_price:.2f} {token_b_symbol}")

            return float(uni_price), float(sushi_price)

        except Exception as e:
            print(f"Error in get_current_prices: {str(e)}")
            return 0.0, 0.0

    
    async def monitor_opportunities(self, token_pairs: List[tuple]) -> List[ArbitrageOpportunity]:
        """Monitor for arbitrage opportunities"""
        opportunities = []
        
        for token_a, token_b in token_pairs:
            # Get current prices
            uni_price, sushi_price = await self.get_current_prices((token_a, token_b))
            
            # Calculate potential profit (simplified for testing)
            price_diff = abs(uni_price - sushi_price)
            if price_diff > 0:
                # Test with 1 ETH
                amount_in = 1000000000000000000  # 1 ETH in wei
                expected_profit = int(price_diff * amount_in / min(uni_price, sushi_price))
                gas_cost = self._estimate_gas_cost()
                
                if expected_profit > gas_cost:
                    opportunities.append(ArbitrageOpportunity(
                        token_a=token_a,
                        token_b=token_b,
                        amount_in=amount_in,
                        expected_profit=expected_profit,
                        gas_cost=gas_cost,
                        net_profit=expected_profit - gas_cost,
                        router1=self.routers['uniswap'],
                        router2=self.routers['sushiswap'],
                        reverse_order=uni_price > sushi_price,
                        confidence_score=0.9
                    ))
        
        return opportunities
        
        # Get current prices
        token_addresses = []
        for pair in token_pairs:
            token_addresses.extend(pair)
        
        prices = await self.get_token_prices(token_addresses)
        
        # Check each token pair
        for token_a, token_b in token_pairs:
            opportunity = self.calculate_arbitrage_opportunity(
                token_a, token_b, amount_in, prices
            )
            
            if opportunity:
                # Assess risk
                risk_assessment = self.assess_risk(opportunity)
                
                # Only include low-risk opportunities
                if risk_assessment['overall_risk'] in ['low', 'medium']:
                    opportunities.append(opportunity)
        
        return opportunities
    
    def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute arbitrage using the smart contract"""
        try:
            # This would interact with the deployed ArbExecutor contract
            # Implementation would depend on your specific setup
            
            print(f"Executing arbitrage:")
            print(f"  Token A: {opportunity.token_a}")
            print(f"  Token B: {opportunity.token_b}")
            print(f"  Amount: {opportunity.amount_in}")
            print(f"  Expected Profit: {opportunity.expected_profit}")
            print(f"  Net Profit: {opportunity.net_profit}")
            print(f"  Confidence: {opportunity.confidence_score:.2f}")
            
            # Here you would call the smart contract
            # contract.functions.executeArbitrage(...).transact()
            
            return True
            
        except Exception as e:
            print(f"Error executing arbitrage: {e}")
            return False

# Example usage
async def main():
    monitor = ArbitrageMonitor(
        rpc_url="https://eth-sepolia.g.alchemy.com/v2/0qBZbUmSupk6zy4Ig9GN5",
        contract_address="0x96888C4B6e569c74fDbDcc40cacf1127421F993c",  # Your deployed contract address
        private_key="0xce0bbf67acfb2d7038b39cdaed5dc84ef0b48a5e1ba268fa339ac2d1c47a45f8"  # Your private key
    )
    
    # Define token pairs to monitor
    token_pairs = [
        ("0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14", "0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8"),  # WETH-USDC
        ("0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14", "0x7169D38820dfd117C3FA1f22a697dBA58d90BA06"),  # WETH-USDT
    ]
    
    while True:
        opportunities = await monitor.monitor_opportunities(token_pairs)
        
        for opportunity in opportunities:
            print(f"Found opportunity: {opportunity.token_a} -> {opportunity.token_b}")
            print(f"Expected profit: {opportunity.expected_profit / 1e18:.6f} ETH")
            
            # Execute if profitable enough
            if opportunity.net_profit > 0.001 * 1e18:  # 0.001 ETH minimum
                success = monitor.execute_arbitrage(opportunity)
                if success:
                    print("Arbitrage executed successfully!")
        
        # Wait before next check
        await asyncio.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    asyncio.run(main())
