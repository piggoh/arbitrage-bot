# Arbitrage Bot Architecture and Flow

## Overview
This arbitrage bot continuously monitors price differences between Uniswap and Sushiswap, executing trades when profitable opportunities are found.

## Core Components

### 1. Price Monitoring (`arbitrage_monitor.py`)
- Monitors real-time prices from DEXs
- Calculates potential profits
- Considers gas costs and slippage
- Stores price data for analysis

### 2. Smart Contract Interface (`smart_contract_interaction.py`)
- Handles blockchain interactions
- Executes trades through smart contract
- Manages transaction signing
- Monitors transaction status

### 3. Main Bot Logic (`integrated_arbitrage_bot.py`)
- Coordinates monitoring and execution
- Validates opportunities
- Manages trade execution
- Tracks performance

### 4. Configuration (`config.py`)
- Network settings
- Token addresses
- Risk parameters
- Performance thresholds

## Detailed Flow

1. **Price Monitoring Phase**
   ```
   Monitor DEX Prices
   ↓
   Calculate Price Differences
   ↓
   Log Price Data
   ```

2. **Opportunity Detection**
   ```
   Check Price Discrepancies
   ↓
   Calculate Potential Profit
   ↓
   Consider Gas Costs
   ↓
   Filter by Minimum Profit
   ```

3. **Validation Phase**
   ```
   Double-check Prices On-chain
   ↓
   Verify Liquidity
   ↓
   Calculate Gas Costs
   ↓
   Confirm Profitability
   ```

4. **Execution Phase**
   ```
   Check Balance
   ↓
   Execute Trade
   ↓
   Monitor Transaction
   ↓
   Log Results
   ```

## Data Logging

The bot maintains detailed logs of:
- Real-time price data
- Identified opportunities
- Executed trades
- Performance metrics
- Error events

## Key Files Generated
- `logs/price_data_YYYYMMDD.csv`: Price monitoring data
- `logs/trade_data_YYYYMMDD.csv`: Executed trade details
- `logs/bot_TIMESTAMP.log`: General bot operation logs

## Smart Contract Interaction
The bot interacts with the deployed smart contract through:
1. Price checks using `checkArbitrageOpportunity()`
2. Trade execution using `executeArbitrage()`
3. Balance monitoring using `getTokenBalance()`

## Performance Tracking
Tracks and logs:
- Number of opportunities found
- Success/fail ratio
- Total profit/loss
- Gas costs
- Response times