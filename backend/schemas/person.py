"""
Pydantic schemas for Person — request validation and response serialization.
These are separate from the ORM models to keep API contracts clean.
"""

from typing import Optional
import re
from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_non_blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        raise ValueError("Value must not be blank.")
    return stripped


def _validate_email_format(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not _EMAIL_RE.match(stripped):
        raise ValueError("Invalid email format.")
    return stripped


# ─── Base Schema ──────────────────────────────────────────────────────────────

class PersonBase(BaseModel):
    """Shared fields used by create, update, and response schemas."""
    first_name: str = Field(..., min_length=1, max_length=100, examples=["John"])
    last_name: str = Field(..., min_length=1, max_length=100, examples=["Smith"])
    full_name: str = Field(..., min_length=1, max_length=200, examples=["John Smith"])
    email: str = Field(..., max_length=200, examples=["john.smith@company.com"])
    phone: Optional[str] = Field(None, examples=["+1-555-123-4567"])
    date_of_birth: Optional[str] = Field(None, examples=["1990-06-15"])
    city: Optional[str] = Field(None, examples=["New York"])
    country: Optional[str] = Field(None, examples=["USA"])
    department: Optional[str] = Field(None, examples=["Engineering"])
    job_title: Optional[str] = Field(None, examples=["Software Engineer"])
    salary: Optional[float] = Field(None, ge=0, examples=[85000.0])
    hire_date: Optional[str] = Field(None, examples=["2020-03-01"])
    education_level: Optional[str] = Field(None, examples=["Master's"])
    education_field: Optional[str] = Field(None, examples=["Computer Science"])
    skills: Optional[str] = Field(None, examples=["Python, SQL, Docker"])
    hobbies: Optional[str] = Field(None, examples=["Reading, Hiking"])
    linkedin: Optional[str] = Field(None, examples=["https://linkedin.com/in/john-smith"])
    notes: Optional[str] = Field(None)

    @field_validator("first_name", "last_name", "full_name")
    @classmethod
    def check_required_non_blank(cls, v: str) -> str:
        return _validate_non_blank(v)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return _validate_email_format(v)


# ─── Create Schema ────────────────────────────────────────────────────────────

class PersonCreate(PersonBase):
    """Schema used when creating a new person (no id required)."""
    pass


# ─── Update Schema ────────────────────────────────────────────────────────────

class PersonUpdate(BaseModel):
    """Schema used for partial updates — all fields are optional."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    salary: Optional[float] = Field(None, ge=0)
    hire_date: Optional[str] = None
    education_level: Optional[str] = None
    education_field: Optional[str] = None
    skills: Optional[str] = None
    hobbies: Optional[str] = None
    linkedin: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("first_name", "last_name", "full_name")
    @classmethod
    def check_optional_non_blank(cls, v: str | None) -> str | None:
        return _validate_non_blank(v)

    @field_validator("email")
    @classmethod
    def check_optional_email(cls, v: str | None) -> str | None:
        return _validate_email_format(v)


# ─── Response Schema ──────────────────────────────────────────────────────────

class PersonResponse(PersonBase):
    """Schema returned by the API — includes the database ID."""
    id: int

    model_config = {"from_attributes": True}


# ─── Search Response ──────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    """A single search result with a match score."""
    person: PersonResponse
    score: float = Field(..., ge=0, le=100, description="Fuzzy match confidence (0-100)")


class SearchResponse(BaseModel):
    """Paginated list of search results."""
    query: str
    total: int
    results: list[SearchResult]


# ─── Summary Schema ───────────────────────────────────────────────────────────

class PersonSummary(BaseModel):
    """Lightweight schema for list views (no heavy fields)."""
    id: int
    full_name: str
    job_title: Optional[str]
    department: Optional[str]
    city: Optional[str]
    country: Optional[str]
    email: str

    model_config = {"from_attributes": True}


class PaginatedPeopleResponse(BaseModel):
    """Paginated response returned by the people listing endpoint."""
    total: int
    skip: int
    limit: int
    results: list[PersonSummary]


class RootResponse(BaseModel):
    """Root status response."""
    status: str
    app: str
    version: str
    docs: str


class HealthResponse(BaseModel):
    """Detailed health check response."""
    status: str
    app: str
    version: str
    database: str
    people_count: int
