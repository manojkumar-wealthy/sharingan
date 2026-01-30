"""
API Response Models for Market Pulse endpoints.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.constants.themes import MAX_THEMED_NEWS_ITEMS
from app.models.domain import (
    MarketOutlook,
    NewsWithImpact,
    MarketSummaryBullet,
    WatchlistAlert,
    IndexData,
    NewsItem,
    ImpactedStock,
)


# -----------------------------------------------------------------------------
# News API response models (single-layer; exclude url, sentiment_score,
# relevance_score, impact_confidence from serialization)
# -----------------------------------------------------------------------------


class NewsItemResponse(BaseModel):
    """News item for API response; excludes url, sentiment_score, relevance_score."""

    id: str = Field(..., description="Unique identifier for the news item")
    headline: str = Field(..., description="News headline/title")
    summary: str = Field(..., description="Brief summary of the news")
    source: str = Field(..., description="News source")
    published_at: datetime = Field(..., description="Publication timestamp")
    sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        ..., description="Sentiment classification"
    )
    mentioned_stocks: List[str] = Field(
        default_factory=list, description="Stock tickers mentioned in the news"
    )
    mentioned_sectors: List[str] = Field(
        default_factory=list, description="Sectors mentioned in the news"
    )
    is_breaking: bool = Field(default=False, description="Whether this is breaking news")


class NewsWithImpactResponse(BaseModel):
    """
    Single-layer news-with-impact for API response.

    Flattens news_item fields; excludes url, sentiment_score, relevance_score,
    impact_confidence from the response.
    """

    news_id: str = Field(..., description="Reference to original news item")
    headline: str = Field(..., description="News headline/title")
    summary: str = Field(..., description="Brief summary of the news")
    source: str = Field(..., description="News source")
    published_at: datetime = Field(..., description="Publication timestamp")
    sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        ..., description="Sentiment classification"
    )
    mentioned_stocks: List[str] = Field(
        default_factory=list, description="Stock tickers mentioned in the news"
    )
    mentioned_sectors: List[str] = Field(
        default_factory=list, description="Sectors mentioned in the news"
    )
    is_breaking: bool = Field(default=False, description="Whether this is breaking news")
    impacted_stocks: List[ImpactedStock] = Field(
        default_factory=list, description="Stocks impacted by this news"
    )
    sector_impacts: Dict[str, Literal["positive", "negative", "neutral"]] = Field(
        default_factory=dict, description="Impact on each sector"
    )
    causal_chain: str = Field(
        ..., description="Causal chain explaining the impact"
    )


def _news_item_to_response(item: NewsItem) -> NewsItemResponse:
    """Convert domain NewsItem to API response (excludes url, sentiment_score, relevance_score)."""
    return NewsItemResponse(
        id=item.id,
        headline=item.headline,
        summary=item.summary,
        source=item.source,
        published_at=item.published_at,
        sentiment=item.sentiment,
        mentioned_stocks=item.mentioned_stocks,
        mentioned_sectors=item.mentioned_sectors,
        is_breaking=item.is_breaking,
    )


def _news_with_impact_to_response(nwi: NewsWithImpact) -> NewsWithImpactResponse:
    """Convert domain NewsWithImpact to single-layer API response (excludes url, sentiment_score, relevance_score, impact_confidence)."""
    n = nwi.news_item
    return NewsWithImpactResponse(
        news_id=nwi.news_id,
        headline=n.headline,
        summary=n.summary,
        source=n.source,
        published_at=n.published_at,
        sentiment=n.sentiment,
        mentioned_stocks=n.mentioned_stocks,
        mentioned_sectors=n.mentioned_sectors,
        is_breaking=n.is_breaking,
        impacted_stocks=nwi.impacted_stocks,
        sector_impacts=nwi.sector_impacts,
        causal_chain=nwi.causal_chain,
    )


class ThemedNewsItem(BaseModel):
    """
    Single themed news item for API response (pre/post market only).

    Only themes from the canonical allowed list are returned; max 5 items.
    """

    theme_name: str = Field(..., description="Display name of the theme (from allowed list)")
    sentiment: Literal["bullish", "bearish", "neutral", "mixed"] = Field(
        ..., description="Overall sentiment for this theme"
    )
    theme: str = Field(
        ...,
        description="Canonical theme name (same as theme_name; from allowed list)",
    )
    reason: str = Field(
        ...,
        description="Brief explanation of why this theme is impacted (post-market / pre-market)",
    )


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

    # Mid-Market Section (single-layer; excludes url, sentiment_score, relevance_score)
    trending_now: Optional[List[NewsItemResponse]] = Field(
        None,
        description="Trending news (only during mid-market)",
    )

    # News & Themes (pre/post market only; max 5 themes from allowed list)
    themed_news: List[ThemedNewsItem] = Field(
        default_factory=list,
        description="Up to 5 themes impacted in post-market and pre-market (theme_name, sentiment, theme)",
        max_length=MAX_THEMED_NEWS_ITEMS,
    )
    # Single-layer; excludes url, sentiment_score, relevance_score, impact_confidence
    all_news: List[NewsWithImpactResponse] = Field(
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

    # Metadata & Diagnostics (metrics are logged, not returned)
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
                "themed_news": [
                    {
                        "theme_name": "Global Market Cues",
                        "sentiment": "bullish",
                        "theme": "Global Market Cues",
                        "reason": "US and Asian indices closed higher; positive overnight cues for opening.",
                    }
                ],
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
