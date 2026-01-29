"""
Tools for the Market Pulse agents.

Available tools:
1. Analysis tools - Impact analysis, supply chain analysis, fundamentals
2. User data tools - Watchlist, portfolio, preferences
3. Market intelligence tools (via service) - Market data, news, clustering
"""

from app.tools.analysis_tools import (
    identify_sector_from_stocks,
    analyze_supply_chain_impact,
    get_company_fundamentals,
    get_analysis_tools,
    get_analysis_tool_handlers,
)

from app.tools.user_data_tools import (
    fetch_user_watchlist,
    fetch_user_portfolio,
    calculate_sector_exposure,
    get_user_preferences,
    get_user_data_tools,
    get_user_data_tool_handlers,
)

from app.tools.tool_registry import ToolRegistry

__all__ = [
    # Analysis tools
    "identify_sector_from_stocks",
    "analyze_supply_chain_impact",
    "get_company_fundamentals",
    "get_analysis_tools",
    "get_analysis_tool_handlers",
    # User data tools
    "fetch_user_watchlist",
    "fetch_user_portfolio",
    "calculate_sector_exposure",
    "get_user_preferences",
    "get_user_data_tools",
    "get_user_data_tool_handlers",
    # Registry
    "ToolRegistry",
]
