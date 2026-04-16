"""Parse JSON from Databricks job output logs.

Databricks job logs may contain:
  - Clean JSON output              → {"name": "Alice", ...}
  - RESULT_START/RESULT_END fence  → RESULT_START\\n{...}\\nRESULT_END
  - Markdown code blocks           → ```json\\n{...}\\n```
  - Mixed log lines + JSON         → extract the first { ... } block
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_json_from_logs(logs: str) -> dict[str, Any]:
    """
    Extract and parse a JSON object from raw Databricks job logs.

    Raises:
        ValueError: If no valid JSON can be found or parsed.
    """
    if not logs or not logs.strip():
        raise ValueError("Job produced no output logs")

    text = logs.strip()

    # ── 1. RESULT_START / RESULT_END markers ──────────────────────────────────
    if "RESULT_START" in text and "RESULT_END" in text:
        start = text.find("RESULT_START") + len("RESULT_START")
        end = text.find("RESULT_END")
        text = text[start:end].strip()
        logger.debug("Extracted JSON via RESULT markers")

    # ── 2. ```json ... ``` markdown fence ─────────────────────────────────────
    elif "```json" in text:
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
            logger.debug("Extracted JSON via ```json fence")

    # ── 3. ``` ... ``` generic code fence ─────────────────────────────────────
    elif "```" in text:
        match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
            logger.debug("Extracted JSON via generic ``` fence")

    # ── 4. First { ... } block in the text ────────────────────────────────────
    else:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
            logger.debug("Extracted JSON via brace scan")
        # else: try to parse `text` as-is (maybe it's already clean JSON)

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error(
            "JSON parse failed: %s | first 400 chars: %s",
            exc,
            logs[:400],
        )
        raise ValueError(f"Cannot parse JSON from job output: {exc}") from exc
