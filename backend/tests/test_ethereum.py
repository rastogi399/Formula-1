"""
Test Suite for Ethereum Service and NexusTrading Contract
Tests blockchain interactions, swaps, and portfolio tracking
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from app.services.ethereum_service import EthereumService
from app.agents.trading_agent import TradingAgent
from app.core.config import settings


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def ethereum_service():
    """Create Ethereum service instance for testing"""
    return EthereumService(rpc_url=settings.ETHEREUM_RPC_URL)


@pytest.fixture
def trading_agent():
    """Create trading agent instance for testing"""
    return TradingAgent()


@pytest.fixture
def mock_eth_account():
    """Mock Ethereum test account"""
    return {
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f42bE",
        "private_key": "0x" + "0" * 64,  # Placeholder
    }


# ============================================
# Ethereum Service Tests
# ============================================

class TestEthereumService:
    """Test suite for EthereumService"""
    
    def test_initialization(self, ethereum_service):
        """Test service initializes with correct RPC endpoint"""
        assert ethereum_service is not None
        assert ethereum_service.w3 is not None
        assert ethereum_service.chain_id == 80001  # Mumbai
        assert ethereum_service.explorer_url == "https://mumbai.polygonscan.com"
    
    def test_token_address_resolution(self, ethereum_service):
        """Test token symbol to address resolution"""
        # Test known tokens
        weth_addr = ethereum_service._resolve_token_address("WETH")
        assert weth_addr == "0x9c3C9283D3e44854697Cd22EDB54CB57F23A5A13"
        
        usdc_addr = ethereum_service._resolve_token_address("USDC")
        assert usdc_addr == "0x0FA8781a83E46826621b3BC094Ea2A0212e71B23"
        
        usdt_addr = ethereum_service._resolve_token_address("USDT")
        assert usdt_addr == "0xA02f6aDB06d98B855f8e0285c053EDA4cD51C89b"
    
    def test_token_address_direct_input(self, ethereum_service):
        """Test handling of direct token addresses"""
        address = "0x9c3C9283D3e44854697Cd22EDB54CB57F23A5A13"
        resolved = ethereum_service._resolve_token_address(address)
        
        # Should return checksummed version
        assert resolved.lower() == address.lower()
    
    def test_invalid_token(self, ethereum_service):
        """Test error handling for invalid tokens"""
        with pytest.raises(ValueError, match="Unknown token"):
            ethereum_service._resolve_token_address("INVALID_TOKEN")
    
    @pytest.mark.asyncio
    async def test_simulate_swap(self, ethereum_service):
        """Test swap simulation without execution"""
        result = await ethereum_service.simulate_swap(
            token_in="WETH",
            token_out="USDC",
            amount=Decimal("1.0")
        )
        
        assert result is not None
        assert "token_in" in result
        assert "token_out" in result
        assert "expected_amount_out" in result
        assert "estimated_gas" in result
        assert float(result["expected_amount_out"]) < 1.0  # Some slippage
    
    @pytest.mark.asyncio
    async def test_get_balance(self, ethereum_service, mock_eth_account):
        """Test balance retrieval"""
        result = await ethereum_service.get_balance(
            token="USDC",
            user_address=mock_eth_account["address"]
        )
        
        assert result is not None
        assert "token" in result
        assert "user" in result
        assert "balance" in result or "balance_wei" in result
    
    @pytest.mark.asyncio
    async def test_get_portfolio(self, ethereum_service, mock_eth_account):
        """Test portfolio retrieval for user"""
        result = await ethereum_service.get_portfolio(
            user_address=mock_eth_account["address"]
        )
        
        assert result is not None
        assert "user" in result
        assert "tokens" in result
        assert "total_value_usd" in result
        assert "chain" in result
        assert result["chain"] == "polygon-mumbai"
    
    def test_explorer_urls(self, ethereum_service):
        """Test blockchain explorer URL generation"""
        tx_url = ethereum_service.get_explorer_url(
            tx_hash="0x123456"
        )
        assert "mumbai.polygonscan.com" in tx_url
        assert "tx" in tx_url
        
        addr_url = ethereum_service.get_explorer_url(
            address="0x742d35Cc6634C0532925a3b844Bc9e7595f42bE"
        )
        assert "mumbai.polygonscan.com" in addr_url
        assert "address" in addr_url


# ============================================
# Trading Agent Tests
# ============================================

class TestTradingAgent:
    """Test suite for TradingAgent with blockchain selector"""
    
    def test_initialization(self, trading_agent):
        """Test trading agent initializes correctly"""
        assert trading_agent is not None
        assert trading_agent.active_chain.value == "ethereum"
        assert trading_agent.ethereum_service is not None
    
    def test_get_active_service(self, trading_agent):
        """Test service selection based on active chain"""
        service = trading_agent.get_active_service()
        assert service is not None
        assert isinstance(service, EthereumService)
    
    @pytest.mark.asyncio
    async def test_execute_swap(self, trading_agent, mock_eth_account):
        """Test swap execution through trading agent"""
        result = await trading_agent.execute_swap(
            token_in="WETH",
            token_out="USDC",
            amount=1.0,
            user_address=mock_eth_account["address"],
            min_amount_out=0.0
        )
        
        assert result is not None
        assert "status" in result
        assert "tx_hash" in result
        assert "token_in" in result
        assert "token_out" in result
        assert "user" in result
    
    @pytest.mark.asyncio
    async def test_simulate_swap_through_agent(self, trading_agent):
        """Test swap simulation through trading agent"""
        result = await trading_agent.simulate_swap(
            token_in="USDC",
            token_out="USDT",
            amount=100.0
        )
        
        assert result is not None
        assert "expected_amount_out" in result
        assert "estimated_gas" in result
    
    @pytest.mark.asyncio
    async def test_get_balance_through_agent(self, trading_agent, mock_eth_account):
        """Test balance retrieval through trading agent"""
        result = await trading_agent.get_balance(
            token="USDC",
            user_address=mock_eth_account["address"]
        )
        
        assert result is not None
        assert "balance" in result
    
    @pytest.mark.asyncio
    async def test_get_portfolio_through_agent(self, trading_agent, mock_eth_account):
        """Test portfolio retrieval through trading agent"""
        result = await trading_agent.get_portfolio(
            user_address=mock_eth_account["address"]
        )
        
        assert result is not None
        assert "tokens" in result
        assert "total_value_usd" in result
    
    def test_get_active_chain_info(self, trading_agent):
        """Test active chain information retrieval"""
        info = trading_agent.get_active_chain_info()
        
        assert info["chain"] == "ethereum"
        assert info["network"] == "polygon-mumbai"
        assert info["chain_id"] == 80001
        assert "rpc_url" in info
        assert "explorer" in info
    
    def test_swap_history(self, trading_agent):
        """Test swap history tracking"""
        tx_hash = "0x123456789abcdef"
        swap_data = {
            "tx_hash": tx_hash,
            "status": "success",
            "amount_out": "100.50"
        }
        
        # Manually add to history
        trading_agent.swap_history[tx_hash] = swap_data
        
        # Retrieve from history
        retrieved = trading_agent.get_swap_status(tx_hash)
        assert retrieved == swap_data
    
    @pytest.mark.asyncio
    async def test_estimate_transaction_cost(self, trading_agent):
        """Test transaction cost estimation"""
        costs = await trading_agent.estimate_transaction_cost(
            token_in="WETH",
            token_out="USDC",
            amount=1.0
        )
        
        assert costs is not None
        assert "estimated_gas" in costs or "estimated_fee_sol" in costs
        assert "estimated_fee_usd" in costs
        assert "chain" in costs


# ============================================
# Integration Tests
# ============================================

class TestIntegration:
    """Integration tests for full swap workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_swap_workflow(self, trading_agent, mock_eth_account):
        """Test complete swap workflow from simulation to execution"""
        user = mock_eth_account["address"]
        
        # Step 1: Simulate swap
        simulation = await trading_agent.simulate_swap(
            token_in="WETH",
            token_out="USDC",
            amount=0.1
        )
        assert simulation is not None
        expected_out = float(simulation["expected_amount_out"])
        
        # Step 2: Execute swap
        execution = await trading_agent.execute_swap(
            token_in="WETH",
            token_out="USDC",
            amount=0.1,
            user_address=user,
            min_amount_out=expected_out * 0.98  # 2% slippage
        )
        assert execution is not None
        assert execution["status"] in ["success", "pending"]
        
        # Step 3: Get updated portfolio
        portfolio = await trading_agent.get_portfolio(user)
        assert portfolio is not None
        assert "tokens" in portfolio
    
    @pytest.mark.asyncio
    async def test_multi_token_portfolio(self, ethereum_service, mock_eth_account):
        """Test portfolio with multiple tokens"""
        user = mock_eth_account["address"]
        
        # Get balance for each token
        weth = await ethereum_service.get_balance("WETH", user)
        usdc = await ethereum_service.get_balance("USDC", user)
        usdt = await ethereum_service.get_balance("USDT", user)
        
        # All should return valid data
        assert weth is not None
        assert usdc is not None
        assert usdt is not None


