"""
Canonical list of allowed themes for themed news (post-market / pre-market).

Sector-Driven (Core): 1–10
Macro / Flow-Driven: 11–14
Structural / Emerging: 15
"""

from typing import List, Optional

# Max number of themed news items returned by the API (impacted in post-market, pre-market).
MAX_THEMED_NEWS_ITEMS = 5

# Allowed theme display names (exact strings for API response).
ALLOWED_THEMES: List[str] = [
    # Sector-Driven (Core)
    "Banking & Financials",
    "Information Technology (IT)",
    "Oil, Gas & Energy",
    "FMCG & Consumer Staples",
    "Consumer Discretionary",
    "Automobiles & Auto Ancillaries",
    "Pharma & Healthcare",
    "Metals & Mining",
    "Infrastructure & Capital Goods",
    "Real Estate",
    # Macro / Flow-Driven
    "Global Market Cues",
    "RBI & Interest Rates",
    "Commodities & Crude Prices",
    "FII & DII Flows",
    # Structural / Emerging
    "EV, Green Energy & New-Age Themes",
]

# Map internal news_type / sector keywords to allowed theme name.
# Keys are lowercased for matching; value is the exact allowed theme string.
NEWS_TYPE_TO_THEME: dict = {
    "economy": "RBI & Interest Rates",
    "economic & policy updates": "RBI & Interest Rates",
    "foreign markets": "Global Market Cues",
    "global market updates": "Global Market Cues",
    "other markets": "Commodities & Crude Prices",
    "commodities & forex": "Commodities & Crude Prices",
    "general": "Global Market Cues",
}

# Map sector keywords (from mentioned_sectors) to allowed theme.
# Match is case-insensitive substring.
SECTOR_KEYWORDS_TO_THEME: List[tuple] = [
    (["banking", "banks", "nbfc", "financials", "insurer", "lending"], "Banking & Financials"),
    (["it", "information technology", "software", "tech", "export"], "Information Technology (IT)"),
    (["oil", "gas", "energy", "power", "utilities", "upstream", "downstream"], "Oil, Gas & Energy"),
    (["fmcg", "consumer staples", "staples", "defensive"], "FMCG & Consumer Staples"),
    (["consumer discretionary", "retail", "durables"], "Consumer Discretionary"),
    (["auto", "automobile", "oem", "ancillar"], "Automobiles & Auto Ancillaries"),
    (["pharma", "healthcare", "diagnostic", "hospital"], "Pharma & Healthcare"),
    (["metals", "mining", "steel", "aluminium"], "Metals & Mining"),
    (["infrastructure", "capital goods", "construction", "engineering"], "Infrastructure & Capital Goods"),
    (["real estate", "realty", "housing"], "Real Estate"),
    (["global", "us ", "europe", "asia", "overnight", "cues"], "Global Market Cues"),
    (["rbi", "interest rate", "monetary", "liquidity", "yield"], "RBI & Interest Rates"),
    (["commodit", "crude", "agri"], "Commodities & Crude Prices"),
    (["fii", "dii", "flow", "institutional"], "FII & DII Flows"),
    (["ev", "green energy", "renewable", "energy transition", "new-age"], "EV, Green Energy & New-Age Themes"),
]


def normalize_theme_to_allowed(theme_name: str) -> Optional[str]:
    """
    Map a theme name (from agents or clustering) to an allowed theme, or None if no match.

    First checks exact match in ALLOWED_THEMES, then tries news_type mapping, then sector keywords.
    """
    if not theme_name or not isinstance(theme_name, str):
        return None
    name = theme_name.strip()
    if name in ALLOWED_THEMES:
        return name
    key = name.lower()
    if key in NEWS_TYPE_TO_THEME:
        return NEWS_TYPE_TO_THEME[key]
    for keywords, allowed in SECTOR_KEYWORDS_TO_THEME:
        if any(kw in key for kw in keywords):
            return allowed
    # Fallback: try removing common suffixes like " News", " Update"
    for suffix in (" news", " update"):
        if key.endswith(suffix):
            base = key[: -len(suffix)].strip()
            if base in ALLOWED_THEMES:
                return base
            for k, v in NEWS_TYPE_TO_THEME.items():
                if k in base or base in k:
                    return v
            for keywords, allowed in SECTOR_KEYWORDS_TO_THEME:
                if any(kw in base for kw in keywords):
                    return allowed
    return None
