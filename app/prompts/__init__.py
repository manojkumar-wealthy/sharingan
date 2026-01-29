"""
System prompts for the simplified multi-agent system.

Prompts for:
1. MarketIntelligenceAgent - Market data and news analysis
2. PortfolioInsightAgent - User context and impact analysis
3. SummaryGenerationAgent - Summary generation
"""

from app.prompts.market_intelligence_prompts import MARKET_INTELLIGENCE_SYSTEM_PROMPT
from app.prompts.portfolio_insight_prompts import PORTFOLIO_INSIGHT_SYSTEM_PROMPT
from app.prompts.summary_generation_prompts import SUMMARY_GENERATION_SYSTEM_PROMPT

__all__ = [
    "MARKET_INTELLIGENCE_SYSTEM_PROMPT",
    "PORTFOLIO_INSIGHT_SYSTEM_PROMPT",
    "SUMMARY_GENERATION_SYSTEM_PROMPT",
]
