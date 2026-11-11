"""
HTTP client for communicating with the FastAPI backend.
All frontend pages use this module instead of calling requests directly.
"""

import os
import requests
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

# Avoid importing settings here since Streamlit has its own env handling
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
API_BASE = f"{BACKEND_URL}/api/v1"

DEFAULT_TIMEOUT = 10  # seconds


def _get(path: str, params: dict | None = None) -> dict | None:
    """Perform a GET request to the backend and return JSON."""
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to backend. Is the API server running?")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def _post(path: str, json: dict) -> dict | None:
    """Perform a POST request to the backend and return JSON."""
    try:
        resp = requests.post(f"{API_BASE}{path}", json=json, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to backend. Is the API server running?")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


# ─── Public API ───────────────────────────────────────────────────────────────

def search_people(query: str, threshold: int = 70, limit: int = 20) -> dict | None:
    """Search people by name via fuzzy matching."""
    return _get("/people/search", params={"q": query, "threshold": threshold, "limit": limit})


def get_person(person_id: int) -> dict | None:
    """Get the full profile of a person by ID."""
    return _get(f"/people/{person_id}")


def list_people(skip: int = 0, limit: int = 50, department: str | None = None, country: str | None = None) -> dict | None:
    """Get a paginated list of people with optional filters."""
    params = {"skip": skip, "limit": limit}
    if department:
        params["department"] = department
    if country:
        params["country"] = country
    return _get("/people/", params=params)


def ask_assistant(question: str) -> dict | None:
    """Send a natural language question to the assistant."""
    return _post("/assistant/ask", json={"question": question})


def health_check() -> dict | None:
    """Check backend health status."""
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None
