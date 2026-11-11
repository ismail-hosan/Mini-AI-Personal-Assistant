"""
services package — business logic layer between API routes and database.
"""

from backend.services.search_service import (
    search_by_name,
    get_person_by_id,
    get_person_by_email,
    get_people_paginated,
    create_person,
    update_person,
    delete_person,
)
from backend.services.assistant_service import answer_question

__all__ = [
    "search_by_name",
    "get_person_by_id",
    "get_person_by_email",
    "get_people_paginated",
    "create_person",
    "update_person",
    "delete_person",
    "answer_question",
]
