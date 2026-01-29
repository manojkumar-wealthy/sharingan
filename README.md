# Market Pulse Multi-Agent API (Simplified)

A production-grade Python backend using FastAPI and Google AI (Gemini) that implements a **Simplified 3-Agent Orchestration System** to power the "Market Pulse" feature.

## 🎯 Overview

Market Pulse is an AI-powered market insights system that uses specialized agents with distinct responsibilities to analyze market data, news, and user portfolios to generate comprehensive market summaries with causal reasoning.

### Why Simplified Multi-Agent?

- **Reduced Complexity:** 3 agents instead of 5 - easier to maintain and debug
- **Efficient Data Flow:** Merged agents eliminate redundant data passing
- **Faster Execution:** Fewer agent transitions = lower latency
- **Better Cohesion:** Related functions are co-located in single agents
- **Service-Oriented:** Data fetching moved to services, agents focus on analysis

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                        │
│  (Coordinates all agents, synthesizes final response)        │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼────────┐    │    ┌────────▼─────────┐
│    MARKET      │    │    │   PORTFOLIO      │
│  INTELLIGENCE  │    │    │    INSIGHT       │
│     AGENT      │    │    │     AGENT        │
│                │    │    │                  │
│ - Market Data  │    │    │ - User Context   │
│ - News Fetch   │    │    │ - Impact Analysis│
│ - Sentiment    │    │    │ - Alerts         │
│ - Themes       │    │    │ - Causal Chains  │
└────────────────┘    │    └──────────────────┘
                      │
        ┌─────────────▼─────────────┐
        │  SUMMARY GENERATION AGENT │
        │                           │
        │ - Market Summary          │
        │ - Causal Narratives       │
        │ - Key Takeaways           │
        └───────────────────────────┘
```

### Agents

| Agent | Merged From | Responsibility |
|-------|-------------|---------------|
| **Market Intelligence Agent** | MarketData + NewsAnalysis | Fetches indices, news, determines market phase, analyzes sentiment |
| **Portfolio Insight Agent** | UserContext + ImpactAnalysis | Retrieves user data, analyzes news impact, generates alerts |
| **Summary Generation Agent** | (unchanged) | Creates market summaries with causal language |
| **Orchestrator** | (unchanged) | Coordinates 3-phase execution, handles failures |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google AI API key (get one from [Google AI Studio](https://aistudio.google.com/apikey))
- Redis (optional, for caching)
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository:**
   ```bash
   cd market-pulse-backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up Google Cloud credentials:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   ```

6. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f market-pulse-api

# Stop services
docker-compose down
```

## 📡 API Endpoints

### Generate Market Pulse

```bash
POST /api/v1/pulse
```

**Request:**
```json
{
    "user_id": "user_123",
    "selected_indices": ["NIFTY 50", "SENSEX", "BANK NIFTY"],
    "include_watchlist": true,
    "include_portfolio": true,
    "news_filter": "all",
    "max_news_items": 50
}
```

**Response:**
```json
{
    "generated_at": "2026-01-30T10:30:00Z",
    "market_phase": "pre",
    "market_outlook": {
        "sentiment": "bullish",
        "confidence": 0.85,
        "reasoning": "NIFTY 50 is up 0.85%",
        "nifty_change_percent": 0.85
    },
    "market_summary": [
        {
            "text": "Markets set to open higher driven by positive global cues...",
            "supporting_news_ids": ["news_001"],
            "confidence": 0.9
        }
    ],
    "themed_news": [...],
    "all_news": [...],
    "portfolio_impact_summary": "Your portfolio is likely to benefit..."
}
```

### Health Check

```bash
GET /api/v1/health
```

### Agent Status

```bash
GET /api/v1/agents/status
```

## 📁 Project Structure

```
market-pulse-backend/
├── app/
│   ├── main.py                         # FastAPI application
│   ├── config.py                       # Configuration
│   ├── agents/                         # Agent implementations
│   │   ├── base.py                     # Base agent class
│   │   ├── orchestrator.py             # 3-phase orchestrator
│   │   ├── market_intelligence_agent.py # Market data + news
│   │   ├── portfolio_insight_agent.py  # User context + impact
│   │   └── summary_generation_agent.py # Summary generation
│   ├── models/                         # Pydantic models
│   │   ├── agent_schemas.py            # Agent I/O schemas
│   │   ├── domain.py                   # Domain models
│   │   ├── requests.py                 # API requests
│   │   └── responses.py                # API responses
│   ├── services/                       # Business services
│   │   ├── cache_service.py            # Redis caching
│   │   └── market_intelligence_service.py # Data fetching
│   ├── tools/                          # Agent tools
│   │   ├── analysis_tools.py           # Impact analysis tools
│   │   ├── user_data_tools.py          # User data tools
│   │   └── tool_registry.py            # Tool registration
│   ├── prompts/                        # System prompts
│   │   ├── market_intelligence_prompts.py
│   │   ├── portfolio_insight_prompts.py
│   │   └── summary_generation_prompts.py
│   ├── utils/                          # Utilities
│   │   ├── logging.py
│   │   ├── tracing.py
│   │   └── exceptions.py
│   └── middleware/                     # Middleware
├── tests/                              # Test suite
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_AI_API_KEY` | Google AI Studio API key | Required |
| `GEMINI_FAST_MODEL` | Fast model for agents | `gemini-2.0-flash-exp` |
| `GEMINI_PRO_MODEL` | Pro model for complex tasks | `gemini-1.5-pro` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `ENABLE_CACHING` | Enable response caching | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_market_intelligence_agent.py

# Run integration tests
pytest tests/integration/
```

## 📊 Monitoring

The API includes:

- **Structured Logging:** JSON-formatted logs with request tracing
- **OpenTelemetry Tracing:** Distributed tracing support
- **Health Checks:** Endpoint for liveness/readiness probes
- **Metrics:** Agent execution times and success rates

## 🔄 Simplified Orchestration Flow

1. **Phase 1:** Market Intelligence Agent
   - Fetches market indices data
   - Determines market phase (pre/mid/post)
   - Fetches and analyzes news
   - Clusters news into themes
   
2. **Phase 2:** Portfolio Insight Agent
   - Fetches user watchlist and portfolio
   - Analyzes news impact on holdings
   - Generates watchlist alerts
   - Builds causal chains
   
3. **Phase 3:** Summary Generation Agent
   - Creates market summary bullets
   - Generates executive summary
   - Extracts key takeaways

### Fallback Strategies

- Market Intelligence fails → Use cached data, return degraded response
- Portfolio Insight fails → Proceed with defaults, mark degraded
- Summary fails → Template-based summary

## 🛠️ Development

### Agent Responsibilities

| Agent | Service Used | Tools |
|-------|--------------|-------|
| Market Intelligence | MarketIntelligenceService | fetch_market_intelligence, fetch_market_indices, get_market_phase, fetch_market_news, cluster_news_by_topic |
| Portfolio Insight | - | fetch_user_watchlist, fetch_user_portfolio, calculate_sector_exposure, analyze_supply_chain_impact |
| Summary Generation | - | get_analysis_tools |

### Replacing Mock Data

The tools use mock data by default. To connect real data sources:

1. Update service functions in `app/services/market_intelligence_service.py`
2. Update tool functions in `app/tools/`
3. Configure API URLs in environment
4. Add authentication as needed

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📧 Support

For questions or issues, please open a GitHub issue.
