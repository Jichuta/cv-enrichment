"""Tests for Pydantic request/response schema validation."""

import pytest
from pydantic import ValidationError

from app.schemas.document import (
    ExperienceItem,
    GenerateCVRequest,
    LanguageItem,
    SkillCategory,
)
from app.schemas.enrich import (
    DirectEnrichRequest,
    EnrichCVRequest,
    JobDescription,
)


# ── EnrichCVRequest ───────────────────────────────────────────────────────────


def test_enrich_request_accepts_camel_case() -> None:
    data = EnrichCVRequest.model_validate(
        {
            "jobDescription": {"title": "Python Developer"},
            "greenhouseParseData": {
                "candidateId": "42",
                "firstName": "Jane",
                "lastName": "Doe",
            },
            "jsonCvTextExtracted": {"rawText": "5 years of Python..."},
        }
    )
    assert data.job_description.title == "Python Developer"
    assert data.greenhouse_parse_data.candidate_id == "42"


def test_enrich_request_requires_job_title() -> None:
    with pytest.raises(ValidationError):
        JobDescription.model_validate({})


def test_direct_enrich_requires_cv_text_and_job_title() -> None:
    with pytest.raises(ValidationError):
        DirectEnrichRequest.model_validate({"cv_text": "some text"})


def test_direct_enrich_rejects_short_cv_text() -> None:
    with pytest.raises(ValidationError):
        DirectEnrichRequest.model_validate({"cv_text": "short", "job_title": "Dev"})


def test_direct_enrich_valid() -> None:
    req = DirectEnrichRequest(
        cv_text="A" * 20,
        job_title="Software Engineer",
        job_requirements=["Python", "FastAPI"],
    )
    assert req.job_title == "Software Engineer"
    assert len(req.job_requirements) == 2


# ── GenerateCVRequest ─────────────────────────────────────────────────────────


def test_generate_cv_request_accepts_camel_case() -> None:
    data = GenerateCVRequest.model_validate(
        {
            "candidateName": "Jane Doe",
            "position": "Backend Engineer",
            "availability": "Immediate",
            "summary": "Experienced backend developer.",
        }
    )
    assert data.candidate_name == "Jane Doe"


def test_generate_cv_request_requires_candidate_name() -> None:
    with pytest.raises(ValidationError):
        GenerateCVRequest.model_validate(
            {"position": "Dev", "availability": "Now", "summary": "Summary"}
        )


def test_experience_item_defaults() -> None:
    exp = ExperienceItem(company="Acme", period="2020–2023")
    assert exp.summary == ""
    assert exp.achievements == []
    assert exp.position is None


def test_language_item_camel_alias() -> None:
    lang = LanguageItem.model_validate(
        {
            "name": "Spanish",
            "level": "Advanced",
            "availableLevels": ["Basic", "Advanced"],
        }
    )
    assert lang.available_levels == ["Basic", "Advanced"]


def test_skill_category_defaults_to_empty_items() -> None:
    skill = SkillCategory(area="Backend")
    assert skill.items == []
