"""
Test suite for FastAPI people and assistant endpoints.
Uses pytest + httpx TestClient for fast in-process testing.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database.session import get_db, Base
from backend.models.person import Person

# ─── Test Database Setup ──────────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    """Set up a test client with a fresh in-memory test database."""
    Base.metadata.create_all(bind=test_engine)

    # Insert test data
    db = TestSessionLocal()
    db.add_all([
        Person(
            first_name="Alice", last_name="Johnson", full_name="Alice Johnson",
            email="alice.johnson@test.com", phone="+1-555-001-0001",
            city="New York", country="USA", department="Engineering",
            job_title="Software Engineer", salary=95000,
            hire_date="2021-03-15", date_of_birth="1990-07-20",
            education_level="Master's", education_field="Computer Science",
            skills="Python, Docker, SQL", hobbies="Reading, Hiking",
            linkedin="https://linkedin.com/in/alice-johnson",
            notes="Test record.",
        ),
        Person(
            first_name="Bob", last_name="Martinez", full_name="Bob Martinez",
            email="bob.martinez@test.com", phone="+1-555-002-0002",
            city="Los Angeles", country="USA", department="Marketing",
            job_title="Marketing Manager", salary=75000,
            hire_date="2019-06-01", date_of_birth="1985-11-03",
            education_level="Bachelor's", education_field="Marketing",
            skills="SEO, Excel, Tableau", hobbies="Gaming, Cooking",
            linkedin="https://linkedin.com/in/bob-martinez",
            notes="Test record.",
        ),
        Person(
            first_name="Carol", last_name="Smith", full_name="Carol Smith",
            email="carol.smith@test.com", phone="+1-555-003-0003",
            city="Chicago", country="USA", department="Engineering",
            job_title="DevOps Engineer", salary=105000,
            hire_date="2022-01-10", date_of_birth="1993-04-15",
            education_level="Bachelor's", education_field="Computer Science",
            skills="Kubernetes, Docker, AWS", hobbies="Cycling, Photography",
            linkedin="https://linkedin.com/in/carol-smith",
            notes="Test record.",
        ),
    ])
    db.commit()
    db.close()

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("backend.main.init_db", lambda: Base.metadata.create_all(bind=test_engine)),
        patch("backend.main.SessionLocal", TestSessionLocal),
        TestClient(app) as c,
    ):
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


# ─── Health Check Tests ───────────────────────────────────────────────────────

class TestHealth:
    def test_root_returns_ok(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["people_count"] == 3

    def test_docs_and_openapi_schema(self, client):
        docs_resp = client.get("/docs")
        assert docs_resp.status_code == 200
        redoc_resp = client.get("/redoc")
        assert redoc_resp.status_code == 200
        openapi_resp = client.get("/openapi.json")
        assert openapi_resp.status_code == 200
        schemas = openapi_resp.json()["components"]["schemas"]
        assert "PaginatedPeopleResponse" in schemas
        assert "HealthResponse" in schemas
        assert "RootResponse" in schemas


# ─── People Endpoint Tests ────────────────────────────────────────────────────

class TestPeopleList:
    def test_list_people(self, client):
        resp = client.get("/api/v1/people/")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "total" in data
        assert data["total"] >= 3

    def test_list_with_department_filter(self, client):
        resp = client.get("/api/v1/people/?department=Engineering")
        assert resp.status_code == 200
        data = resp.json()
        for person in data["results"]:
            assert "engineering" in person["department"].lower()


class TestPeopleSearch:
    def test_search_exact_name(self, client):
        resp = client.get("/api/v1/people/search?q=Alice+Johnson")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["results"][0]["person"]["full_name"] == "Alice Johnson"

    def test_search_partial_name(self, client):
        resp = client.get("/api/v1/people/search?q=carol")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_search_no_results(self, client):
        resp = client.get("/api/v1/people/search?q=XXXXXXNONEXISTENT")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    def test_search_missing_query(self, client):
        resp = client.get("/api/v1/people/search")
        assert resp.status_code == 422  # Validation error

    def test_search_zero_threshold_respected(self, client):
        resp = client.get("/api/v1/people/search?q=Alice&threshold=0")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


class TestPeopleGetById:
    def test_get_existing_person(self, client):
        # First get a valid ID
        list_resp = client.get("/api/v1/people/")
        first_id = list_resp.json()["results"][0]["id"]
        resp = client.get(f"/api/v1/people/{first_id}")
        assert resp.status_code == 200
        assert "full_name" in resp.json()

    def test_get_nonexistent_person(self, client):
        resp = client.get("/api/v1/people/999999")
        assert resp.status_code == 404


class TestPeopleCRUD:
    def test_create_person(self, client):
        payload = {
            "first_name": "Dave",
            "last_name": "Lee",
            "full_name": "Dave Lee",
            "email": "dave.lee@test.com",
            "department": "Design",
            "job_title": "UX Designer",
        }
        resp = client.post("/api/v1/people/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["full_name"] == "Dave Lee"
        assert "id" in data

    def test_create_duplicate_email_returns_409(self, client):
        payload = {
            "first_name": "Alice",
            "last_name": "Clone",
            "full_name": "Alice Clone",
            "email": "alice.johnson@test.com",
        }
        resp = client.post("/api/v1/people/", json=payload)
        assert resp.status_code == 409

    def test_create_invalid_email_returns_422(self, client):
        payload = {
            "first_name": "Bad",
            "last_name": "Email",
            "full_name": "Bad Email",
            "email": "not-an-email",
        }
        resp = client.post("/api/v1/people/", json=payload)
        assert resp.status_code == 422

    def test_update_person(self, client):
        list_resp = client.get("/api/v1/people/")
        first_id = list_resp.json()["results"][0]["id"]
        resp = client.patch(f"/api/v1/people/{first_id}", json={"job_title": "Senior Engineer"})
        assert resp.status_code == 200
        assert resp.json()["job_title"] == "Senior Engineer"

    def test_update_duplicate_email_returns_409(self, client):
        list_resp = client.get("/api/v1/people/")
        first_id = list_resp.json()["results"][0]["id"]
        second_email = list_resp.json()["results"][1]["email"]
        resp = client.patch(f"/api/v1/people/{first_id}", json={"email": second_email})
        assert resp.status_code == 409

    def test_update_negative_salary_returns_422(self, client):
        list_resp = client.get("/api/v1/people/")
        first_id = list_resp.json()["results"][0]["id"]
        resp = client.patch(f"/api/v1/people/{first_id}", json={"salary": -500})
        assert resp.status_code == 422

    def test_delete_person(self, client):
        # Create then delete
        create_resp = client.post("/api/v1/people/", json={
            "first_name": "Temp", "last_name": "User", "full_name": "Temp User",
            "email": "temp.delete@test.com",
        })
        person_id = create_resp.json()["id"]
        del_resp = client.delete(f"/api/v1/people/{person_id}")
        assert del_resp.status_code == 204
        get_resp = client.get(f"/api/v1/people/{person_id}")
        assert get_resp.status_code == 404


# ─── Assistant Endpoint Tests ─────────────────────────────────────────────────

class TestAssistant:
    def test_ask_count_question(self, client):
        resp = client.post("/api/v1/assistant/ask", json={"question": "How many people are there?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert data["intent"] == "count"

    def test_ask_department_question(self, client):
        resp = client.post("/api/v1/assistant/ask", json={"question": "Who works in Engineering?"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "find_by_department"
        assert data["people_count"] >= 1

    def test_ask_person_question(self, client):
        resp = client.post("/api/v1/assistant/ask", json={"question": "Tell me about Alice Johnson"})
        assert resp.status_code == 200
        data = resp.json()
        assert "Alice" in data["answer"]

    def test_ask_get_endpoint(self, client):
        resp = client.get("/api/v1/assistant/ask?q=How+many+people")
        assert resp.status_code == 200
        assert "answer" in resp.json()

    def test_ask_blank_question_returns_422(self, client):
        resp = client.post("/api/v1/assistant/ask", json={"question": "   "})
        assert resp.status_code == 422

    def test_ask_find_someone_in_department(self, client):
        resp = client.post("/api/v1/assistant/ask", json={"question": "Find someone in Engineering"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "find_by_department"
        assert data["people_count"] >= 1

    def test_ask_list_all_people(self, client):
        resp = client.post("/api/v1/assistant/ask", json={"question": "Show me all people"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "list_all"
        assert data["people_count"] >= 3

    def test_ask_count_with_department(self, client):
        resp = client.post("/api/v1/assistant/ask", json={"question": "How many people are in Engineering?"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "count"
        assert data["query_value"] == "Engineering"
        assert "2" in data["answer"]

    def test_ask_who_knows_skill(self, client):
        resp = client.post("/api/v1/assistant/ask", json={"question": "Who knows Python?"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "find_by_skill"
        assert data["people_count"] >= 1
