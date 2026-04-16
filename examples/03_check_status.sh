#!/usr/bin/env bash
# ── Example 3: Check job status ───────────────────────────────────────────────
# GET /api/v1/cv/runs/{run_id}/status
#
# Replace RUN_ID with the run_id returned from Example 1 (async trigger).
# lifecycle_state values: PENDING | RUNNING | TERMINATING | TERMINATED
# result_state values (only when TERMINATED): SUCCESS | FAILED | TIMEDOUT

API_URL="http://localhost:8000"
API_KEY="change-me-in-production"
RUN_ID="464504671128240"  # Replace with your actual run_id

curl -s -X GET "$API_URL/api/v1/cv/runs/$RUN_ID/status" \
  -H "Authorization: Bearer $API_KEY" \
  | python -m json.tool

# ── Expected response (running) ───────────────────────────────────────────────
# {
#   "run_id": 464504671128240,
#   "lifecycle_state": "RUNNING",
#   "result_state": null,
#   "state_message": "",
#   "is_complete": false,
#   "is_success": false
# }

# ── Expected response (completed) ────────────────────────────────────────────
# {
#   "run_id": 464504671128240,
#   "lifecycle_state": "TERMINATED",
#   "result_state": "SUCCESS",
#   "state_message": "",
#   "is_complete": true,
#   "is_success": true
# }
