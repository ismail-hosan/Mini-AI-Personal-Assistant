"""
api package — FastAPI route handlers.
"""

from backend.api.people import router as people_router
from backend.api.assistant import router as assistant_router

__all__ = ["people_router", "assistant_router"]
