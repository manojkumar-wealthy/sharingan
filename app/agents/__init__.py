"""
Simplified Multi-Agent System for Market Pulse Generation.

This package contains 3 specialized agents:
1. MarketIntelligenceAgent - Combined market data and news analysis
2. PortfolioInsightAgent - Combined user context and impact analysis
3. SummaryGenerationAgent - Market summary generation

The OrchestratorAgent coordinates these agents in a 3-phase execution flow.
"""

from app.agents.base import BaseAgent, AgentConfig, AgentExecutionContext
from app.agents.market_intelligence_agent import MarketIntelligenceAgent
from app.agents.portfolio_insight_agent import PortfolioInsightAgent
from app.agents.summary_generation_agent import SummaryGenerationAgent
from app.agents.orchestrator import OrchestratorAgent

__all__ = [
    # Base
    "BaseAgent",
    "AgentConfig",
    "AgentExecutionContext",
    # Simplified Agents (3 agents)
    "MarketIntelligenceAgent",
    "PortfolioInsightAgent",
    "SummaryGenerationAgent",
    # Orchestrator
    "OrchestratorAgent",
]
