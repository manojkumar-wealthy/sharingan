"""
API Response Models for Market Pulse endpoints.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.models.domain import (
    MarketOutlook,
    ThemeGroup,
    NewsWithImpact,
    MarketSummaryBullet,
    WatchlistAlert,
    IndexData,
    NewsItem,
)
from app.models.agent_schemas import OrchestrationMetrics


class MarketPulseResponse(BaseModel):
    """
    Response model for the Market Pulse API endpoint.
    
    Contains the complete market pulse analysis including:
    - Market phase and outlook
    - Summary bullets (pre/post market only)
    - Trending news (mid-market only)
    - Themed news groups
    - Portfolio and watchlist impacts
    """

    # Metadata
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the response was generated",
    )
    request_id: Optional[str] = Field(
        None, description="Unique request identifier for tracing"
    )

    # Market Status
    market_phase: Literal["pre", "mid", "post"] = Field(
        ..., description="Current market phase"
    )
    market_outlook: Optional[MarketOutlook] = Field(
        None,
        description="Market outlook (None during mid-market)",
    )
    indices_data: Dict[str, IndexData] = Field(
        default_factory=dict,
        description="Current data for requested indices",
    )

    # Summary Section
    market_summary: Optional[List[MarketSummaryBullet]] = Field(
        None,
        description="Market summary bullets (None during mid-market)",
        max_length=5,
    )
    executive_summary: Optional[str] = Field(
        None, description="Brief executive summary"
    )

    # Mid-Market Section
    trending_now: Optional[List[NewsItem]] = Field(
        None,
        description="Trending news (only during mid-market)",
    )

    # News & Themes
    themed_news: List[ThemeGroup] = Field(
        default_factory=list,
        description="News grouped by themes with impact analysis",
    )
    all_news: List[NewsWithImpact] = Field(
        default_factory=list,
        description="All news items with impact analysis",
    )

    # User-Specific Analysis
    watchlist_impacted: List[str] = Field(
        default_factory=list,
        description="Watchlist stocks with potential impact",
    )
    watchlist_alerts: List[WatchlistAlert] = Field(
        default_factory=list,
        description="Detailed alerts for watchlist stocks",
    )
    portfolio_impact_summary: Optional[str] = Field(
        None, description="Summary of portfolio impact"
    )
    portfolio_sentiment: Optional[Literal["positive", "negative", "neutral", "mixed"]] = Field(
        None, description="Overall portfolio sentiment"
    )

    # Metadata & Diagnostics
    metrics: Optional[OrchestrationMetrics] = Field(
        None, description="Orchestration metrics (for debugging)"
    )
    degraded_mode: bool = Field(
        default=False,
        description="Whether response is in degraded mode due to agent failures",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Any warnings during processing",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "generated_at": "2026-01-30T10:30:00Z",
                "request_id": "req_abc123",
                "market_phase": "pre",
                "market_outlook": {
                    "sentiment": "bullish",
                    "confidence": 0.85,
                    "reasoning": "NIFTY 50 showing positive momentum",
                    "nifty_change_percent": 0.75,
                    "key_drivers": ["IT sector gains", "Global cues positive"],
                },
                "market_summary": [
                    {
                        "text": "Markets set to open higher driven by positive global cues after US markets closed at record highs.",
                        "supporting_news_ids": ["news_001", "news_002"],
                        "confidence": 0.9,
                        "sentiment": "bullish",
                    }
                ],
                "themed_news": [],
                "all_news": [],
                "watchlist_impacted": ["TCS", "INFY"],
                "portfolio_impact_summary": "Your portfolio is likely to see moderate positive movement.",
                "degraded_mode": False,
            }
        }


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Overall health status"
    )
    service: str = Field(
        default="market-pulse-multi-agent",
        description="Service name",
    )
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp",
    )
    agents: Dict[str, Literal["operational", "degraded", "down"]] = Field(
        default_factory=dict,
        description="Status of each agent",
    )
    dependencies: Optional[Dict[str, bool]] = Field(
        None,
        description="Status of external dependencies (for deep check)",
    )


class AgentStatusResponse(BaseModel):
    """Response model for agent status endpoint."""

    agents: List[Dict] = Field(
        ..., description="List of agent status information"
    )
    total_agents: int = Field(..., description="Total number of agents")
    operational_agents: int = Field(..., description="Number of operational agents")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    request_id: Optional[str] = Field(
        None, description="Request ID for tracing"
    )
    details: Optional[Dict] = Field(
        None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "OrchestrationError",
                "message": "Failed to generate market pulse",
                "request_id": "req_abc123",
                "details": {"failed_agents": ["news_analysis_agent"]},
                "timestamp": "2026-01-30T10:30:00Z",
            }
        }
