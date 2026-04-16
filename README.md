# CV Enrichment Service

A service that enriches CVs based on job descriptions by reordering experience, improving descriptions, and generating professional PDF/DOCX documents.

## Documentation

- **[Proposal](docs/proposal/proposal.md)** - MVP documentation with architecture, tech stack, and Databricks integration details
- **[Recommendation](docs/proposal/recommended.md)** - Analysis of the proposed architecture with cost/effort considerations

## Getting Started

The `.venv` directory is not committed — run setup once before anything else:

```bash
./setup.sh
```

This creates `.venv/`, installs dependencies, and copies `.env.example` → `.env`. Then fill in your credentials:

```
DATABRICKS_TOKEN=...
API_SECRET_KEY=...
```

Activate the virtual environment before running any commands:

```bash
# Windows (Git Bash)
source .venv/Scripts/activate

# Mac/Linux
source .venv/bin/activate
```

Start the server:

```bash
# Simple (reads config from .env)
python run.py

# With hot-reload (dev)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Running with Docker

```bash
docker compose up -d                             # Start (production)
docker compose --profile dev up api-dev          # Start with hot-reload
docker compose down                              # Stop
```

Once running, the following URLs are available locally:

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/api/v1/health | Health check (no auth required) |

## Quick Overview

| Component | Technology |
|-----------|------------|
| API | FastAPI |
| Processing | Databricks (Spark + AI) |
| Storage | PostgreSQL, GCS |
| Output | PDF / DOCX |