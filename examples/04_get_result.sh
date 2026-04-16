#!/usr/bin/env bash
# ── Example 4: Fetch enrichment result ───────────────────────────────────────
# GET /api/v1/cv/runs/{run_id}/result
#
# Call this AFTER the job status shows is_complete=true and is_success=true.

API_URL="http://localhost:8000"
API_KEY="change-me-in-production"
RUN_ID="464504671128240"  # Replace with your actual run_id

curl -s -X GET "$API_URL/api/v1/cv/runs/$RUN_ID/result" \
  -H "Authorization: Bearer $API_KEY" \
  | python -m json.tool

# ── Expected response ─────────────────────────────────────────────────────────
# {
#   "run_id": 464504671128240,
#   "status": "completed",
#   "data": {
#     "full_name": "Jane Smith",
#     "first_name": "Jane",
#     "last_name": "Smith",
#     "email": "jane.smith@example.com",
#     "phone": "+15550199",
#     "linkedin": "",
#     "candidate_location": "",
#     "english_level": "C1",
#     "current_title": "Python Developer",
#     "current_company": "TechCorp Inc.",
#     "total_experience": 5.0,
#     "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
#     "soft_skills": ["Team collaboration", "Problem solving"],
#     "education": [...],
#     "work_experience": [...],
#     "certifications": [{"name": "AWS Solutions Architect Associate", "year": "2022"}],
#     "summary": "Senior Python Developer with 5+ years of experience...",
#     "safety_information": {"red_flags": [], "safety_certifications": []}
#   }
# }
