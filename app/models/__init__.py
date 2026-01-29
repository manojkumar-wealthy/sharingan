"""
Pydantic models for Market Pulse Multi-Agent API.

This module contains all data models organized as:
- domain.py: Core domain models shared across the system
- agent_schemas.py: Input/output schemas for each agent
- requests.py: API request models
- responses.py: API response models
"""

from app.models.domain import (
    IndexData,
    MarketOutlook,
    NewsItem,
    PortfolioHolding,
    ThemeGroup,
    ImpactedStock,
    WatchlistAlert,
)
from app.models.agent_schemas import (
    MarketDataAgentInput,
    MarketDataAgentOutput,
    NewsAnalysisAgentInput,
    NewsAnalysisAgentOutput,
    UserContextAgentInput,
    UserContextAgentOutput,
    ImpactAnalysisAgentInput,
    ImpactAnalysisAgentOutput,
    SummaryGenerationAgentInput,
    SummaryGenerationAgentOutput,
)
from app.models.requests import MarketPulseRequest
from app.models.responses import MarketPulseResponse

__all__ = [
    # Domain models
    "IndexData",
    "MarketOutlook",
    "NewsItem",
    "PortfolioHolding",
    "ThemeGroup",
    "ImpactedStock",
    "WatchlistAlert",
    # Agent schemas
    "MarketDataAgentInput",
    "MarketDataAgentOutput",
    "NewsAnalysisAgentInput",
    "NewsAnalysisAgentOutput",
    "UserContextAgentInput",
    "UserContextAgentOutput",
    "ImpactAnalysisAgentInput",
    "ImpactAnalysisAgentOutput",
    "SummaryGenerationAgentInput",
    "SummaryGenerationAgentOutput",
    # Request/Response
    "MarketPulseRequest",
    "MarketPulseResponse",
]
