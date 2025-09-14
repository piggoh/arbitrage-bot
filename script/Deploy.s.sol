// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Script} from "forge-std/Script.sol";
import {console} from "forge-std/console.sol";
import {ArbExecutor} from "../src/ArbExecutor.sol";

/**
 * @title Deploy
 * @dev Deployment script for Sepolia
 * @notice This script deploys the ArbExecutor contract to Sepolia testnet
 */
contract Deploy is Script {
    // Common token addresses on Sepolia
    address constant WETH_SEPOLIA = 0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14;
    address constant USDC_SEPOLIA = 0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8;
    address constant USDT_SEPOLIA = 0x7169D38820dfd117C3FA1f22a697dBA58d90BA06;
    
    // Common router addresses on Sepolia
    address constant UNISWAP_V2_ROUTER_SEPOLIA = 0xC532A74256D3db4d4444457e8D5c9C7B6e1c3c6A;
    address constant SUSHISWAP_ROUTER_SEPOLIA = 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        // Deploy ArbExecutor contract
        ArbExecutor arbExecutor = new ArbExecutor();
        
        console.log("ArbExecutor deployed at:", address(arbExecutor));
        
        // Authorize common tokens
        arbExecutor.authorizeToken(WETH_SEPOLIA);
        arbExecutor.authorizeToken(USDC_SEPOLIA);
        arbExecutor.authorizeToken(USDT_SEPOLIA);
        
        console.log("Authorized tokens:");
        console.log("WETH:", WETH_SEPOLIA);
        console.log("USDC:", USDC_SEPOLIA);
        console.log("USDT:", USDT_SEPOLIA);
        
        // Authorize common routers
        arbExecutor.authorizeRouter(UNISWAP_V2_ROUTER_SEPOLIA);
        arbExecutor.authorizeRouter(SUSHISWAP_ROUTER_SEPOLIA);
        
        console.log("Authorized routers:");
        console.log("Uniswap V2 Router:", UNISWAP_V2_ROUTER_SEPOLIA);
        console.log("SushiSwap Router:", SUSHISWAP_ROUTER_SEPOLIA);
        
        // Set initial parameters
        arbExecutor.setMinProfitThreshold(1000000000000000); // 0.001 ETH minimum profit (1e15 wei)
        arbExecutor.setMaxSlippage(300); // 3% max slippage
        
        console.log("Contract initialized with:");
        console.log("Min profit threshold: 0.001 ETH");
        console.log("Max slippage: 3%");
        
        // Print deployment summary
        console.log("\nDeployment Summary");
        console.log("=================");
        console.log("Contract Address:", address(arbExecutor));
        console.log("Network: Sepolia");
        console.log("Block Number:", block.number);
        console.log("Deployer:", msg.sender);
        
        vm.stopBroadcast();
    }
}
