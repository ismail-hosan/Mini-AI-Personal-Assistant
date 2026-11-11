"""
Unit tests for service-layer functions (search, assistant).
These tests run against an in-memory SQLite DB without HTTP overhead.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.session import Base
from backend.models.person import Person
from backend.services.search_service import search_by_name, get_people_paginated
from backend.services.assistant_service import answer_question, _detect_intent, _format_person

# ─── In-Memory DB Fixture ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Seed test data
    db.add_all([
        Person(
            first_name="Emma", last_name="Brown", full_name="Emma Brown",
            email="emma.brown@test.com", city="London", country="UK",
            department="Data Science", job_title="Data Scientist", salary=90000,
            skills="Python, Machine Learning, SQL", hobbies="Chess, Painting",
        ),
        Person(
            first_name="Liam", last_name="Wilson", full_name="Liam Wilson",
            email="liam.wilson@test.com", city="Sydney", country="Australia",
            department="Sales", job_title="Sales Director", salary=120000,
            skills="Negotiation, Excel, Salesforce", hobbies="Surfing, Running",
        ),
        Person(
            first_name="Sophia", last_name="Garcia", full_name="Sophia Garcia",
            email="sophia.garcia@test.com", city="Toronto", country="Canada",
            department="Engineering", job_title="Senior Engineer", salary=115000,
            skills="Python, AWS, Docker", hobbies="Hiking, Photography",
        ),
    ])
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


# ─── Intent Detection Tests ───────────────────────────────────────────────────

class TestIntentDetection:
    def test_count_intent(self):
        intent, _ = _detect_intent("How many people are there?")
        assert intent == "count"

    def test_count_intent_variant(self):
        intent, _ = _detect_intent("What is the total number of employees?")
        assert intent == "count"

    def test_department_intent(self):
        intent, value = _detect_intent("Who works in Engineering?")
        assert intent == "find_by_department"
        assert "engineering" in value.lower()

    def test_location_intent(self):
        intent, value = _detect_intent("Who lives in London?")
        assert intent == "find_by_location"
        assert "london" in value.lower()

    def test_skill_intent(self):
        intent, value = _detect_intent("Who has Python skills?")
        assert intent == "find_by_skill"
        assert "python" in value.lower()

    def test_find_person_intent(self):
        intent, value = _detect_intent("Tell me about Emma Brown")
        assert intent == "find_person"
        assert "emma brown" in value.lower()

    def test_find_someone_in_department_intent(self):
        intent, value = _detect_intent("Find someone in Data Science")
        assert intent == "find_by_department"
        assert value == "Data Science"

    def test_find_someone_in_location_intent(self):
        intent, value = _detect_intent("Find someone in London")
        assert intent == "find_by_location"
        assert value.lower() == "london"

    def test_italy_not_confused_with_it_department(self):
        intent, value = _detect_intent("Who works in Italy?")
        assert intent == "find_by_location"
        assert value == "Italy"

    def test_skill_without_trailing_word(self):
        intent, value = _detect_intent("Who knows Python?")
        assert intent == "find_by_skill"
        assert value == "Python"

        intent2, value2 = _detect_intent("Who knows Node.js?")
        assert intent2 == "find_by_skill"
        assert value2 == "Node.js"

    def test_list_all_intent(self):
        intent, _ = _detect_intent("Show me all people")
        assert intent == "list_all"


# ─── Search Service Tests ─────────────────────────────────────────────────────

class TestSearchService:
    def test_exact_name_match(self, db_session):
        results = search_by_name("Emma Brown", db_session)
        assert len(results) >= 1
        assert results[0].person.full_name == "Emma Brown"
        assert results[0].score >= 90

    def test_partial_first_name(self, db_session):
        results = search_by_name("Sophia", db_session, threshold=50)
        assert any(r.person.first_name == "Sophia" for r in results)

    def test_fuzzy_typo_tolerance(self, db_session):
        # "Wlison" (typo for "Wilson") should still match Liam Wilson
        results = search_by_name("Liam Wlison", db_session, threshold=50)
        assert len(results) >= 1

    def test_empty_query_returns_empty(self, db_session):
        results = search_by_name("", db_session)
        assert results == []

    def test_below_threshold_excluded(self, db_session):
        results = search_by_name("ZZZNOMATCH", db_session, threshold=99)
        assert results == []

    def test_zero_threshold_returns_results(self, db_session):
        results = search_by_name("Emma", db_session, threshold=0, limit=10)
        assert len(results) >= 1


# ─── Pagination Tests ─────────────────────────────────────────────────────────

class TestPagination:
    def test_get_all_people(self, db_session):
        people, total = get_people_paginated(db_session, skip=0, limit=10)
        assert total == 3
        assert len(people) == 3

    def test_pagination_offset(self, db_session):
        people, total = get_people_paginated(db_session, skip=2, limit=10)
        assert len(people) == 1

    def test_department_filter(self, db_session):
        people, total = get_people_paginated(db_session, department="Engineering")
        assert total == 1
        assert people[0].department == "Engineering"

    def test_country_filter(self, db_session):
        people, total = get_people_paginated(db_session, country="Canada")
        assert total == 1
        assert people[0].country == "Canada"


# ─── Assistant Service Tests ──────────────────────────────────────────────────

class TestAssistantService:
    def test_count_answer(self, db_session):
        result = answer_question("How many people are in the system?", db_session)
        assert result["intent"] == "count"
        assert "3" in result["answer"]

    def test_department_answer(self, db_session):
        result = answer_question("Who works in Sales?", db_session)
        assert result["intent"] == "find_by_department"
        assert len(result["people"]) >= 1

    def test_location_answer(self, db_session):
        result = answer_question("Who lives in London?", db_session)
        assert result["intent"] == "find_by_location"
        assert any(p.city == "London" for p in result["people"])

    def test_skill_answer(self, db_session):
        result = answer_question("Who has Python skills?", db_session)
        assert result["intent"] == "find_by_skill"
        assert len(result["people"]) >= 1

    def test_person_lookup(self, db_session):
        result = answer_question("Tell me about Emma Brown", db_session)
        assert "Emma Brown" in result["answer"]

    def test_count_filtered_by_department(self, db_session):
        result = answer_question("How many people are in Sales?", db_session)
        assert result["intent"] == "count"
        assert result["query_value"] == "Sales"
        assert "**1**" in result["answer"]

    def test_count_filtered_by_location(self, db_session):
        result = answer_question("How many people live in London?", db_session)
        assert result["intent"] == "count"
        assert "**1**" in result["answer"]

    def test_count_filtered_by_skill(self, db_session):
        result = answer_question("How many people have Python skills?", db_session)
        assert result["intent"] == "count"
        assert "**2**" in result["answer"]

    def test_format_person_handles_none_fields(self):
        minimal = Person(
            first_name="Test", last_name="User", full_name="Test User",
            email="test.user@example.com",
        )
        formatted = _format_person(minimal)
        assert "None" not in formatted
        assert "Location: N/A" in formatted
        assert "Education: N/A" in formatted
