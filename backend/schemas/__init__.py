"""
schemas package — Pydantic request/response models for API validation.
"""

from backend.schemas.person import (
    PersonBase,
    PersonCreate,
    PersonUpdate,
    PersonResponse,
    PersonSummary,
    PaginatedPeopleResponse,
    SearchResult,
    SearchResponse,
    RootResponse,
    HealthResponse,
)

__all__ = [
    "PersonBase",
    "PersonCreate",
    "PersonUpdate",
    "PersonResponse",
    "PersonSummary",
    "PaginatedPeopleResponse",
    "SearchResult",
    "SearchResponse",
    "RootResponse",
    "HealthResponse",
]
