"""
Services for the Market Pulse application.

Services:
1. CacheService - Redis-based caching
2. MarketIntelligenceService - Unified market data and news fetching
"""

from app.services.cache_service import CacheService
from app.services.market_intelligence_service import (
    fetch_market_intelligence,
    fetch_market_indices,
    get_market_phase,
    fetch_market_news,
    fetch_stock_specific_news,
    cluster_news_by_topic,
    get_market_intelligence_tools,
    get_market_intelligence_tool_handlers,
)

__all__ = [
    "CacheService",
    # Market Intelligence Service
    "fetch_market_intelligence",
    "fetch_market_indices",
    "get_market_phase",
    "fetch_market_news",
    "fetch_stock_specific_news",
    "cluster_news_by_topic",
    "get_market_intelligence_tools",
    "get_market_intelligence_tool_handlers",
]
