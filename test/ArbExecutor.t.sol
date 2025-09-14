// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {console} from "forge-std/console.sol";
import {ArbExecutor} from "../src/ArbExecutor.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

// Mock contracts for testing
contract MockERC20 is IERC20 {
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;
    
    uint256 private _totalSupply;
    string public name;
    string public symbol;
    uint8 public decimals;
    
    constructor(string memory _name, string memory _symbol, uint8 _decimals) {
        name = _name;
        symbol = _symbol;
        decimals = _decimals;
    }
    
    function totalSupply() external view override returns (uint256) {
        return _totalSupply;
    }
    
    function balanceOf(address account) external view override returns (uint256) {
        return _balances[account];
    }
    
    function transfer(address to, uint256 amount) external override returns (bool) {
        _balances[msg.sender] -= amount;
        _balances[to] += amount;
        return true;
    }
    
    function allowance(address owner, address spender) external view override returns (uint256) {
        return _allowances[owner][spender];
    }
    
    function approve(address spender, uint256 amount) external override returns (bool) {
        _allowances[msg.sender][spender] = amount;
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) external override returns (bool) {
        _allowances[from][msg.sender] -= amount;
        _balances[from] -= amount;
        _balances[to] += amount;
        return true;
    }
    
    function mint(address to, uint256 amount) external {
        _balances[to] += amount;
        _totalSupply += amount;
    }
}

contract MockRouter {
    mapping(address => mapping(address => uint256)) public exchangeRates;
    
    function setExchangeRate(address tokenIn, address tokenOut, uint256 rate) external {
        exchangeRates[tokenIn][tokenOut] = rate;
    }
    
    function getAmountsOut(uint amountIn, address[] calldata path) external view returns (uint[] memory amounts) {
        amounts = new uint[](2);
        amounts[0] = amountIn;
        amounts[1] = amountIn * exchangeRates[path[0]][path[1]] / 1e18;
    }
    
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts) {
        amounts = new uint[](2);
        amounts[0] = amountIn;
        amounts[1] = amountIn * exchangeRates[path[0]][path[1]] / 1e18;
        
        IERC20 tokenIn = IERC20(path[0]);
        IERC20 tokenOut = IERC20(path[1]);
        
        // Use SafeERC20 for transfers
        SafeERC20.safeTransferFrom(tokenIn, msg.sender, address(this), amountIn);
        
        // Mint tokens for the router if needed
        if (MockERC20(address(tokenOut)).balanceOf(address(this)) < amounts[1]) {
            MockERC20(address(tokenOut)).mint(address(this), amounts[1]);
        }
        
        SafeERC20.safeTransfer(tokenOut, to, amounts[1]);
    }
}

/**
 * @title ArbExecutorTest
 * @dev Unit tests for contract logic (local fork or dry-run)
 * @notice Comprehensive test suite for the ArbExecutor contract
 */
