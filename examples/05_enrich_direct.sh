#!/usr/bin/env bash
# ── Example 5: Direct LLM enrichment (no Databricks job) ─────────────────────
# POST /api/v1/cv/enrich/direct
#
# Calls Databricks Model Serving directly — fastest option.
# Does NOT write results to Delta tables.
# Great for testing or one-off enrichment without the job overhead.

API_URL="http://localhost:8000"
API_KEY="change-me-in-production"

curl -s -X POST "$API_URL/api/v1/cv/enrich/direct" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "cv_text": "John Locke\nSoftware Engineer at Oceanic Airlines (2019-Present)\nEmail: john.locke@oceanic.com | Phone: +1-555-0123\nSkills: Python, JavaScript, React, PostgreSQL, Docker, AWS\nExperience: 6 years building distributed systems and REST APIs.\nEducation: B.S. Computer Science, Oxford University (2013-2017)\nCertifications: AWS Solutions Architect Professional (2023)\nLanguages: English (Native), Spanish (B2)",
    "job_title": "Senior Software Engineer",
    "job_requirements": ["Python", "React", "AWS", "PostgreSQL", "Docker"],
    "candidate_name": "John Locke"
  }' | python -m json.tool

# ── Expected response ─────────────────────────────────────────────────────────
# HTTP 200 OK
# {
#   "full_name": "John Locke",
#   "first_name": "John",
#   "last_name": "Locke",
#   "email": "john.locke@oceanic.com",
#   "phone": "+15550123",
#   "technical_skills": ["Python", "JavaScript", "React", "PostgreSQL", "Docker", "AWS"],
#   "english_level": "Native",
#   "total_experience": 6.0,
#   "summary": "Senior Software Engineer with 6 years of experience...",
#   ...
# }
