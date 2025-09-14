// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "forge-std/console.sol";
import "../src/ArbExecutor.sol";

/**
 * @title RunArb
 * @dev Script to trigger arbitrage function
 * @notice This script executes arbitrage opportunities using the deployed ArbExecutor contract
 */
contract RunArb is Script {
    // Contract address (newly deployed contract)
    address constant ARB_EXECUTOR_ADDRESS = 0x96888C4B6e569c74fDbDcc40cacf1127421F993c;
    
    // Token addresses on Sepolia
    address constant WETH_SEPOLIA = 0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14;
    address constant USDC_SEPOLIA = 0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8;
    address constant USDT_SEPOLIA = 0x7169D38820dfd117C3FA1f22a697dBA58d90BA06;
    
    // Router addresses on Sepolia
    address constant UNISWAP_V2_ROUTER_SEPOLIA = 0xC532A74256D3db4d4444457e8D5c9C7B6e1c3c6A;
    address constant SUSHISWAP_ROUTER_SEPOLIA = 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);
        
        ArbExecutor arbExecutor = ArbExecutor(ARB_EXECUTOR_ADDRESS);
        
        console.log("Running arbitrage bot...");
        console.log("Contract address:", address(arbExecutor));
        
        // Example arbitrage execution
        _executeArbitrageExample(arbExecutor);
        
        vm.stopBroadcast();
    }
    
    /**
     * @dev Execute an example arbitrage between WETH and USDC
     * @param arbExecutor The ArbExecutor contract instance
     */
    function _executeArbitrageExample(ArbExecutor arbExecutor) internal {
        console.log("\n=== Starting Arbitrage Testing ===");
        
        // 1. First check if tokens are authorized
        console.log("\nChecking token authorizations...");
        bool isWethAuthorized = arbExecutor.authorizedTokens(WETH_SEPOLIA);
        bool isUsdcAuthorized = arbExecutor.authorizedTokens(USDC_SEPOLIA);
        console.log("WETH authorized:", isWethAuthorized);
        console.log("USDC authorized:", isUsdcAuthorized);
        
        // 2. Check router authorizations
        console.log("\nChecking router authorizations...");
        bool isUniswapAuthorized = arbExecutor.authorizedRouters(UNISWAP_V2_ROUTER_SEPOLIA);
        bool isSushiswapAuthorized = arbExecutor.authorizedRouters(SUSHISWAP_ROUTER_SEPOLIA);
        console.log("Uniswap authorized:", isUniswapAuthorized);
        console.log("Sushiswap authorized:", isSushiswapAuthorized);
        
        // 3. Check token balances
        console.log("\nChecking token balances...");
        uint256 wethBalance = arbExecutor.getTokenBalance(WETH_SEPOLIA);
        uint256 usdcBalance = arbExecutor.getTokenBalance(USDC_SEPOLIA);
        console.log("WETH balance:", wethBalance);
        console.log("USDC balance:", usdcBalance);
        
        // 4. Check arbitrage opportunities with different amounts
        console.log("\nChecking arbitrage opportunities...");
        uint256[] memory testAmounts = new uint256[](3);
        testAmounts[0] = 0.01 ether;  // 0.01 WETH
        testAmounts[1] = 0.1 ether;   // 0.1 WETH
        testAmounts[2] = 1 ether;     // 1 WETH
        
        for (uint i = 0; i < testAmounts.length; i++) {
            console.log("\nTesting with amount:", testAmounts[i] / 1e18, "WETH");
            uint256 profit = arbExecutor.checkArbitrageOpportunity(
            WETH_SEPOLIA,
            USDC_SEPOLIA,
            amountIn,
            UNISWAP_V2_ROUTER_SEPOLIA,
            SUSHISWAP_ROUTER_SEPOLIA,
            true // reverse order on second router
        );
        
        console.log("Checking arbitrage opportunity...");
        console.log("Amount in: 0.01 WETH");
        console.log("Expected profit:", profit, "wei");
        
        if (profit > 0) {
            console.log("Profitable arbitrage found! Executing...");
            
            try arbExecutor.executeArbitrage(
                WETH_SEPOLIA,
                USDC_SEPOLIA,
                amountIn,
                UNISWAP_V2_ROUTER_SEPOLIA,
                SUSHISWAP_ROUTER_SEPOLIA,
                true
            ) {
                console.log("Arbitrage executed successfully!");
                
                // Check new balance
                uint256 newBalance = arbExecutor.getTokenBalance(WETH_SEPOLIA);
                console.log("New WETH balance:", newBalance, "wei");
                
            } catch Error(string memory reason) {
                console.log("Arbitrage failed:", reason);
            } catch {
                console.log("Arbitrage failed: Unknown error");
            }
        } else {
            console.log("No profitable arbitrage opportunity found.");
        }
    }  // Close _executeArbitrageExample function
    
    /**
     * @dev Check multiple arbitrage opportunities
     * @param arbExecutor The ArbExecutor contract instance
     */
    function _checkMultipleOpportunities(ArbExecutor arbExecutor) internal view {
        console.log("\n=== Checking Multiple Arbitrage Opportunities ===");
        
        uint256 amountIn = 0.01 ether;
        
        // WETH -> USDC -> WETH
        uint256 profit1 = arbExecutor.checkArbitrageOpportunity(
            WETH_SEPOLIA,
            USDC_SEPOLIA,
            amountIn,
            UNISWAP_V2_ROUTER_SEPOLIA,
            SUSHISWAP_ROUTER_SEPOLIA,
            true
        );
        
        // USDC -> WETH -> USDC
        uint256 profit2 = arbExecutor.checkArbitrageOpportunity(
            USDC_SEPOLIA,
            WETH_SEPOLIA,
            amountIn,
            UNISWAP_V2_ROUTER_SEPOLIA,
            SUSHISWAP_ROUTER_SEPOLIA,
            true
        );
        
        // WETH -> USDT -> WETH
        uint256 profit3 = arbExecutor.checkArbitrageOpportunity(
            WETH_SEPOLIA,
            USDT_SEPOLIA,
            amountIn,
            UNISWAP_V2_ROUTER_SEPOLIA,
            SUSHISWAP_ROUTER_SEPOLIA,
            true
        );
        
        console.log("WETH->USDC->WETH profit:", profit1, "wei");
        console.log("USDC->WETH->USDC profit:", profit2, "wei");
        console.log("WETH->USDT->WETH profit:", profit3, "wei");
        
        // Find the most profitable opportunity
        uint256 maxProfit = 0;
        string memory bestPair = "";
        
        if (profit1 > maxProfit) {
            maxProfit = profit1;
            bestPair = "WETH->USDC->WETH";
        }
        if (profit2 > maxProfit) {
            maxProfit = profit2;
            bestPair = "USDC->WETH->USDC";
        }
        if (profit3 > maxProfit) {
            maxProfit = profit3;
            bestPair = "WETH->USDT->WETH";
        }
        
        if (maxProfit > 0) {
            console.log("Best opportunity:", bestPair);
            console.log("Expected profit:", maxProfit, "wei");
        } else {
            console.log("No profitable opportunities found.");
        }
    }
    
    /**
     * @dev Deposit tokens for arbitrage
     * @param arbExecutor The ArbExecutor contract instance
     * @param token Token address to deposit
     * @param amount Amount to deposit
     */
    function depositTokens(ArbExecutor arbExecutor, address token, uint256 amount) external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("Depositing tokens...");
        console.log("Token:", token);
        console.log("Amount:", amount);
        
        arbExecutor.depositToken(token, amount);
        
        uint256 newBalance = arbExecutor.getTokenBalance(token);
        console.log("New balance:", newBalance);
        
        vm.stopBroadcast();
    }
    
    /**
     * @dev Withdraw profits
     * @param arbExecutor The ArbExecutor contract instance
     * @param token Token address to withdraw
     * @param amount Amount to withdraw
     */
    function withdrawProfits(ArbExecutor arbExecutor, address token, uint256 amount) external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("Withdrawing profits...");
        console.log("Token:", token);
        console.log("Amount:", amount);
        
        arbExecutor.withdrawProfit(token, amount);
        
        uint256 newBalance = arbExecutor.getTokenBalance(token);
        console.log("Remaining balance:", newBalance);
        
        vm.stopBroadcast();
    }
}
