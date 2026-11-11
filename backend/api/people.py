"""
People API router — CRUD and fuzzy search endpoints for person records.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.person import (
    PersonCreate,
    PersonUpdate,
    PersonResponse,
    PersonSummary,
    PaginatedPeopleResponse,
    SearchResponse,
    SearchResult,
)
from backend.services.search_service import (
    search_by_name,
    get_person_by_id,
    get_person_by_email,
    get_people_paginated,
    create_person,
    update_person,
    delete_person,
)
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/people", tags=["People"])


# ─── Search ───────────────────────────────────────────────────────────────────

@router.get("/search", response_model=SearchResponse, summary="Fuzzy name search")
def search_people(
    q: str = Query(..., min_length=1, description="Name or partial name to search"),
    threshold: int = Query(70, ge=0, le=100, description="Minimum fuzzy match score"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    db: Session = Depends(get_db),
):
    """
    Search for people by name using fuzzy matching (RapidFuzz).
    Returns ranked results with match confidence scores.
    """
    results: list[SearchResult] = search_by_name(
        query=q, db=db, threshold=threshold, limit=limit
    )
    return SearchResponse(query=q, total=len(results), results=results)


# ─── List All ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=PaginatedPeopleResponse, summary="List people with pagination")
def list_people(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Records to return"),
    department: str | None = Query(None, description="Filter by department"),
    country: str | None = Query(None, description="Filter by country"),
    db: Session = Depends(get_db),
):
    """
    Retrieve a paginated list of people with optional filters.
    """
    people, total = get_people_paginated(
        db=db, skip=skip, limit=limit, department=department, country=country
    )
    return PaginatedPeopleResponse(
        total=total,
        skip=skip,
        limit=limit,
        results=[PersonSummary.model_validate(p) for p in people],
    )


# ─── Get by ID ────────────────────────────────────────────────────────────────

@router.get(
    "/{person_id}",
    response_model=PersonResponse,
    summary="Get person by ID",
    responses={404: {"description": "Person not found"}},
)
def get_person(person_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the full profile of a person by their database ID.
    """
    person = get_person_by_id(person_id, db)
    if not person:
        raise HTTPException(status_code=404, detail=f"Person with id={person_id} not found.")
    return PersonResponse.model_validate(person)


# ─── Create ───────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=PersonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new person",
    responses={409: {"description": "A person with this email already exists"}},
)
def create_new_person(payload: PersonCreate, db: Session = Depends(get_db)):
    """
    Add a new person record to the database.
    """
    if get_person_by_email(payload.email, db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Person with email '{payload.email}' already exists.",
        )
    try:
        person = create_person(data=payload.model_dump(), db=db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Person with email '{payload.email}' already exists.",
        )
    return PersonResponse.model_validate(person)


# ─── Update ───────────────────────────────────────────────────────────────────

@router.patch(
    "/{person_id}",
    response_model=PersonResponse,
    summary="Partially update a person",
    responses={
        404: {"description": "Person not found"},
        409: {"description": "A person with this email already exists"},
    },
)
def patch_person(person_id: int, payload: PersonUpdate, db: Session = Depends(get_db)):
    """
    Apply partial updates to an existing person record.
    Only provided fields will be updated.
    """
    person = get_person_by_id(person_id, db)
    if not person:
        raise HTTPException(status_code=404, detail=f"Person with id={person_id} not found.")

    update_data = payload.model_dump(exclude_none=True)
    if "email" in update_data:
        existing = get_person_by_email(update_data["email"], db)
        if existing and existing.id != person_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Person with email '{update_data['email']}' already exists.",
            )

    try:
        updated = update_person(person=person, data=update_data, db=db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists.",
        )
    return PersonResponse.model_validate(updated)


# ─── Delete ───────────────────────────────────────────────────────────────────

@router.delete(
    "/{person_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a person",
    responses={404: {"description": "Person not found"}},
)
def remove_person(person_id: int, db: Session = Depends(get_db)):
    """
    Permanently delete a person record by ID.
    """
    person = get_person_by_id(person_id, db)
    if not person:
        raise HTTPException(status_code=404, detail=f"Person with id={person_id} not found.")
    delete_person(person=person, db=db)
