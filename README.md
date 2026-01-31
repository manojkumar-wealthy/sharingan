# Market Pulse Engine

A production-grade Python backend using FastAPI, Celery, MongoDB, and Google AI (Gemini) that provides **AI-powered market intelligence** through a background processing architecture. The API serves pre-computed snapshots for sub-200ms response times.

## 🎯 Overview

Market Pulse is a market insights system that uses **3 specialized AI agents** running as Celery tasks to fetch news, process indices, and generate market snapshots. The API reads only from MongoDB—no real-time AI processing on request—ensuring fast, consistent responses.

### Key Design

- **Background Processing:** Celery tasks handle news fetch, AI analysis, and snapshot generation on a schedule
- **Pre-computed Snapshots:** API serves cached snapshots from MongoDB; target response time &lt; 200ms
- **3 Agents:** NewsProcessingAgent, SnapshotGenerationAgent, IndicesCollectionAgent
- **Data Sources:** CMOTS API for news and world indices; Gemini for sentiment and summaries

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Request                           │
│                    GET /api/v1/market-summary                 │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                       MongoDB                                │
│  ┌──────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │ market_snapshots │  │ news_articles  │  │indices_timeseries│
│  │ (TTL: 15 min)    │  │ (90 day retain)│  │ (90 day TTL)  │ │
│  └──────────────────┘  └────────────────┘  └──────────────┘ │
└─────────────────────────────────▲───────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────┐
│                    Celery Tasks (Background)                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │fetch_news (3m)  │  │gen_snapshot (5m) │  │fetch_indices │  │
│  └────────┬────────┘  └────────┬─────────┘  └──────┬───────┘ │
│           ▼                    ▼                    ▼         │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │NewsProcessing   │  │SnapshotGeneration│  │IndicesCollection│
│  │Agent (Gemini)   │  │Agent (Gemini)    │  │Agent           │
│  └─────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Agents

| Agent | Location | Responsibility |
|-------|----------|----------------|
| **NewsProcessingAgent** | `app/agents/news_processing_agent.py` | AI sentiment, entity extraction, summary, impact analysis |
| **SnapshotGenerationAgent** | `app/agents/snapshot_agent.py` | Market outlook, summary bullets, executive summary, trending news |
| **IndicesCollectionAgent** | `app/agents/indices_agent.py` | Fetch world indices from CMOTS, store in MongoDB, market-hours aware |

