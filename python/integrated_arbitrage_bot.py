#!/usr/bin/env python3
"""
Integrated Arbitrage Bot - Complete Python + Solidity Integration

Flow:
1. Price Monitoring:
   - Continuously monitors Uniswap and Sushiswap prices
   - Stores price data for analysis
   - Calculates price differences and potential profits

2. Opportunity Detection:
   - Identifies price discrepancies above threshold
   - Calculates gas costs and net profit
   - Filters opportunities by minimum profit

3. Smart Contract Validation:
   - Double-checks prices on-chain
   - Verifies liquidity is available
   - Confirms transaction viability

4. Trade Execution:
   - Executes trades through smart contract
   - Monitors transaction success
   - Records trade outcomes
"""

import asyncio
import time
from typing import List, Optional
from arbitrage_monitor import ArbitrageMonitor, ArbitrageOpportunity
from smart_contract_interaction import SmartContractInterface
from config import TOKENS, ROUTERS, RPC_URL, CONTRACT_ADDRESS, PRIVATE_KEY
from utils.logger import ArbitrageLogger

class IntegratedArbitrageBot:
    """Complete arbitrage bot that combines Python monitoring with Solidity execution"""
    
    def __init__(self):
        # Initialize logging system
        self.logger = ArbitrageLogger()
        self.logger.log_info("Initializing Arbitrage Bot...")

        # Initialize the monitoring system
        self.logger.log_info("Setting up price monitoring system...")
        self.monitor = ArbitrageMonitor(
            rpc_url=RPC_URL,
            contract_address=CONTRACT_ADDRESS,
            private_key=PRIVATE_KEY
        )
        
        # Initialize the smart contract interface
        self.logger.log_info("Setting up smart contract interface...")
        self.contract_interface = SmartContractInterface(
            rpc_url=RPC_URL,
            contract_address=CONTRACT_ADDRESS,
            private_key=PRIVATE_KEY
        )
        
        # Bot configuration
        self.is_running = False
        self.executed_trades = 0
        self.total_profit = 0
        
        # Performance tracking
        self.start_time = time.time()
        self.total_opportunities_found = 0
        self.total_validations_passed = 0
        
        print("🤖 Integrated Arbitrage Bot Initialized")
        print(f"   Contract: {CONTRACT_ADDRESS}")
        print(f"   Account: {self.contract_interface.account.address}")
    
    async def run_arbitrage_cycle(self, token_pairs: List[tuple]) -> List[ArbitrageOpportunity]:
        """Run one complete arbitrage cycle"""
        cycle_start = time.time()
        self.logger.log_info("\n=== Starting New Arbitrage Cycle ===")
        
        # Step 1: Monitor for opportunities using Python
        self.logger.log_info("Checking prices on DEXs...")
        for pair in token_pairs:
            # Get and log prices for each pair
            uni_price, sushi_price = await self.monitor.get_current_prices(pair)
            self.logger.log_prices(
                token_pair=pair,
                uni_price=uni_price,
                sushi_price=sushi_price
            )
            self.logger.log_info(f"Price check: {pair[0]}/{pair[1]}")
            self.logger.log_info(f"  Uniswap: {uni_price:.6f}")
            self.logger.log_info(f"  Sushiswap: {sushi_price:.6f}")
            self.logger.log_info(f"  Difference: {abs(uni_price - sushi_price):.6f} ({abs(uni_price - sushi_price)/min(uni_price, sushi_price)*100:.2f}%)")
        
        # Find opportunities
        opportunities = await self.monitor.monitor_opportunities(token_pairs)
        
        if not opportunities:
            self.logger.log_info("No profitable opportunities found in this cycle")
            return []
        
        self.total_opportunities_found += len(opportunities)
        self.logger.log_info(f"Found {len(opportunities)} potential opportunities")
        
        # Step 2: Validate opportunities using smart contract
        validated_opportunities = []
        for opp in opportunities:
            print(f"\n   Validating opportunity: {opp.token_a[:10]}... -> {opp.token_b[:10]}...")
            
            # Double-check with smart contract
            contract_profit = self.contract_interface.check_arbitrage_opportunity(
                opp.token_a, opp.token_b, opp.amount_in,
                ROUTERS["UNISWAP_V2"], ROUTERS["SUSHISWAP"], opp.reverse_order
            )
            
            print(f"     Python profit: {opp.expected_profit / 1e18:.6f} ETH")
            print(f"     Contract profit: {contract_profit / 1e18:.6f} ETH")
            
            # Validate that both systems agree (within 10% tolerance)
            if abs(opp.expected_profit - contract_profit) / max(opp.expected_profit, contract_profit) < 0.1:
                validated_opportunities.append(opp)
                print(f"     ✅ Validation passed")
            else:
                print(f"     ❌ Validation failed - profit mismatch")
        
        return validated_opportunities
    
    async def execute_opportunity(self, opportunity: ArbitrageOpportunity) -> bool:
        """Execute a validated arbitrage opportunity"""
        self.logger.log_info("\n=== Executing Arbitrage Opportunity ===")
        
        # Log detailed opportunity information
        trade_data = {
            'token_a': opportunity.token_a,
            'token_b': opportunity.token_b,
            'amount_in': opportunity.amount_in / 1e18,
            'expected_profit': opportunity.expected_profit / 1e18,
            'gas_cost': opportunity.gas_cost / 1e18,
            'net_profit': opportunity.net_profit / 1e18,
            'confidence_score': opportunity.confidence_score,
            'execution_time': datetime.now().isoformat()
        }
        
        self.logger.log_info("Trade Details:")
        self.logger.log_info(f"  Pair: {opportunity.token_a[:10]}... -> {opportunity.token_b[:10]}...")
        self.logger.log_info(f"  Amount: {opportunity.amount_in / 1e18:.6f} ETH")
        self.logger.log_info(f"  Expected profit: {opportunity.expected_profit / 1e18:.6f} ETH")
        self.logger.log_info(f"  Gas cost: {opportunity.gas_cost / 1e18:.6f} ETH")
        self.logger.log_info(f"  Net profit: {opportunity.net_profit / 1e18:.6f} ETH")
        
        # Check if we have enough balance
        current_balance = self.contract_interface.get_token_balance(opportunity.token_a)
        if current_balance < opportunity.amount_in:
            print(f"   ❌ Insufficient balance: {current_balance / 1e18:.6f} < {opportunity.amount_in / 1e18:.6f}")
            return False
        
        # Execute arbitrage using smart contract
        success = self.contract_interface.execute_arbitrage(
            opportunity.token_a, opportunity.token_b, opportunity.amount_in,
            ROUTERS["UNISWAP_V2"], ROUTERS["SUSHISWAP"], opportunity.reverse_order
        )
        
        if success:
            self.executed_trades += 1
            self.total_profit += opportunity.net_profit
            print(f"   ✅ Arbitrage executed successfully!")
            print(f"   📊 Total trades: {self.executed_trades}")
            print(f"   💰 Total profit: {self.total_profit / 1e18:.6f} ETH")
        else:
            print(f"   ❌ Arbitrage execution failed")
        
        return success
    
    async def run_bot(self, token_pairs: List[tuple], max_cycles: int = 10):
        """Run the complete arbitrage bot"""
        print("🚀 Starting Integrated Arbitrage Bot")
        print("=" * 50)
        
        self.is_running = True
        cycle_count = 0
        
        try:
            while self.is_running and cycle_count < max_cycles:
                cycle_count += 1
                print(f"\n📊 Cycle {cycle_count}/{max_cycles}")
                
                # Run arbitrage cycle
                opportunities = await self.run_arbitrage_cycle(token_pairs)
                
                # Execute profitable opportunities
                for opportunity in opportunities:
                    if opportunity.net_profit > 1000000000000000:  # > 0.001 ETH
                        await self.execute_opportunity(opportunity)
                        
                        # Small delay between trades
                        await asyncio.sleep(5)
                
                # Wait before next cycle
                print(f"\n⏳ Waiting 30 seconds before next cycle...")
                await asyncio.sleep(30)
                
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            print(f"\n❌ Bot error: {e}")
        finally:
            self.is_running = False
            print(f"\n📈 Bot Summary:")
            print(f"   Total cycles: {cycle_count}")
            print(f"   Total trades: {self.executed_trades}")
            print(f"   Total profit: {self.total_profit / 1e18:.6f} ETH")
    
    def stop_bot(self):
        """Stop the arbitrage bot"""
        self.is_running = False
        print("🛑 Stopping arbitrage bot...")

def main():
    """Main function to run the integrated arbitrage bot"""
    
    # Define token pairs to monitor (Sepolia testnet)
    token_pairs = [
        (TOKENS["WETH"], TOKENS["USDC"]),
        (TOKENS["WETH"], TOKENS["USDT"]),
        (TOKENS["USDC"], TOKENS["USDT"])
    ]
    
    # Initialize the bot
    bot = IntegratedArbitrageBot()
    
    # Run the bot
    asyncio.run(bot.run_bot(token_pairs, max_cycles=5))

if __name__ == "__main__":
    main()