# ============================================
# Contract Deployment Tests
# ============================================

class TestContractDeployment:
    """Tests for NexusTrading contract deployment and interaction"""
    
    @pytest.mark.asyncio
    async def test_contract_address_configuration(self):
        """Test contract address is properly configured"""
        # Contract address should be set after deployment
        # For testing, we use None (not deployed yet)
        if settings.ETHEREUM_CONTRACT_ADDRESS:
            assert settings.ETHEREUM_CONTRACT_ADDRESS.startswith("0x")
            assert len(settings.ETHEREUM_CONTRACT_ADDRESS) == 42
    
    def test_token_configuration(self):
        """Test token addresses are properly configured"""
        assert settings.ETHEREUM_WETH.startswith("0x")
        assert settings.ETHEREUM_USDC.startswith("0x")
        assert settings.ETHEREUM_USDT.startswith("0x")
        
        # All should be unique
        tokens = {settings.ETHEREUM_WETH, settings.ETHEREUM_USDC, settings.ETHEREUM_USDT}
        assert len(tokens) == 3
    
    def test_network_configuration(self):
        """Test Ethereum network is correctly configured for Mumbai"""
        assert settings.ETHEREUM_CHAIN_ID == 80001
        assert "mumbai" in settings.ETHEREUM_RPC_URL.lower()
        assert "mumbai" in settings.ETHEREUM_EXPLORER.lower()


# ============================================
# Error Handling Tests
# ============================================

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_zero_amount_swap(self, ethereum_service):
        """Test swap with zero amount raises error"""
        with pytest.raises(ValueError):
            await ethereum_service.simulate_swap(
                token_in="WETH",
                token_out="USDC",
                amount=Decimal("0")
            )
    
    @pytest.mark.asyncio
    async def test_invalid_token_swap(self, ethereum_service):
        """Test swap with invalid token raises error"""
        with pytest.raises((ValueError, KeyError)):
            await ethereum_service.simulate_swap(
                token_in="INVALID",
                token_out="USDC",
                amount=Decimal("1")
            )
    
    @pytest.mark.asyncio
    async def test_invalid_address(self, ethereum_service):
        """Test operations with invalid address"""
        with pytest.raises(Exception):  # Web3 validation error
            await ethereum_service.get_balance(
                token="USDC",
                user_address="invalid_address"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