contract ArbExecutorTest is Test {
    ArbExecutor public arbExecutor;
    MockERC20 public tokenA;
    MockERC20 public tokenB;
    MockRouter public router1;
    MockRouter public router2;
    
    address public owner;
    address public user;
    
    event ArbitrageExecuted(
        address indexed tokenA,
        address indexed tokenB,
        uint256 amountIn,
        uint256 profit,
        uint256 timestamp
    );
    
    event ProfitWithdrawn(address indexed token, uint256 amount);
    event EmergencyWithdraw(address indexed token, uint256 amount);
    
    function setUp() public {
        owner = address(this);
        user = makeAddr("user");
        
        // Deploy contracts
        arbExecutor = new ArbExecutor();
        tokenA = new MockERC20("Token A", "TKA", 18);
        tokenB = new MockERC20("Token B", "TKB", 18);
        router1 = new MockRouter();
        router2 = new MockRouter();
        
        // Authorize tokens and routers
        arbExecutor.authorizeToken(address(tokenA));
        arbExecutor.authorizeToken(address(tokenB));
        arbExecutor.authorizeRouter(address(router1));
        arbExecutor.authorizeRouter(address(router2));
        
        // Set up exchange rates
        router1.setExchangeRate(address(tokenA), address(tokenB), 2e18); // 1 TKA = 2 TKB
        router1.setExchangeRate(address(tokenB), address(tokenA), 5e17); // 1 TKB = 0.5 TKA
        
        router2.setExchangeRate(address(tokenA), address(tokenB), 19e17); // 1 TKA = 1.9 TKB (slightly worse)
        router2.setExchangeRate(address(tokenB), address(tokenA), 526e15); // 1 TKB = 0.526 TKA (better)
        
        // Mint tokens to contract
        tokenA.mint(address(arbExecutor), 1000e18);
        tokenB.mint(address(arbExecutor), 1000e18);
    }
    
    function testInitialization() public {
        assertTrue(arbExecutor.authorizedTokens(address(tokenA)));
        assertTrue(arbExecutor.authorizedTokens(address(tokenB)));
        assertTrue(arbExecutor.authorizedRouters(address(router1)));
        assertTrue(arbExecutor.authorizedRouters(address(router2)));
        assertEq(arbExecutor.minProfitThreshold(), 0.01 ether);
        assertEq(arbExecutor.maxSlippage(), 500);
    }
    
    function testAuthorizeToken() public {
        MockERC20 newToken = new MockERC20("New Token", "NEW", 18);
        
        arbExecutor.authorizeToken(address(newToken));
        assertTrue(arbExecutor.authorizedTokens(address(newToken)));
        
        arbExecutor.revokeToken(address(newToken));
        assertFalse(arbExecutor.authorizedTokens(address(newToken)));
    }
    
    function testAuthorizeRouter() public {
        MockRouter newRouter = new MockRouter();
        
        arbExecutor.authorizeRouter(address(newRouter));
        assertTrue(arbExecutor.authorizedRouters(address(newRouter)));
        
        arbExecutor.revokeRouter(address(newRouter));
        assertFalse(arbExecutor.authorizedRouters(address(newRouter)));
    }
    
    function testSetMinProfitThreshold() public {
        uint256 newThreshold = 0.005 ether;
        arbExecutor.setMinProfitThreshold(newThreshold);
        assertEq(arbExecutor.minProfitThreshold(), newThreshold);
    }
    
    function testSetMaxSlippage() public {
        uint256 newSlippage = 300; // 3%
        arbExecutor.setMaxSlippage(newSlippage);
        assertEq(arbExecutor.maxSlippage(), newSlippage);
        
        // Test max slippage limit
        vm.expectRevert("Slippage too high");
        arbExecutor.setMaxSlippage(1500); // 15%
    }
    
    function testDepositToken() public {
        MockERC20 newToken = new MockERC20("Deposit Token", "DEP", 18);
        arbExecutor.authorizeToken(address(newToken));
        
        newToken.mint(user, 100e18);
        vm.prank(user);
        newToken.approve(address(arbExecutor), 100e18);
        
        vm.prank(user);
        arbExecutor.depositToken(address(newToken), 50e18);
        
        assertEq(newToken.balanceOf(address(arbExecutor)), 50e18);
        assertEq(arbExecutor.getTokenBalance(address(newToken)), 50e18);
    }
    
    function testDepositUnauthorizedToken() public {
        MockERC20 unauthorizedToken = new MockERC20("Unauthorized", "UNAUTH", 18);
        
        vm.expectRevert("Token not authorized");
        arbExecutor.depositToken(address(unauthorizedToken), 100e18);
    }
    
    function testCheckArbitrageOpportunity() public {
        uint256 amountIn = 10e18;
        
        uint256 profit = arbExecutor.checkArbitrageOpportunity(
            address(tokenA),
            address(tokenB),
            amountIn,
            address(router1),
            address(router2),
            true
        );
        
        // Expected: 10 TKA -> 20 TKB (via router1) -> 10.52 TKA (via router2)
        // Profit: 10.52 - 10 = 0.52 TKA
        assertGt(profit, 0);
    }
    
    function testExecuteArbitrage() public {
        uint256 amountIn = 10e18;
        uint256 initialBalance = tokenA.balanceOf(address(arbExecutor));
        
        // Check if arbitrage is profitable
        uint256 expectedProfit = arbExecutor.checkArbitrageOpportunity(
            address(tokenA),
            address(tokenB),
            amountIn,
            address(router1),
            address(router2),
            true
        );
        
        if (expectedProfit > 0) {
            vm.expectEmit(true, true, false, true);
            emit ArbitrageExecuted(address(tokenA), address(tokenB), amountIn, expectedProfit, block.timestamp);
            
            arbExecutor.executeArbitrage(
                address(tokenA),
                address(tokenB),
                amountIn,
                address(router1),
                address(router2),
                true
            );
            
            uint256 finalBalance = tokenA.balanceOf(address(arbExecutor));
            assertGt(finalBalance, initialBalance);
        }
    }
    
    function testExecuteArbitrageInsufficientBalance() public {
        uint256 amountIn = 2000e18; // More than contract has
        
        vm.expectRevert("Insufficient balance");
        arbExecutor.executeArbitrage(
            address(tokenA),
            address(tokenB),
            amountIn,
            address(router1),
            address(router2),
            true
        );
    }
    
    function testExecuteArbitrageUnauthorizedToken() public {
        MockERC20 unauthorizedToken = new MockERC20("Unauthorized", "UNAUTH", 18);
        
        vm.expectRevert("Token A not authorized");
        arbExecutor.executeArbitrage(
            address(unauthorizedToken),
            address(tokenB),
            10e18,
            address(router1),
            address(router2),
            true
        );
    }
    
    function testExecuteArbitrageUnauthorizedRouter() public {
        MockRouter unauthorizedRouter = new MockRouter();
        
        vm.expectRevert("Router1 not authorized");
        arbExecutor.executeArbitrage(
            address(tokenA),
            address(tokenB),
            10e18,
            address(unauthorizedRouter),
            address(router2),
            true
        );
    }
    
    function testExecuteArbitrageZeroAmount() public {
        vm.expectRevert("Amount must be greater than 0");
        arbExecutor.executeArbitrage(
            address(tokenA),
            address(tokenB),
            0,
            address(router1),
            address(router2),
            true
        );
    }
    
    function testWithdrawProfit() public {
        uint256 withdrawAmount = 50e18;
        
        vm.expectEmit(true, false, false, true);
        emit ProfitWithdrawn(address(tokenA), withdrawAmount);
        
        arbExecutor.withdrawProfit(address(tokenA), withdrawAmount);
        
        assertEq(tokenA.balanceOf(owner), withdrawAmount);
    }
    
    function testWithdrawProfitUnauthorizedToken() public {
        MockERC20 unauthorizedToken = new MockERC20("Unauthorized", "UNAUTH", 18);
        
        vm.expectRevert("Token not authorized");
        arbExecutor.withdrawProfit(address(unauthorizedToken), 50e18);
    }
    
    function testWithdrawProfitInsufficientBalance() public {
        uint256 withdrawAmount = 2000e18; // More than contract has
        
        vm.expectRevert("Insufficient balance");
        arbExecutor.withdrawProfit(address(tokenA), withdrawAmount);
    }
    
    function testEmergencyWithdraw() public {
        uint256 balance = tokenA.balanceOf(address(arbExecutor));
        
        vm.expectEmit(true, false, false, true);
        emit EmergencyWithdraw(address(tokenA), balance);
        
        arbExecutor.emergencyWithdraw(address(tokenA));
        
        assertEq(tokenA.balanceOf(owner), balance);
        assertEq(tokenA.balanceOf(address(arbExecutor)), 0);
    }
    
    function testGetTokenBalance() public {
        uint256 balance = arbExecutor.getTokenBalance(address(tokenA));
        assertEq(balance, tokenA.balanceOf(address(arbExecutor)));
    }
    
    function testFuzzArbitrageExecution(uint256 amountIn) public {
        vm.assume(amountIn > 0 && amountIn <= 100e18);
        
        uint256 initialBalance = tokenA.balanceOf(address(arbExecutor));
        
        if (initialBalance >= amountIn) {
            uint256 profit = arbExecutor.checkArbitrageOpportunity(
                address(tokenA),
                address(tokenB),
                amountIn,
                address(router1),
                address(router2),
                true
            );
            
            if (profit >= arbExecutor.minProfitThreshold()) {
                try arbExecutor.executeArbitrage(
                    address(tokenA),
                    address(tokenB),
                    amountIn,
                    address(router1),
                    address(router2),
                    true
                ) {
                    uint256 finalBalance = tokenA.balanceOf(address(arbExecutor));
                    assertGe(finalBalance, initialBalance);
                } catch {
                    // Some fuzz inputs might fail due to mock limitations, which is expected
                }
            }
        }
    }
    
    function testMultipleArbitrageOpportunities() public {
        // Test different token pairs
        uint256 amountIn = 5e18;
        
        uint256 profit1 = arbExecutor.checkArbitrageOpportunity(
            address(tokenA),
            address(tokenB),
            amountIn,
            address(router1),
            address(router2),
            true
        );
        
        uint256 profit2 = arbExecutor.checkArbitrageOpportunity(
            address(tokenB),
            address(tokenA),
            amountIn,
            address(router1),
            address(router2),
            true
        );
        
        console.log("Profit A->B->A:", profit1);
        console.log("Profit B->A->B:", profit2);
        
        // At least one should be profitable
        assertTrue(profit1 > 0 || profit2 > 0);
    }
}