See [ARCHITECTURE.md](ARCHITECTURE.md) for data flow, task schedules, and configuration details.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google AI API key ([Google AI Studio](https://aistudio.google.com/apikey))
- Redis (Celery broker + cache)
- MongoDB
- Docker (optional, for Redis/MongoDB and full stack)

### Installation

1. **Clone and enter the project:**
   ```bash
   cd sharingan
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and .env.local with GOOGLE_AI_API_KEY, MONGODB_URL, REDIS_URL, etc.
   ```

5. **Run with the startup script (recommended):**
   ```bash
   ./run.sh all
   ```
   This starts Redis, MongoDB (via Docker), Celery worker, Celery beat, triggers initial data tasks, and runs the FastAPI server.

### Manual Run (without run.sh)

```bash
# Start Redis and MongoDB (e.g. via Docker or local install)
# Then:
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# In another terminal: start Celery worker and beat (see run.sh)
```

### Docker Deployment

```bash
# All services via docker-compose
./run.sh docker

# With dev/monitoring profile (e.g. Flower)
./run.sh docker-dev

# Or directly:
docker-compose up -d
docker-compose logs -f market-pulse-api
docker-compose down
```

## 📜 run.sh Commands Guide

The project includes a development script `run.sh` that manages local services. Ensure `.venv` exists and optionally create `.env.local` for overrides.

| Command | Description |
|---------|-------------|
| `./run.sh all` | Start **all** services: Redis, MongoDB, Celery worker, Celery beat, trigger initial data population, then run the FastAPI API (foreground). Use for full local dev. |
| `./run.sh debug` | Same as `all` but runs the API in **debug** mode (verbose logging, access log). |
| `./run.sh api` | Start **only** the FastAPI server (assumes Redis/MongoDB/Celery already running or not needed for read-only testing). |
| `./run.sh celery` | Start **Celery worker** and **Celery beat** in the background; script stays running and shows logs. Use Ctrl+C to stop. |
| `./run.sh worker` | Start **only** the Celery worker in the **foreground** (single terminal). |
| `./run.sh beat` | Start **only** Celery beat in the **foreground**. |
| `./run.sh flower` | Start **Flower** monitoring UI at http://localhost:5555 (foreground). |
| `./run.sh infra` | Start **only** infrastructure: Redis and MongoDB (Docker containers). |
| `./run.sh logs` | **Tail** Celery worker and beat log files (`logs/celery-worker.log`, `logs/celery-beat.log`). |
| `./run.sh populate` | **Trigger** initial data population tasks (news fetch, indices fetch, snapshot generation). Requires Celery worker running. |
| `./run.sh stop` | **Stop** all background services: Celery worker, Celery beat, Flower, and Docker containers (Redis, MongoDB). |
| `./run.sh status` | **Show status** of Redis, MongoDB, Celery worker, Celery beat, and Flower (running/stopped). |
| `./run.sh docker` | Run the full stack with **docker-compose** (build and up). |
| `./run.sh docker-dev` | Run with **docker-compose** using dev and monitoring profiles. |
| `./run.sh help` | Print usage and available commands. |

**Examples:**

```bash
# Full dev: API + Celery + infra + initial data
./run.sh all

# Only API (e.g. if Celery is already running elsewhere)
./run.sh api

# Only infra, then in another terminal run worker + beat + api
./run.sh infra
./run.sh celery   # in terminal 2
./run.sh api      # in terminal 3

# Check what's running
./run.sh status

# Stop everything
./run.sh stop
```

Celery logs are written to `logs/`. Use `./run.sh logs` to tail them.

## 📡 API Endpoints

### Primary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/market-summary` | Returns the latest pre-computed market snapshot from MongoDB. Target &lt; 200ms. Triggers async snapshot generation if none exists. |

### Supporting

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/snapshot/generate` | Manually trigger snapshot generation. |
| GET | `/api/v1/db/stats` | Database statistics. |
| POST | `/api/v1/data/populate` | Manually trigger data population (news, indices, snapshot). |
| GET | `/api/v1/health` | Health check. |
| GET | `/api/v1/agents/status` | Agent/task status. |

### Example: Get market summary

```bash
curl "http://localhost:8000/api/v1/market-summary"
```

## 📁 Project Structure

```
sharingan/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration (Pydantic Settings)
│   ├── agents/                     # AI agents (Celery task logic)
│   │   ├── base.py
│   │   ├── news_processing_agent.py
│   │   ├── snapshot_agent.py
│   │   └── indices_agent.py
│   ├── celery_app/
│   │   ├── celery_config.py
│   │   └── tasks/
│   │       ├── news_tasks.py
│   │       ├── snapshot_tasks.py
│   │       ├── indices_tasks.py
│   │       └── cleanup_tasks.py
│   ├── db/
│   │   ├── mongodb.py
│   │   ├── models/                 # MongoDB document models
│   │   └── repositories/
│   ├── models/                     # Pydantic request/response schemas
│   ├── services/                   # Business logic & external APIs
│   │   ├── cmots_news_service.py
│   │   ├── company_news_service.py
│   │   ├── news_processor_service.py
│   │   ├── snapshot_generator_service.py
│   │   └── redis_service.py
│   ├── constants/                  # Themes, tickers
│   ├── middleware/
│   ├── prompts/
│   ├── tools/
│   └── utils/
├── tests/
├── run.sh                          # Development run script
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── ARCHITECTURE.md
└── README.md
```

## 🔧 Configuration

Key environment variables (see `app/config.py` and `.env` / `.env.local`):

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_AI_API_KEY` | Google AI (Gemini) API key | Required |
| `GEMINI_FAST_MODEL` | Model for fast tasks | `gemini-2.0-flash` |
| `GEMINI_PRO_MODEL` | Model for complex tasks | `gemini-1.5-pro` |
| `MONGODB_URL` | MongoDB connection URL | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Database name | `market_intelligence` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `CELERY_BROKER_URL` | Celery broker (Redis) | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery results backend | `redis://localhost:6379/1` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `NEWS_FETCH_INTERVAL` | News task interval (seconds) | `180` (3 min) |
| `SNAPSHOT_GENERATION_INTERVAL` | Snapshot task interval (seconds) | `300` (5 min) |
| `INDICES_FETCH_INTERVAL` | Indices task interval (seconds) | `300` (5 min) |

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_market_data_agent.py

# Integration tests
pytest tests/integration/
```

## 📊 Monitoring

- **Structured logging:** JSON-formatted logs with request tracing
- **Health checks:** `/api/v1/health`, `/api/v1/agents/status`
- **Flower:** Celery monitoring at http://localhost:5555 when started via `./run.sh flower` or docker-dev profile

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository  
2. Create a feature branch  
3. Make changes with tests  
4. Submit a pull request  

## 📧 Support

For questions or issues, please open a GitHub issue.
