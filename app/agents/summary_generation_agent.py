"""
Summary Generation Agent for creating market summaries with causal language.

Responsibilities:
- Generate market summary bullets with causal explanations
- Create trending news section for mid-market
- Produce executive summary
"""

from typing import Dict, List, Optional

from app.agents.base import BaseAgent, AgentConfig, AgentExecutionContext
from app.config import get_settings
from app.models.agent_schemas import (
    SummaryGenerationAgentInput,
    SummaryGenerationAgentOutput,
)
from app.models.domain import MarketSummaryBullet, NewsItem
from app.prompts.summary_generation_prompts import SUMMARY_GENERATION_SYSTEM_PROMPT
from app.tools.analysis_tools import (
    get_analysis_tools,
    get_analysis_tool_handlers,
)


# Causal keywords that must be present in summaries
CAUSAL_KEYWORDS = [
    "due to",
    "after",
    "following",
    "driven by",
    "as",
    "because",
    "on account of",
    "amid",
    "on the back of",
    "triggered by",
    "led by",
    "supported by",
    "weighed by",
]


class SummaryGenerationAgent(BaseAgent[SummaryGenerationAgentInput, SummaryGenerationAgentOutput]):
    """
    Specialized agent for generating market summaries.
    
    This agent creates:
    - Market summary bullets with mandatory causal language
    - Trending news section for mid-market phase
    - Executive summary
    """

    input_schema = SummaryGenerationAgentInput
    output_schema = SummaryGenerationAgentOutput

    def __init__(self):
        settings = get_settings()
        config = AgentConfig(
            name="summary_generation_agent",
            description="Generates market summaries with causal language",
            model_name=settings.GEMINI_FAST_MODEL,
            temperature=0.3,  # Some creativity for narrative
            max_output_tokens=4096,
            timeout_seconds=settings.SUMMARY_AGENT_TIMEOUT,
            retry_attempts=2,
        )
        super().__init__(config)

        # Register tool handlers
        for name, handler in get_analysis_tool_handlers().items():
            self.register_tool_handler(name, handler)

    def get_system_prompt(self) -> str:
        return SUMMARY_GENERATION_SYSTEM_PROMPT

    def get_tools(self):
        return get_analysis_tools()

    async def execute(
        self,
        input_data: SummaryGenerationAgentInput,
        context: AgentExecutionContext,
    ) -> SummaryGenerationAgentOutput:
        """
        Execute summary generation.
        
        Steps:
        1. If mid-market: Generate trending news section
        2. If pre/post market: Generate causal summary bullets
        3. Generate executive summary
        4. Extract key takeaways
        """
        self.logger.info(
            "executing_summary_generation",
            market_phase=input_data.market_phase,
            news_count=len(input_data.news_with_impacts),
            request_id=context.request_id,
        )

        market_summary_bullets: Optional[List[MarketSummaryBullet]] = None
        trending_now: Optional[List[NewsItem]] = None
        
        if input_data.market_phase == "mid":
            # Mid-market: Generate trending news
            trending_now = self._generate_trending_now(input_data)
            bullets_generated = 0
        else:
            # Pre/Post market: Generate causal summaries
            market_summary_bullets = self._generate_causal_summaries(input_data)
            bullets_generated = len(market_summary_bullets)

        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            input_data,
            market_summary_bullets,
        )

        # Extract key takeaways
        key_takeaways = self._extract_key_takeaways(input_data)

        self.logger.info(
            "summary_generation_complete",
            bullets=bullets_generated,
            trending_count=len(trending_now) if trending_now else 0,
        )

        return SummaryGenerationAgentOutput(
            market_summary_bullets=market_summary_bullets,
            trending_now_section=trending_now,
            executive_summary=executive_summary,
            key_takeaways=key_takeaways,
            generation_metadata={
                "bullets_generated": bullets_generated,
                "market_phase": input_data.market_phase,
                "news_analyzed": len(input_data.news_with_impacts),
                "themes_used": len(input_data.refined_themes),
            },
        )

    def _generate_causal_summaries(
        self,
        input_data: SummaryGenerationAgentInput,
    ) -> List[MarketSummaryBullet]:
        """Generate summary bullets with causal language."""
        bullets: List[MarketSummaryBullet] = []

        # Sort news by importance (using impact confidence as proxy)
        sorted_news = sorted(
            input_data.news_with_impacts,
            key=lambda x: x.impact_confidence,
            reverse=True,
        )

        # Get market outlook info
        outlook_text = ""
        if input_data.market_outlook:
            direction = "higher" if input_data.market_outlook.sentiment == "bullish" else (
                "lower" if input_data.market_outlook.sentiment == "bearish" else "flat"
            )
            change = abs(input_data.market_outlook.nifty_change_percent)
            outlook_text = f"Markets trading {direction} by {change:.1f}%"

        # Generate bullets based on top news and themes
        used_themes = set()
        
        for nwi in sorted_news[:5]:  # Consider top 5 news
            if len(bullets) >= input_data.max_bullets:
                break

            # Find which theme this news belongs to
            theme_name = None
            for theme in input_data.refined_themes:
                if nwi.news_id in [n.id for n in theme.news_items]:
                    if theme.theme_name not in used_themes:
                        theme_name = theme.theme_name
                        used_themes.add(theme_name)
                    break

            # Generate causal bullet
            bullet_text = self._create_causal_bullet(
                nwi,
                input_data.indices_data,
                outlook_text,
            )

            if bullet_text and self._has_causal_language(bullet_text):
                sentiment = "bullish" if nwi.news_item.sentiment == "bullish" else (
                    "bearish" if nwi.news_item.sentiment == "bearish" else "neutral"
                )
                
                bullets.append(
                    MarketSummaryBullet(
                        text=bullet_text,
                        supporting_news_ids=[nwi.news_id],
                        confidence=nwi.impact_confidence,
                        sentiment=sentiment,
                    )
                )

        # If we don't have enough bullets, create from themes
        if len(bullets) < input_data.max_bullets:
            for theme in input_data.refined_themes:
                if len(bullets) >= input_data.max_bullets:
                    break
                if theme.theme_name in used_themes:
                    continue

                bullet_text = self._create_theme_bullet(theme, outlook_text)
                if bullet_text and self._has_causal_language(bullet_text):
                    bullets.append(
                        MarketSummaryBullet(
                            text=bullet_text,
                            supporting_news_ids=[n.id for n in theme.news_items[:2]],
                            confidence=0.75,
                            sentiment=theme.overall_sentiment,
                        )
                    )

        return bullets

    def _create_causal_bullet(
        self,
        nwi,  # NewsWithImpact
        indices_data: Dict,
        outlook_text: str,
    ) -> str:
        """Create a single causal bullet from news impact."""
        news = nwi.news_item
        
        # Determine the causal connector based on sentiment
        if news.sentiment == "bullish":
            connectors = ["driven by", "supported by", "on the back of"]
        elif news.sentiment == "bearish":
            connectors = ["weighed by", "pressured by", "following"]
        else:
            connectors = ["amid", "following", "as"]

        connector = connectors[0]

        # Build the bullet
        if nwi.impacted_stocks:
            affected = ", ".join([s.ticker for s in nwi.impacted_stocks[:3]])
            return (
                f"{affected} {'gained' if news.sentiment == 'bullish' else 'faced pressure'} "
                f"{connector} {news.headline.lower()[:60]}."
            )
        
        # Fallback to sector-level
        if nwi.sector_impacts:
            sector = list(nwi.sector_impacts.keys())[0]
            impact = nwi.sector_impacts[sector]
            return (
                f"{sector} sector shows {impact} momentum {connector} "
                f"{news.headline.lower()[:50]}."
            )

        return ""

    def _create_theme_bullet(self, theme, outlook_text: str) -> str:
        """Create a bullet from a theme."""
        sentiment_words = {
            "bullish": "positive momentum",
            "bearish": "headwinds",
            "neutral": "consolidation",
            "mixed": "mixed signals",
        }

        sentiment_desc = sentiment_words.get(theme.overall_sentiment, "movement")
        
        if theme.impacted_stocks:
            stocks = ", ".join(theme.impacted_stocks[:3])
            return (
                f"{stocks} showing {sentiment_desc} driven by "
                f"{theme.theme_name.lower()} developments."
            )
        
        return (
            f"{theme.theme_name} sector seeing {sentiment_desc} "
            f"on the back of recent news flow."
        )

    def _has_causal_language(self, text: str) -> bool:
        """Check if text contains causal language."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in CAUSAL_KEYWORDS)

    def _generate_trending_now(
        self,
        input_data: SummaryGenerationAgentInput,
    ) -> List[NewsItem]:
        """Generate trending news section for mid-market."""
        # Sort by recency (published_at)
        all_news = [nwi.news_item for nwi in input_data.news_with_impacts]
        
        sorted_news = sorted(
            all_news,
            key=lambda x: x.published_at,
            reverse=True,  # Newest first
        )

        # Return top 5 most recent
        return sorted_news[:5]

    def _generate_executive_summary(
        self,
        input_data: SummaryGenerationAgentInput,
        bullets: Optional[List[MarketSummaryBullet]],
    ) -> str:
        """Generate 2-3 sentence executive summary."""
        parts = []

        # Market direction
        if input_data.market_outlook:
            direction = input_data.market_outlook.sentiment
            change = input_data.market_outlook.nifty_change_percent
            
            if direction == "bullish":
                parts.append(f"Markets trading higher with NIFTY up {change:.1f}%.")
            elif direction == "bearish":
                parts.append(f"Markets under pressure with NIFTY down {abs(change):.1f}%.")
            else:
                parts.append(f"Markets trading flat with NIFTY at {change:.1f}%.")

        # Key drivers
        if input_data.refined_themes:
            top_theme = input_data.refined_themes[0]
            if top_theme.overall_sentiment == "bullish":
                parts.append(f"Key driver: {top_theme.theme_name} providing support.")
            elif top_theme.overall_sentiment == "bearish":
                parts.append(f"Pressure from: {top_theme.theme_name} weighing on sentiment.")

        # Portfolio context
        if input_data.portfolio_impact:
            if input_data.portfolio_impact.overall_sentiment == "positive":
                parts.append("Your portfolio positioned to benefit from current trends.")
            elif input_data.portfolio_impact.overall_sentiment == "negative":
                parts.append("Monitor portfolio exposure to current headwinds.")

        return " ".join(parts) if parts else "Market activity ongoing. Key developments being monitored."

    def _extract_key_takeaways(
        self,
        input_data: SummaryGenerationAgentInput,
    ) -> List[str]:
        """Extract key takeaways for the user."""
        takeaways = []

        # Market outlook takeaway
        if input_data.market_outlook:
            sentiment = input_data.market_outlook.sentiment
            takeaways.append(f"Market sentiment is {sentiment}")

        # Theme-based takeaways
        for theme in input_data.refined_themes[:2]:
            if theme.overall_sentiment == "bullish":
                takeaways.append(f"{theme.theme_name} showing strength")
            elif theme.overall_sentiment == "bearish":
                takeaways.append(f"Caution in {theme.theme_name}")

        # Portfolio takeaway
        if input_data.portfolio_impact:
            if input_data.portfolio_impact.top_affected_holdings:
                top = input_data.portfolio_impact.top_affected_holdings[0]
                takeaways.append(f"Watch {top} for near-term movement")

        return takeaways[:4]
