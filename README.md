# CV Enrichment Service

A service that enriches CVs based on job descriptions by reordering experience, improving descriptions, and generating professional PDF/DOCX documents.

## Documentation

- **[Proposal](docs/proposal/proposal.md)** - MVP documentation with architecture, tech stack, and Databricks integration details
- **[Recommendation](docs/proposal/recommended.md)** - Analysis of the proposed architecture with cost/effort considerations

## Quick Overview

| Component | Technology |
|-----------|------------|
| API | FastAPI |
| Processing | Databricks (Spark + AI) |
| Storage | PostgreSQL, GCS |
| Output | PDF / DOCX |