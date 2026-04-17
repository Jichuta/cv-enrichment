"""Pydantic models for CV document generation."""

from pydantic import BaseModel, ConfigDict, Field


class ExperienceItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    company: str
    position: str | None = None
    period: str
    summary: str = ""
    achievements: list[str] = []


class EducationItem(BaseModel):
    degree: str
    location: str
    year: str


class CertificationItem(BaseModel):
    name: str
    institution: str
    year: str


class SkillCategory(BaseModel):
    """A named group of skills, e.g. { area: 'Programming Languages', items: ['Python', 'Node.js'] }"""
    area: str
    items: list[str] = []


class LanguageItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    level: str
    available_levels: list[str] = Field(default=[], alias="availableLevels")


class GenerateCVRequest(BaseModel):
    """Request body for POST /api/v1/cv/generate-document."""

    model_config = ConfigDict(populate_by_name=True)

    candidate_name: str = Field(alias="candidateName")
    position: str
    availability: str
    summary: str
    experience: list[ExperienceItem] = []
    education: list[EducationItem] = []
    certifications: list[CertificationItem] = []
    skills: list[SkillCategory] = []
    languages: list[LanguageItem] = []
