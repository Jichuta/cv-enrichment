# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup

The `.venv` directory is **not committed** — run this once before anything else:

```bash
./setup.sh          # Creates .venv/, installs deps, copies .env.example → .env
```

Activate before running any commands:
```bash
source .venv/Scripts/activate   # Windows (Git Bash)
source .venv/bin/activate       # Mac/Linux
```

If you only need to reinstall dependencies without re-running the full setup:
```bash
pip install -r requirements.txt        # Production dependencies
pip install -r requirements-dev.txt    # Dev dependencies (pytest, ruff, mypy)
```

### Running
```bash
python run.py                                          # Reads APP_HOST/APP_PORT/APP_DEBUG from .env
uvicorn app.main:app --host 0.0.0.0 --port 8000        # Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug  # Dev with hot-reload
```

### Testing & Quality
```bash
pytest tests/ -v                         # Run all tests
pytest tests/path/test_file.py           # Run a single test file
pytest -k "test_name"                    # Run tests matching a pattern
ruff check app/                          # Lint
ruff format app/                         # Auto-format
mypy app/                                # Type-check
```

### Docker
```bash
docker build --target runtime -t cv-enrichment:local .   # Build production image
docker compose up -d                                      # Start production container
docker compose down                                       # Stop containers
docker compose --profile dev up api-dev                   # Dev container with hot-reload
```

### API Docs (local dev)

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/api/v1/health | Health check (no auth required) |

## Architecture

### High-Level Flow

```
Client → FastAPI (Bearer auth) → EnrichmentService → Databricks Jobs API / LLM Serving
                                                   ↓
                                        GCS (output artifacts)
```

The service exposes three enrichment strategies, all accepting the same `EnrichCVRequest` body (camelCase, Greenhouse-compatible):

| Endpoint | Mode | Description |
|---|---|---|
| `POST /api/v1/cv/enrich` | Async | Triggers Databricks job, returns `run_id` immediately (202) |
| `POST /api/v1/cv/enrich/sync` | Sync | Triggers job and polls until completion (up to ~5 min) |
| `POST /api/v1/cv/enrich/direct` | Direct LLM | Calls Model Serving directly; no job, no Delta table write |

Async mode requires the client to poll:
- `GET /api/v1/cv/runs/{run_id}/status`
- `GET /api/v1/cv/runs/{run_id}/result`

### Key Modules

- [app/main.py](app/main.py) — FastAPI app factory; registers middleware, exception handlers, routers
- [app/api/v1/endpoints/enrich.py](app/api/v1/endpoints/enrich.py) — All enrichment route handlers
- [app/api/deps.py](app/api/deps.py) — Bearer token auth dependency (`verify_api_key`)
- [app/services/enrichment.py](app/services/enrichment.py) — Orchestrator; delegates to Databricks clients
- [app/services/databricks_jobs.py](app/services/databricks_jobs.py) — Async client for Databricks Jobs REST API 2.0 (trigger, poll, fetch output)
- [app/services/databricks_llm.py](app/services/databricks_llm.py) — Async client for Databricks Model Serving (OpenAI-compatible)
- [app/schemas/enrich.py](app/schemas/enrich.py) — Pydantic v2 request/response models with camelCase aliases
- [app/core/config.py](app/core/config.py) — `Settings` class (pydantic-settings); all env vars loaded here
- [app/core/exceptions.py](app/core/exceptions.py) — Custom exception hierarchy (`AppException`, `DatabricksError`, `DatabricksJobFailedError`, `DatabricksTimeoutError`, `LLMError`)

### Databricks Integration Details

- **Jobs API**: POSTs to `/api/2.0/jobs/run-now` with JSON params; polls `/api/2.1/jobs/runs/get` every `DATABRICKS_JOB_POLL_INTERVAL_SECS` seconds until terminal state or `DATABRICKS_JOB_TIMEOUT_SECS` elapsed
- **LLM Model Serving**: POSTs to `/serving-endpoints/{model}/invocations` using an OpenAI-compatible `chat/completions` format
- **Output**: Databricks jobs write enriched results to GCS; the API retrieves them via signed URLs parsed from the run's output log
- **Clients**: Both clients are singletons with a shared `httpx.AsyncClient`; initialized at startup via FastAPI lifespan

### Configuration

All settings come from environment variables loaded by `app/core/config.py`. Copy `.env.example` to `.env` and fill in:

```
API_SECRET_KEY                     # Bearer token for all endpoints
DATABRICKS_HOST                    # e.g. https://adb-xxx.azuredatabricks.net
DATABRICKS_TOKEN                   # Personal access token
DATABRICKS_ENRICHMENT_JOB_ID      # Numeric job ID
DATABRICKS_LLM_MODEL              # e.g. databricks-gemma-3-12b
```

### Async Pattern

All Databricks I/O is async (`httpx.AsyncClient`). Polling uses `asyncio.sleep`. Never introduce blocking calls (e.g., `requests`, `time.sleep`) inside endpoint handlers or services.

### Error Handling

Raise from the custom hierarchy in `app/core/exceptions.py`. The global exception handler in `app/main.py` converts these to structured JSON responses with a `request_id`. Don't return raw exception messages directly from endpoints.
