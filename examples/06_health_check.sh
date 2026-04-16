#!/usr/bin/env bash
# ── Example 6: Health check (no auth required) ───────────────────────────────
# GET /api/v1/health

API_URL="http://localhost:8000"

curl -s "$API_URL/api/v1/health" | python -m json.tool

# ── Expected response (healthy) ───────────────────────────────────────────────
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "environment": "development",
#   "dependencies": {
#     "databricks": "healthy"
#   }
# }

# ── Expected response (degraded) ─────────────────────────────────────────────
# {
#   "status": "degraded",
#   "version": "1.0.0",
#   "environment": "development",
#   "dependencies": {
#     "databricks": "unreachable"
#   }
# }
