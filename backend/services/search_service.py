"""
Search service — fuzzy name matching and database query logic.
Uses RapidFuzz to handle typos, partial names, and nicknames gracefully.
"""

from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from backend.models.person import Person
from backend.schemas.person import SearchResult, PersonResponse
from backend.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _person_to_response(person: Person) -> PersonResponse:
    """Convert a Person ORM instance to a PersonResponse Pydantic model."""
    return PersonResponse.model_validate(person)


def search_by_name(
    query: str,
    db: Session,
    threshold: int | None = None,
    limit: int | None = None,
) -> list[SearchResult]:
    """
    Search for people by name using fuzzy matching.

    Strategy:
    1. First, do a fast SQL LIKE query to narrow candidates.
    2. Then score all candidates with RapidFuzz and filter by threshold.
    3. Return results sorted by score (best match first).

    Args:
        query: The name string to search for.
        db: SQLAlchemy database session.
        threshold: Minimum fuzzy match score (0-100). Defaults to settings value.
        limit: Maximum number of results to return. Defaults to settings value.

    Returns:
        List of SearchResult ordered by match score descending.
    """
    if not query or not query.strip():
        return []

    if threshold is None:
        threshold = settings.fuzzy_match_threshold
    if limit is None:
        limit = settings.max_search_results
    query = query.strip()

    # Step 1: Broad SQL LIKE filter to reduce the candidate pool
    like_pattern = f"%{query}%"
    candidates: list[Person] = (
        db.query(Person)
        .filter(
            or_(
                Person.full_name.ilike(like_pattern),
                Person.first_name.ilike(like_pattern),
                Person.last_name.ilike(like_pattern),
            )
        )
        .all()
    )

    # Step 2: If LIKE found nothing, do a full scan with fuzzy scoring
    if not candidates:
        candidates = db.query(Person).all()

    logger.debug(f"Fuzzy search: '{query}' → {len(candidates)} candidates")

    # Step 3: Score each candidate against the query
    results: list[SearchResult] = []
    for person in candidates:
        score = fuzz.WRatio(query.lower(), person.full_name.lower())
        if score >= threshold:
            results.append(
                SearchResult(
                    person=_person_to_response(person),
                    score=round(score, 2),
                )
            )

    # Sort by score descending, limit results
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]


def get_person_by_id(person_id: int, db: Session) -> Person | None:
    """
    Retrieve a single person by their database ID.

    Args:
        person_id: The person's primary key.
        db: SQLAlchemy database session.

    Returns:
        Person ORM instance or None if not found.
    """
    return db.query(Person).filter(Person.id == person_id).first()


def get_person_by_email(email: str, db: Session) -> Person | None:
    """
    Retrieve a single person by email (case-insensitive).

    Args:
        email: Email address to look up.
        db: SQLAlchemy database session.

    Returns:
        Person ORM instance or None if not found.
    """
    return db.query(Person).filter(func.lower(Person.email) == email.strip().lower()).first()


def get_people_paginated(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    department: str | None = None,
    country: str | None = None,
) -> tuple[list[Person], int]:
    """
    Retrieve people with optional filtering and pagination.

    Args:
        db: SQLAlchemy database session.
        skip: Number of records to skip (offset).
        limit: Maximum records to return.
        department: Optional department filter.
        country: Optional country filter.

    Returns:
        Tuple of (list of Person instances, total count).
    """
    query = db.query(Person)

    if department and department.strip():
        query = query.filter(Person.department.ilike(f"%{department.strip()}%"))
    if country and country.strip():
        query = query.filter(Person.country.ilike(f"%{country.strip()}%"))

    total = query.count()
    people = query.order_by(Person.id).offset(skip).limit(limit).all()
    return people, total


def create_person(data: dict, db: Session) -> Person:
    """
    Insert a new Person record into the database.

    Args:
        data: Dict of person fields.
        db: SQLAlchemy database session.

    Returns:
        The newly created Person ORM instance.
    """
    person = Person(**data)
    db.add(person)
    db.commit()
    db.refresh(person)
    logger.info(f"Created person: {person.full_name} (id={person.id})")
    return person


def update_person(person: Person, data: dict, db: Session) -> Person:
    """
    Apply partial updates to an existing Person record.

    Args:
        person: Existing Person ORM instance.
        data: Dict of fields to update (only non-None values applied).
        db: SQLAlchemy database session.

    Returns:
        Updated Person ORM instance.
    """
    for field, value in data.items():
        if value is not None:
            setattr(person, field, value)
    db.commit()
    db.refresh(person)
    logger.info(f"Updated person id={person.id}")
    return person


def delete_person(person: Person, db: Session) -> None:
    """
    Delete a Person record from the database.

    Args:
        person: Person ORM instance to delete.
        db: SQLAlchemy database session.
    """
    db.delete(person)
    db.commit()
    logger.info(f"Deleted person id={person.id} name='{person.full_name}'")
