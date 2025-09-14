# Arbitrage Bot

A sophisticated smart contract-based arbitrage bot built with Solidity and Foundry, designed to identify and execute profitable arbitrage opportunities across different decentralized exchanges (DEXs).

## 🚀 Features

- **Multi-DEX Arbitrage**: Execute arbitrage between Uniswap V2, SushiSwap, and other compatible DEXs
- **Token Authorization**: Secure token and router authorization system
- **Slippage Protection**: Configurable maximum slippage tolerance
- **Profit Optimization**: Minimum profit threshold to avoid unprofitable trades
- **Emergency Functions**: Emergency withdrawal capabilities
- **Comprehensive Testing**: Full test suite with fuzz testing
- **Gas Optimization**: Optimized for efficient gas usage

## 📁 Project Structure

```
arbitrage-bot/
├── src/
│   └── ArbExecutor.sol          # Main smart contract for arbitrage execution
├── script/
│   ├── Deploy.s.sol             # Deployment script for Sepolia
│   └── RunArb.s.sol             # Script to trigger arbitrage function
├── test/
│   └── ArbExecutor.t.sol        # Unit tests for contract logic
├── foundry.toml                 # Foundry configuration file
├── .env                         # Private keys & RPC URLs (not committed)
└── README.md                    # This documentation
```

## 🛠️ Prerequisites

- [Foundry](https://book.getfoundry.sh/getting-started/installation)
- Node.js (for additional tooling)
- Ethereum wallet with testnet ETH (for Sepolia testing)

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd arbitrage-bot
   ```

2. **Install Foundry dependencies**
   ```bash
   forge install OpenZeppelin/openzeppelin-contracts
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

4. **Compile the contracts**
   ```bash
   forge build
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Private key for deployment and execution (without 0x prefix)
PRIVATE_KEY=your_private_key_here

# Infura API key for RPC endpoints
INFURA_API_KEY=your_infura_api_key_here

# Etherscan API key for contract verification
ETHERSCAN_API_KEY=your_etherscan_api_key_here

# Network RPC URLs
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/${INFURA_API_KEY}
MAINNET_RPC_URL=https://mainnet.infura.io/v3/${INFURA_API_KEY}
```

### Contract Configuration

The contract supports the following configurable parameters:

- **Minimum Profit Threshold**: Minimum profit required to execute arbitrage
- **Maximum Slippage**: Maximum acceptable slippage (in basis points)
- **Authorized Tokens**: List of tokens approved for arbitrage
- **Authorized Routers**: List of DEX routers approved for trading

## 🚀 Deployment

### Deploy to Sepolia Testnet

1. **Deploy the contract**
   ```bash
   forge script script/Deploy.s.sol --rpc-url sepolia --broadcast --verify
   ```

2. **Update contract address**
   After deployment, update the `ARB_EXECUTOR_ADDRESS` in `script/RunArb.s.sol`

3. **Verify deployment**
   ```bash
   forge verify-contract <CONTRACT_ADDRESS> src/ArbExecutor.sol:ArbExecutor --chain sepolia
   ```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
forge test

# Run tests with verbose output
forge test -vvv

# Run specific test
forge test --match-test testExecuteArbitrage

# Run fuzz tests
forge test --match-test testFuzz
```

### Test Coverage

```bash
# Generate coverage report
forge coverage

# Generate HTML coverage report
forge coverage --report html
```

## 📊 Usage

### Basic Arbitrage Execution

1. **Deposit tokens**
   ```bash
   forge script script/RunArb.s.sol:RunArb --sig "depositTokens(address,address,uint256)" <CONTRACT_ADDRESS> <TOKEN_ADDRESS> <AMOUNT> --rpc-url sepolia --broadcast
   ```

2. **Check arbitrage opportunities**
   ```bash
   forge script script/RunArb.s.sol:RunArb --sig "checkMultipleOpportunities(address)" <CONTRACT_ADDRESS> --rpc-url sepolia
   ```

3. **Execute arbitrage**
   ```bash
   forge script script/RunArb.s.sol:RunArb --rpc-url sepolia --broadcast
   ```

4. **Withdraw profits**
   ```bash
   forge script script/RunArb.s.sol:RunArb --sig "withdrawProfits(address,address,uint256)" <CONTRACT_ADDRESS> <TOKEN_ADDRESS> <AMOUNT> --rpc-url sepolia --broadcast
   ```

### Contract Functions

#### Core Functions

- `executeArbitrage()`: Execute arbitrage between two routers
- `checkArbitrageOpportunity()`: Check if arbitrage is profitable
- `depositToken()`: Deposit tokens for arbitrage
- `withdrawProfit()`: Withdraw profits
- `emergencyWithdraw()`: Emergency withdrawal of all tokens

#### Management Functions

- `authorizeToken()`: Authorize a token for arbitrage
- `revokeToken()`: Revoke token authorization
- `authorizeRouter()`: Authorize a router for trading
- `revokeRouter()`: Revoke router authorization
- `setMinProfitThreshold()`: Set minimum profit threshold
- `setMaxSlippage()`: Set maximum slippage tolerance

## 🔒 Security Features

- **Reentrancy Protection**: Uses OpenZeppelin's ReentrancyGuard
- **Access Control**: Owner-only functions for critical operations
- **Token Authorization**: Only authorized tokens can be used
- **Router Authorization**: Only authorized routers can be used
- **Slippage Protection**: Maximum slippage limits prevent excessive losses
- **Balance Checks**: Ensures sufficient balance before execution

## 📈 Arbitrage Strategy

The bot implements a two-step arbitrage strategy:

1. **Step 1**: Swap Token A → Token B on Router 1
2. **Step 2**: Swap Token B → Token A on Router 2 (or vice versa)

The bot calculates expected profits before execution and only proceeds if the profit exceeds the minimum threshold.

## 🌐 Supported Networks

- **Sepolia Testnet**: For testing and development
- **Ethereum Mainnet**: For production use (with proper configuration)

## 📝 Common Token Addresses

### Sepolia Testnet
- WETH: `0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14`
- USDC: `0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8`
- USDT: `0x7169D38820dfd117C3FA1f22a697dBA58d90BA06`

### Common Router Addresses
- Uniswap V2 Router: `0xC532a74256D3Db4D4444457E8D5c9C7b6e1c3C6a`
- SushiSwap Router: `0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506`

## ⚠️ Important Notes

1. **Test First**: Always test on Sepolia before deploying to mainnet
2. **Gas Costs**: Consider gas costs when setting minimum profit thresholds
3. **Market Conditions**: Arbitrage opportunities are market-dependent
4. **MEV Protection**: Consider MEV protection strategies for production
5. **Liquidity**: Ensure sufficient liquidity exists on target DEXs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the test cases for usage examples

## 🔮 Future Enhancements

- [ ] Multi-hop arbitrage support
- [ ] Flash loan integration
- [ ] MEV protection mechanisms
- [ ] Automated opportunity detection
- [ ] Cross-chain arbitrage support
- [ ] Advanced slippage protection
- [ ] Gas optimization improvements

---

**Disclaimer**: This software is for educational purposes. Use at your own risk. Always test thoroughly before using with real funds.
