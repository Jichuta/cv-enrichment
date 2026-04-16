#!/usr/bin/env bash
# ── Example 1: Trigger enrichment (async) ────────────────────────────────────
# POST /api/v1/cv/enrich
#
# Returns immediately with a run_id.
# Use examples/03_check_status.sh to poll completion.

API_URL="http://localhost:8000"
API_KEY="change-me-in-production"  # Must match API_SECRET_KEY in .env

curl -s -X POST "$API_URL/api/v1/cv/enrich" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "jobDescription": {
      "id": "jd-001",
      "title": "Senior Python Developer",
      "requirements": ["Python", "FastAPI", "PostgreSQL", "Docker"],
      "responsibilities": ["Build and maintain REST APIs", "Mentor junior devs"],
      "niceToHave": ["AWS", "Kubernetes", "Redis"]
    },
    "greenhouseParseData": {
      "candidateId": "53883394",
      "firstName": "Jane",
      "lastName": "Smith",
      "email": "jane.smith@example.com",
      "phone": "+1-555-0199",
      "currentTitle": "Python Developer",
      "currentCompany": "TechCorp Inc.",
      "education": [
        {"degree": "B.S. Computer Science", "institution": "MIT", "years": "2015-2019"}
      ],
      "employmentHistory": [
        {"title": "Python Developer", "company": "TechCorp Inc.", "years": "2020-Present"},
        {"title": "Junior Developer", "company": "StartupXYZ", "years": "2019-2020"}
      ]
    },
    "jsonCvTextExtracted": {
      "rawText": "Jane Smith\nPython Developer at TechCorp Inc. (2020-Present)\nSkills: Python, FastAPI, PostgreSQL, Docker, AWS\nEducation: B.S. Computer Science, MIT (2015-2019)\nCertifications: AWS Solutions Architect Associate (2022)",
      "structured": {
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "certifications": ["AWS Solutions Architect Associate"]
      }
    },
    "documentType": 1
  }' | python -m json.tool

# ── Expected response ─────────────────────────────────────────────────────────
# HTTP 202 Accepted
# {
#   "run_id": 464504671128240,
#   "status": "started",
#   "message": "CV enrichment job triggered. Poll /cv/runs/{run_id}/status ..."
# }
