"""
Assistant API router — natural language Q&A endpoint.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator

from backend.database.session import get_db
from backend.services.assistant_service import answer_question
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/assistant", tags=["Assistant"])


class QuestionRequest(BaseModel):
    """Request body for a question to the assistant."""
    question: str = Field(
        ...,
        min_length=1,
        description="Natural language question about people in the database",
        examples=["Who works in Engineering?"],
    )

    @field_validator("question")
    @classmethod
    def check_non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Question must not be blank.")
        return stripped


class QuestionResponse(BaseModel):
    """Response from the assistant."""
    question: str
    answer: str
    intent: str
    query_value: str | None
    people_count: int


@router.post("/ask", response_model=QuestionResponse, summary="Ask the AI assistant a question")
def ask_assistant(payload: QuestionRequest, db: Session = Depends(get_db)):
    """
    Ask a natural language question about people in the database.

    Example questions:
    - "Tell me about John Smith"
    - "Who works in Engineering?"
    - "Who lives in New York?"
    - "How many people are in the system?"
    - "Show me people with Python skills"
    """
    result = answer_question(question=payload.question, db=db)
    return QuestionResponse(
        question=payload.question,
        answer=result["answer"],
        intent=result["intent"],
        query_value=result.get("query_value"),
        people_count=len(result.get("people", [])),
    )


@router.get("/ask", response_model=QuestionResponse, summary="Ask via GET (for quick testing)")
def ask_assistant_get(
    q: str = Query(..., min_length=1, description="The question to ask"),
    db: Session = Depends(get_db),
):
    """GET version of /ask for easy testing in the browser/Swagger UI."""
    result = answer_question(question=q, db=db)
    return QuestionResponse(
        question=q,
        answer=result["answer"],
        intent=result["intent"],
        query_value=result.get("query_value"),
        people_count=len(result.get("people", [])),
    )
