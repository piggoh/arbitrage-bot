#!/usr/bin/env python3
"""
Test script to monitor real-time DEX prices
"""
import asyncio
from arbitrage_monitor import ArbitrageMonitor
from config import TOKENS, RPC_URL, CONTRACT_ADDRESS, PRIVATE_KEY

async def monitor_prices():
    print("🔍 Starting Price Monitor Test")
    print("=" * 50)
    
    # Initialize monitor
    monitor = ArbitrageMonitor(
        rpc_url=RPC_URL,
        contract_address=CONTRACT_ADDRESS,
        private_key=PRIVATE_KEY
    )
    
    # Token pairs to monitor
    token_pairs = [
        (TOKENS["WETH"], TOKENS["USDC"]),
        (TOKENS["WETH"], TOKENS["USDT"])
    ]
    
    print("\n📊 Starting price monitoring...")
    try:
        # Monitor for 5 rounds
        for i in range(5):
            print(f"\nRound {i+1}/5:")
            print("-" * 30)
            
            for pair in token_pairs:
                token_a_symbol = "WETH" if pair[0] == TOKENS["WETH"] else "USDC"
                token_b_symbol = "USDC" if pair[1] == TOKENS["USDC"] else "USDT"
                print(f"\nChecking {token_a_symbol}/{token_b_symbol} pair:")
                
                # Get prices
                uni_price, sushi_price = await monitor.get_current_prices(pair)
                
                # If we got valid prices
                if uni_price > 0 and sushi_price > 0:
                    # Calculate price difference
                    price_diff = abs(uni_price - sushi_price)
                    price_diff_percent = (price_diff / min(uni_price, sushi_price)) * 100
                    
                    print(f"Price difference: {price_diff_percent:.2f}%")
                    if price_diff_percent > 1.0:  # More than 1% difference
                        print("⚠️ Significant price difference detected!")
            
            # Wait before next round
            if i < 4:  # Don't wait after last round
                print("\nWaiting 30 seconds...")
                await asyncio.sleep(30)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print("\n✅ Price monitoring test complete")

if __name__ == "__main__":
    asyncio.run(monitor_prices())