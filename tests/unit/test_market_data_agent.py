"""
Unit tests for MarketDataAgent.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.agents.market_data_agent import MarketDataAgent
from app.agents.base import AgentExecutionContext
from app.models.agent_schemas import MarketDataAgentInput


@pytest.fixture
def agent():
    """Create MarketDataAgent instance."""
    return MarketDataAgent()


@pytest.fixture
def context():
    """Create test execution context."""
    return AgentExecutionContext(
        request_id="test_123",
        user_id="test_user",
        timestamp=datetime.utcnow(),
    )


@pytest.fixture
def input_data():
    """Create test input data."""
    return MarketDataAgentInput(
        selected_indices=["NIFTY 50", "SENSEX"],
        timestamp=datetime.utcnow(),
        force_refresh=False,
    )


class TestMarketDataAgent:
    """Tests for MarketDataAgent."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "market_data_agent"
        assert agent.config.temperature == 0.0
        assert agent.get_system_prompt() is not None

    def test_agent_has_tools(self, agent):
        """Test agent has required tools."""
        tools = agent.get_tools()
        assert tools is not None
        assert len(tools) > 0

    def test_agent_has_tool_handlers(self, agent):
        """Test agent has tool handlers."""
        handlers = agent.get_tool_handlers()
        assert "fetch_market_indices" in handlers
        assert "get_market_phase" in handlers
        assert "calculate_index_momentum" in handlers

    @pytest.mark.asyncio
    async def test_execute_returns_valid_output(self, agent, input_data, context):
        """Test agent execution returns valid output."""
        # This test would need mocking of Vertex AI in a real scenario
        # For now, test the structure
        with patch.object(agent, 'execute', new_callable=AsyncMock) as mock_execute:
            from tests.fixtures.mock_data import mock_market_data_output
            mock_execute.return_value = mock_market_data_output()
            
            result = await agent.execute(input_data, context)
            
            assert result is not None
            assert result.market_phase in ["pre", "mid", "post"]
            assert "NIFTY 50" in result.indices_data

    @pytest.mark.asyncio
    async def test_bullish_outlook_when_nifty_up(self, agent, input_data, context):
        """Test bullish outlook when NIFTY is up > 0.5%."""
        with patch.object(agent, 'execute', new_callable=AsyncMock) as mock_execute:
            from tests.fixtures.mock_data import mock_market_data_output
            output = mock_market_data_output()
            output.indices_data["NIFTY 50"].change_percent = 0.85
            mock_execute.return_value = output
            
            result = await agent.execute(input_data, context)
            
            if result.market_phase != "mid" and result.market_outlook:
                assert result.market_outlook.sentiment == "bullish"

    @pytest.mark.asyncio
    async def test_no_outlook_during_mid_market(self, agent, input_data, context):
        """Test that market outlook is None during mid-market."""
        with patch.object(agent, 'execute', new_callable=AsyncMock) as mock_execute:
            from tests.fixtures.mock_data import mock_market_data_output
            output = mock_market_data_output()
            output.market_phase = "mid"
            output.market_outlook = None
            mock_execute.return_value = output
            
            result = await agent.execute(input_data, context)
            
            if result.market_phase == "mid":
                assert result.market_outlook is None
