#!/usr/bin/env bash
# ── Example 2: Trigger enrichment (synchronous) ───────────────────────────────
# POST /api/v1/cv/enrich/sync
#
# Waits up to 5 minutes for the Databricks job to finish.
# Returns the full enriched CV in one shot.
# Use this for simple integrations; use async for high-throughput scenarios.

API_URL="http://localhost:8000"
API_KEY="change-me-in-production"

curl -s -X POST "$API_URL/api/v1/cv/enrich/sync" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "jobDescription": {
      "id": "jd-002",
      "title": "Data Engineer",
      "requirements": ["Python", "Spark", "Databricks", "SQL"],
      "responsibilities": ["Build data pipelines", "Optimize ETL processes"],
      "niceToHave": ["Airflow", "dbt", "Kafka"]
    },
    "greenhouseParseData": {
      "candidateId": "99887766",
      "firstName": "Carlos",
      "lastName": "Mendez",
      "email": "carlos.mendez@example.com",
      "phone": "+52-55-1234-5678",
      "currentTitle": "Data Engineer",
      "currentCompany": "DataFlow S.A.",
      "education": [
        {"degree": "M.S. Computer Science", "institution": "UNAM", "years": "2016-2018"}
      ],
      "employmentHistory": [
        {"title": "Data Engineer", "company": "DataFlow S.A.", "years": "2019-Present"},
        {"title": "Analytics Engineer", "company": "BigData Co.", "years": "2018-2019"}
      ]
    },
    "jsonCvTextExtracted": {
      "rawText": "Carlos Mendez\nData Engineer at DataFlow S.A. (2019-Present)\nSkills: Python, Apache Spark, Databricks, SQL, Airflow, dbt\nLanguages: Spanish (Native), English (C1)\nCertifications: Databricks Certified Associate Developer for Apache Spark",
      "structured": {
        "skills": ["Python", "Apache Spark", "Databricks", "SQL", "Airflow", "dbt"],
        "certifications": ["Databricks Certified Associate Developer for Apache Spark"],
        "languages": ["Spanish", "English"]
      }
    },
    "documentType": 1
  }' | python -m json.tool

# ── Expected response ─────────────────────────────────────────────────────────
# HTTP 200 OK
# {
#   "run_id": 0,
#   "status": "completed",
#   "processing_time_ms": 18500,
#   "data": {
#     "full_name": "Carlos Mendez",
#     "technical_skills": ["Python", "Apache Spark", "Databricks", ...],
#     "summary": "...",
#     ...
#   }
# }
