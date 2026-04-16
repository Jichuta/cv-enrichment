"""Direct Databricks LLM client — OpenAI-compatible Model Serving API.

Use this when you want to call the LLM directly (no job required).
Faster for one-off enrichment calls; does NOT write to Delta tables.
"""

import json
import logging
import re
from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class DatabricksLLMClient:
    """Calls Databricks Model Serving via its OpenAI-compatible REST API."""

    def __init__(self) -> None:
        self._endpoint = (
            f"{settings.DATABRICKS_HOST}"
            f"/serving-endpoints/{settings.DATABRICKS_LLM_MODEL}/invocations"
        )
        self._headers = {
            "Authorization": settings.databricks_auth_header,
            "Content-Type": "application/json",
        }

    async def complete(self, prompt: str) -> str:
        """Send a user prompt and return the raw LLM text response."""
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": settings.DATABRICKS_LLM_MAX_TOKENS,
            "temperature": settings.DATABRICKS_LLM_TEMPERATURE,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    self._endpoint,
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise LLMError(
                    f"Databricks LLM returned HTTP {exc.response.status_code}",
                    details={"body": exc.response.text[:500]},
                ) from exc
            except httpx.TimeoutException as exc:
                raise LLMError("Databricks LLM request timed out (120s)") from exc
            except httpx.RequestError as exc:
                raise LLMError(f"Network error calling LLM: {exc}") from exc

        try:
            content: str = response.json()["choices"][0]["message"]["content"]
            return content
        except (KeyError, IndexError) as exc:
            raise LLMError(
                "Unexpected response format from Databricks LLM",
                details={"raw": response.text[:500]},
            ) from exc

    async def complete_json(self, prompt: str) -> dict[str, Any]:
        """Send a prompt and parse the response as JSON."""
        raw = await self.complete(prompt)
        return _parse_json_response(raw)

    def build_enrichment_prompt(
        self,
        cv_text: str,
        job_title: str,
        job_requirements: list[str],
        candidate_name: str = "",
    ) -> str:
        """Build the structured CV enrichment prompt."""
        reqs = ", ".join(job_requirements) if job_requirements else "Not specified"
        name_hint = f"Candidate: {candidate_name}\n" if candidate_name else ""

        return f"""You are an expert CV parser and enrichment system.
Analyze the CV below and return ONLY a valid JSON object — no markdown, no explanation.

### Target Position
- Title: {job_title}
- Required Skills: {reqs}

{name_hint}
### Extract and return exactly these fields:
{{
  "full_name": "string",
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "phone": "string",
  "linkedin": "string",
  "candidate_location": "string (City, Country)",
  "english_level": "A1 | A2 | B1 | B2 | C1 | C2 | Native",
  "current_title": "string",
  "current_company": "string",
  "total_experience": 0.0,
  "technical_skills": ["string"],
  "soft_skills": ["string"],
  "education": [{{"degree": "string", "institution": "string", "years": "string"}}],
  "work_experience": [{{"title": "string", "company": "string", "years": "string", "highlights": ["string"]}}],
  "certifications": [{{"name": "string", "year": "string"}}],
  "courses": [{{"name": "string", "year": "string"}}],
  "summary": "2-3 sentence professional summary tailored to the target position",
  "safety_information": {{
    "red_flags": ["string — unexplained employment gaps > 6 months or date conflicts"],
    "safety_certifications": ["string — OSHA, First Aid, etc."]
  }}
}}

### Rules
- Return ONLY the JSON object. No text before or after.
- Use "" for missing strings, [] for missing arrays, 0.0 for missing numbers.
- Tailor the summary to highlight relevance for: {job_title}
- Map english proficiency to CEFR: Native/Fluent=C1/C2, Intermediate=B1/B2, Basic=A1/A2.

### CV TEXT:
{cv_text}
"""


def _parse_json_response(text: str) -> dict[str, Any]:
    """Strip markdown fences and parse the first JSON object from LLM output."""
    text = text.strip()

    if "```json" in text:
        m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
    elif "```" in text:
        m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)

    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        text = m.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(
            "LLM returned invalid JSON",
            details={"parse_error": str(exc), "snippet": text[:300]},
        ) from exc


# Module-level singleton
databricks_llm = DatabricksLLMClient()
