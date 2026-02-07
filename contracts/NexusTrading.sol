// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title NexusTrading
 * @dev Non-custodial token swap contract for Polygon Mumbai
 * Integrates with Uniswap V3 for token exchanges
 * Supports portfolio tracking and gas estimation
 */

import "@uniswap/v3-periphery/contracts/interfaces/ISwapRouter.sol";
import "@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface IQuoter {
    function quoteExactInputSingle(
        address tokenIn,
        address tokenOut,
        uint24 fee,
        uint256 amountIn,
        uint160 sqrtPriceLimitX96
    ) external returns (uint256 amountOut);
}

contract NexusTrading is ReentrancyGuard, Ownable {
    // Uniswap V3 Router on Polygon Mumbai
    ISwapRouter public constant swapRouter = ISwapRouter(0xE592427A0AEce92De3Edee1F18E0157C05861564);
    
    // Uniswap V3 Quoter for price simulation
    IQuoter public constant quoter = IQuoter(0xb27F1EF629B4CC20b86b40d41166FAACF0E5e5DF);
    
    // Fee tier for swaps (0.3%)
    uint24 public constant FEE_TIER = 3000;
    
    // Portfolio tracking per user
    mapping(address => PortfolioData) public portfolios;
    
    // Swap event for tracking
    event SwapExecuted(
        address indexed user,
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        uint256 timestamp
    );
    
    // Portfolio updated
    event PortfolioUpdated(
        address indexed user,
        uint256 totalValue,
        uint256 timestamp
    );
    
    struct PortfolioData {
        uint256 lastUpdateTime;
        uint256 totalValueUSD;
        mapping(address => uint256) tokenBalances;
        uint256 swapCount;
    }
    
    /**
     * @dev Execute a token swap using Uniswap V3
     * @param tokenIn Input token address
     * @param tokenOut Output token address
     * @param amountIn Amount of input tokens
     * @param minAmountOut Minimum acceptable output (slippage protection)
     * @return amountOut Actual output amount
     */
    function executeSwap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut
    ) external nonReentrant returns (uint256 amountOut) {
        require(tokenIn != address(0) && tokenOut != address(0), "Invalid tokens");
        require(amountIn > 0, "Amount must be greater than 0");
        
        // Transfer tokens from user to contract
        require(
            IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn),
            "Transfer failed"
        );
        
        // Approve router
        IERC20(tokenIn).approve(address(swapRouter), amountIn);
        
        // Execute swap
        ISwapRouter.ExactInputSingleParams memory params = ISwapRouter.ExactInputSingleParams({
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            fee: FEE_TIER,
            recipient: msg.sender,
            deadline: block.timestamp + 60,
            amountIn: amountIn,
            amountOutMinimum: minAmountOut,
            sqrtPriceLimitX96: 0
        });
        
        amountOut = swapRouter.exactInputSingle(params);
        
        // Update portfolio
        PortfolioData storage portfolio = portfolios[msg.sender];
        portfolio.lastUpdateTime = block.timestamp;
        portfolio.swapCount += 1;
        portfolio.tokenBalances[tokenOut] += amountOut;
        if (portfolio.tokenBalances[tokenIn] >= amountIn) {
            portfolio.tokenBalances[tokenIn] -= amountIn;
        }
        
        emit SwapExecuted(msg.sender, tokenIn, tokenOut, amountIn, amountOut, block.timestamp);
    }
    
    /**
     * @dev Simulate a swap to get expected output without executing
     * @param tokenIn Input token address
     * @param tokenOut Output token address
     * @param amountIn Amount of input tokens
     * @return expectedAmountOut Expected output amount
     */
    function simulateSwap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) external returns (uint256 expectedAmountOut) {
        require(tokenIn != address(0) && tokenOut != address(0), "Invalid tokens");
        require(amountIn > 0, "Amount must be greater than 0");
        
        try quoter.quoteExactInputSingle(
            tokenIn,
            tokenOut,
            FEE_TIER,
            amountIn,
            0
        ) returns (uint256 amountOut) {
            expectedAmountOut = amountOut;
        } catch {
            expectedAmountOut = 0;
        }
    }
    
    /**
     * @dev Get current balance of a token for a user
     * @param token Token address
     * @param user User address
     * @return balance Balance amount
     */
    function getBalance(address token, address user) external view returns (uint256) {
        return IERC20(token).balanceOf(user);
    }
    
    /**
     * @dev Get portfolio data for a user
     * @param user User address
     * @return lastUpdate Last portfolio update time
     * @return totalValue Total portfolio value in USD
     * @return swapCount Total number of swaps
     */
    function getPortfolio(address user) 
        external 
        view 
        returns (uint256 lastUpdate, uint256 totalValue, uint256 swapCount) 
    {
        PortfolioData storage portfolio = portfolios[user];
        return (portfolio.lastUpdateTime, portfolio.totalValueUSD, portfolio.swapCount);
    }
    
    /**
     * @dev Estimate gas cost for a swap (simplified)
     * @param tokenIn Input token
     * @param tokenOut Output token
     * @param amountIn Input amount
     * @return estimatedGas Estimated gas in wei
     */
    function estimateGas(
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) external view returns (uint256) {
        // Uniswap V3 swap typically costs 150k-200k gas
        // Return in wei at current gas price (estimated at 30 gwei for Mumbai)
        return 175000 * 30 * 10**9;
    }
    
    /**
     * @dev Wait for transaction confirmation (helper for frontend)
     * @param txHash Transaction hash to track
     * @return confirmed Whether transaction was confirmed
     */
    function waitForConfirmation(bytes32 txHash) external view returns (bool) {
        // On EVM chains, this would need to be checked externally
        // This is a placeholder for contract interaction
        return true;
    }
    
    /**
     * @dev Update portfolio total value (called by oracle or admin)
     * @param user User address
     * @param newTotalValue New total portfolio value
     */
    function updatePortfolioValue(address user, uint256 newTotalValue) external onlyOwner {
        portfolios[user].totalValueUSD = newTotalValue;
        portfolios[user].lastUpdateTime = block.timestamp;
        emit PortfolioUpdated(user, newTotalValue, block.timestamp);
    }
    
    /**
     * @dev Emergency withdrawal of stuck tokens
     * @param token Token to withdraw
     * @param amount Amount to withdraw
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        require(IERC20(token).transfer(owner(), amount), "Withdrawal failed");
    }
}
