// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

interface IUniswapV2Router {
    function getAmountsOut(uint amountIn, address[] calldata path)
        external view returns (uint[] memory amounts);
    
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);
}

interface IUniswapV2Factory {
    function getPair(address tokenA, address tokenB) external view returns (address pair);
}

/**
 * @title ArbExecutor
 * @dev Main smart contract for arbitrage execution
 * @notice This contract executes arbitrage opportunities between different DEXs
 */
contract ArbExecutor is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;

    // Events
    event ArbitrageExecuted(
        address indexed tokenA,
        address indexed tokenB,
        uint256 amountIn,
        uint256 profit,
        uint256 timestamp
    );
    
    event ProfitWithdrawn(address indexed token, uint256 amount);
    event EmergencyWithdraw(address indexed token, uint256 amount);

    // State variables
    mapping(address => bool) public authorizedTokens;
    mapping(address => bool) public authorizedRouters;
    mapping(address => uint256) public tokenBalances;
    
    uint256 public minProfitThreshold = 0.01 ether; // Minimum profit threshold
    uint256 public maxSlippage = 500; // 5% max slippage (in basis points)
    
    // Constants
    uint256 private constant BASIS_POINTS = 10000;
    uint256 private constant DEADLINE_BUFFER = 300; // 5 minutes

    constructor() Ownable(msg.sender) {
        // Initialize with common tokens and routers
        // These should be set by the owner after deployment
    }

    /**
     * @dev Authorize a token for arbitrage
     * @param token Address of the token to authorize
     */
    function authorizeToken(address token) external onlyOwner {
        authorizedTokens[token] = true;
    }

    /**
     * @dev Revoke authorization for a token
     * @param token Address of the token to revoke
     */
    function revokeToken(address token) external onlyOwner {
        authorizedTokens[token] = false;
    }

    /**
     * @dev Authorize a router for arbitrage
     * @param router Address of the router to authorize
     */
    function authorizeRouter(address router) external onlyOwner {
        authorizedRouters[router] = true;
    }

    /**
     * @dev Revoke authorization for a router
     * @param router Address of the router to revoke
     */
    function revokeRouter(address router) external onlyOwner {
        authorizedRouters[router] = false;
    }

    /**
     * @dev Set minimum profit threshold
     * @param threshold New minimum profit threshold in wei
     */
    function setMinProfitThreshold(uint256 threshold) external onlyOwner {
        minProfitThreshold = threshold;
    }

    /**
     * @dev Set maximum slippage tolerance
     * @param slippage New maximum slippage in basis points
     */
    function setMaxSlippage(uint256 slippage) external onlyOwner {
        require(slippage <= 1000, "Slippage too high"); // Max 10%
        maxSlippage = slippage;
    }

    /**
     * @dev Execute arbitrage between two routers
     * @param tokenA Address of token A
     * @param tokenB Address of token B
     * @param amountIn Amount of token A to swap
     * @param router1 First router address
     * @param router2 Second router address
     * @param reverseOrder Whether to reverse the swap order on router2
     */
    function executeArbitrage(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        address router1,
        address router2,
        bool reverseOrder
    ) external nonReentrant onlyOwner {
        require(authorizedTokens[tokenA], "Token A not authorized");
        require(authorizedTokens[tokenB], "Token B not authorized");
        require(authorizedRouters[router1], "Router1 not authorized");
        require(authorizedRouters[router2], "Router2 not authorized");
        require(amountIn > 0, "Amount must be greater than 0");

        IERC20 token = IERC20(tokenA);
        require(token.balanceOf(address(this)) >= amountIn, "Insufficient balance");

        // Calculate expected output from router1
        uint256 expectedOutput1 = _getExpectedOutput(router1, tokenA, tokenB, amountIn);
        require(expectedOutput1 > 0, "No liquidity on router1");

        // Calculate expected output from router2
        uint256 expectedOutput2 = _getExpectedOutput(
            router2, 
            reverseOrder ? tokenB : tokenA, 
            reverseOrder ? tokenA : tokenB, 
            reverseOrder ? expectedOutput1 : amountIn
        );
        require(expectedOutput2 > 0, "No liquidity on router2");

        // Check if arbitrage is profitable
        uint256 profit = expectedOutput2 > amountIn ? expectedOutput2 - amountIn : 0;
        require(profit >= minProfitThreshold, "Profit below threshold");

        // Execute the arbitrage
        uint256 actualProfit = _executeArbitrageSwap(
            tokenA,
            tokenB,
            amountIn,
            router1,
            router2,
            reverseOrder
        );

        require(actualProfit > 0, "Arbitrage failed");

        // Update token balance
        tokenBalances[tokenA] = token.balanceOf(address(this));

        emit ArbitrageExecuted(tokenA, tokenB, amountIn, actualProfit, block.timestamp);
    }

    /**
     * @dev Internal function to execute the arbitrage swap
     */
    function _executeArbitrageSwap(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        address router1,
        address router2,
        bool reverseOrder
    ) internal returns (uint256 profit) {
        IERC20 token = IERC20(tokenA);
        uint256 initialBalance = token.balanceOf(address(this));

        // First swap on router1
        uint256 amountOut1 = _performSwap(router1, tokenA, tokenB, amountIn);
        
        // Second swap on router2
        uint256 amountOut2;
        if (reverseOrder) {
            amountOut2 = _performSwap(router2, tokenB, tokenA, amountOut1);
        } else {
            amountOut2 = _performSwap(router2, tokenA, tokenB, amountIn);
        }

        uint256 finalBalance = token.balanceOf(address(this));
        profit = finalBalance > initialBalance ? finalBalance - initialBalance : 0;
    }

    /**
     * @dev Internal function to perform a swap
     */
    function _performSwap(
        address router,
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) internal returns (uint256 amountOut) {
        IERC20 token = IERC20(tokenIn);
        IUniswapV2Router routerContract = IUniswapV2Router(router);

        // Approve router to spend tokens
        token.forceApprove(router, amountIn);

        // Create path
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;

        // Calculate minimum amount out with slippage protection
        uint256[] memory amounts = routerContract.getAmountsOut(amountIn, path);
        uint256 minAmountOut = amounts[1] * (BASIS_POINTS - maxSlippage) / BASIS_POINTS;

        // Execute swap
        uint256[] memory swapAmounts = routerContract.swapExactTokensForTokens(
            amountIn,
            minAmountOut,
            path,
            address(this),
            block.timestamp + DEADLINE_BUFFER
        );

        amountOut = swapAmounts[1];
    }

    /**
     * @dev Get expected output from a router
     */
    function _getExpectedOutput(
        address router,
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) internal view returns (uint256) {
        try IUniswapV2Router(router).getAmountsOut(amountIn, _createPath(tokenIn, tokenOut)) 
        returns (uint256[] memory amounts) {
            return amounts[1];
        } catch {
            return 0;
        }
    }

    /**
     * @dev Create swap path
     */
    function _createPath(address tokenIn, address tokenOut) internal pure returns (address[] memory path) {
        path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;
    }

    /**
     * @dev Withdraw profits in a specific token
     * @param token Address of the token to withdraw
     * @param amount Amount to withdraw
     */
    function withdrawProfit(address token, uint256 amount) external onlyOwner {
        require(authorizedTokens[token], "Token not authorized");
        require(amount > 0, "Amount must be greater than 0");
        
        IERC20 tokenContract = IERC20(token);
        require(tokenContract.balanceOf(address(this)) >= amount, "Insufficient balance");

        tokenContract.safeTransfer(owner(), amount);
        tokenBalances[token] = tokenContract.balanceOf(address(this));

        emit ProfitWithdrawn(token, amount);
    }

    /**
     * @dev Emergency withdraw all tokens
     * @param token Address of the token to withdraw
     */
    function emergencyWithdraw(address token) external onlyOwner {
        IERC20 tokenContract = IERC20(token);
        uint256 balance = tokenContract.balanceOf(address(this));
        
        if (balance > 0) {
            tokenContract.safeTransfer(owner(), balance);
            tokenBalances[token] = 0;
            emit EmergencyWithdraw(token, balance);
        }
    }

    /**
     * @dev Deposit tokens for arbitrage
     * @param token Address of the token to deposit
     * @param amount Amount to deposit
     */
    function depositToken(address token, uint256 amount) external {
        require(authorizedTokens[token], "Token not authorized");
        require(amount > 0, "Amount must be greater than 0");

        IERC20 tokenContract = IERC20(token);
        tokenContract.safeTransferFrom(msg.sender, address(this), amount);
        tokenBalances[token] = tokenContract.balanceOf(address(this));
    }

    /**
     * @dev Get token balance
     * @param token Address of the token
     * @return Current balance of the token
     */
    function getTokenBalance(address token) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }

    /**
     * @dev Check if arbitrage opportunity exists
     * @param tokenA Address of token A
     * @param tokenB Address of token B
     * @param amountIn Amount to check
     * @param router1 First router
     * @param router2 Second router
     * @param reverseOrder Whether to reverse order on router2
     * @return profit Expected profit from arbitrage
     */
    function checkArbitrageOpportunity(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        address router1,
        address router2,
        bool reverseOrder
    ) external view returns (uint256 profit) {
        require(authorizedTokens[tokenA], "Token A not authorized");
        require(authorizedTokens[tokenB], "Token B not authorized");
        require(authorizedRouters[router1], "Router1 not authorized");
        require(authorizedRouters[router2], "Router2 not authorized");

        uint256 expectedOutput1 = _getExpectedOutput(router1, tokenA, tokenB, amountIn);
        if (expectedOutput1 == 0) return 0;

        uint256 expectedOutput2 = _getExpectedOutput(
            router2, 
            reverseOrder ? tokenB : tokenA, 
            reverseOrder ? tokenA : tokenB, 
            reverseOrder ? expectedOutput1 : amountIn
        );
        if (expectedOutput2 == 0) return 0;

        profit = expectedOutput2 > amountIn ? expectedOutput2 - amountIn : 0;
    }
}
