"""
Assistant service — natural language question answering about people.

Parses free-text questions like:
  "Who works in Engineering?"
  "Tell me about John Smith"
  "Who lives in New York?"
  "How many people are in Sales?"
  "Show me developers with Python skills"

No ML model is used — pure rule-based NLP with keyword/pattern matching.
"""

import re
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from backend.models.person import Person
from backend.services.search_service import search_by_name
from backend.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ─── Intent Detection ─────────────────────────────────────────────────────────

INTENT_PATTERNS = {
    "count": [
        r"\bhow many\b",
        r"\bcount\b",
        r"\bnumber of\b",
        r"\btotal\b",
    ],
    "find_by_department": [
        r"\bwho (?:works?|is) in (?:the )?(\w[\w\s&.-]+?)\s+(?:department|team|division)\b",
        r"\b(?:show|list|find) (?:me )?(?:all )?(?:people|employees|staff|persons?|someone|anyone|anybody) (?:in|from|at) (?:the )?(\w[\w\s&.-]+?)\s+(?:department|team|division)\b",
        r"\b(\w[\w\s&.-]+?) (?:department|team|division) (?:staff|employees|people|members)\b",
    ],
    "find_by_location": [
        r"\bwho (?:lives?|is located|is based|is from) (?:in|at|from) ([\w\s.-]+)$",
        r"\b(?:people|employees|staff) (?:living|located|based) (?:in|at) ([\w\s.-]+)$",
        r"\bwho is from ([\w\s.-]+)$",
    ],
    "find_by_skill": [
        r"\bwho has (?:skills?|experience|expertise) in ([\w\s+#.-]+)$",
        r"\bwho (?:knows?|has|uses?|can(?: use)?) ([\w\s+#.-]+?)(?: (?:skills?|experience|knowledge|expertise))?$",
        r"\b(?:(?:show|find|list) (?:me )?)?(?:people|employees|developers?|engineers?|staff|someone|anyone) with ([\w\s+#.-]+?)(?: (?:skills?|experience|knowledge|expertise))?$",
        r"\b([\w\s+#.-]+?) (?:developers?|engineers?|specialists?|experts?)$",
    ],
    "list_all": [
        r"\b(?:show|list|display) (?:me )?(?:all|every)(?: (?:the )?(?:people|employees|staff|persons?)|one|body)?$",
        r"\bwho (?:are|do we have|do you have)(?: in(?: the)? system)?$",
    ],
    "find_person": [
        r"\btell me about (.+)",
        r"\bwho is (.+)",
        r"\bshow me (.+)",
        r"\bfind (.+)",
        r"\bsearch for (.+)",
        r"\blook up (.+)",
        r"\binfo (?:on|about|for) (.+)",
        r"\bdetails (?:on|about|for) (.+)",
    ],
}

DEPARTMENTS = [
    "Engineering", "Marketing", "Sales", "Human Resources", "Finance",
    "Operations", "Legal", "Research & Development", "Customer Support",
    "Product Management", "Design", "Data Science", "IT", "Procurement",
]
KNOWN_DEPARTMENTS = {d.lower(): d for d in DEPARTMENTS}
DEPARTMENT_ALIASES = {
    "hr": "Human Resources",
    "r&d": "Research & Development",
    "rd": "Research & Development",
    "support": "Customer Support",
    "product": "Product Management",
}
_UNFILTERED_COUNT_TARGETS = {
    "system", "the system", "database", "the database", "db", "total", "company", "all",
}


def _resolve_department(value: str) -> str | None:
    """Return canonical department name if value refers to a department, else None."""
    cleaned = re.sub(r"\s+(?:department|team|division)$", "", value.strip(), flags=re.IGNORECASE).strip()
    lower = cleaned.lower()
    if lower in DEPARTMENT_ALIASES:
        return DEPARTMENT_ALIASES[lower]
    if lower in KNOWN_DEPARTMENTS:
        return KNOWN_DEPARTMENTS[lower]
    if len(lower) >= 4:
        for dept_lower, canonical in KNOWN_DEPARTMENTS.items():
            if lower in dept_lower:
                return canonical
    return None


def _detect_count_target(q: str) -> tuple[str, str] | None:
    """Extract optional (filter_kind, filter_value) from a count question."""
    skill_match = re.search(
        r"\b(?:people|employees|staff|developers?|engineers?) (?:who )?(?:have|know|knows|use|uses|with) ([\w\s+#.-]+?)(?: (?:skills?|experience|knowledge|expertise))?$",
        q,
        re.IGNORECASE,
    )
    if skill_match:
        return "skill", skill_match.group(1).strip()

    loc_match = re.search(
        r"\b(?:people|employees|staff|persons?) (?:who )?(?:live|lives|are based|are located|based|located) (?:in|at|from) (?:the )?([\w\s.-]+)$",
        q,
        re.IGNORECASE,
    )
    if loc_match:
        return "location", loc_match.group(1).strip()

    in_match = re.search(
        r"\b(?:people|employees|staff|persons?) (?:who )?(?:are |work |working )?(?:in|from|at) (?:the )?([\w\s&.-]+)$",
        q,
        re.IGNORECASE,
    )
    if in_match:
        val = in_match.group(1).strip()
        if val.lower() in _UNFILTERED_COUNT_TARGETS:
            return None
        dept = _resolve_department(val)
        if dept:
            return "department", dept
        if re.search(r"\b(?:department|team|division)$", val, re.IGNORECASE):
            clean = re.sub(r"\s+(?:department|team|division)$", "", val, flags=re.IGNORECASE).strip()
            return "department", clean
        return "location", val

    return None


def _detect_intent(question: str) -> tuple[str, str | None]:
    """
    Detect the intent of a natural language question.

    Returns:
        Tuple of (intent_name, extracted_value).
        extracted_value is the department/city/skill/name captured from the pattern.
    """
    q = re.sub(r"[?!.,]+$", "", question.strip()).strip()

    # 1. Count queries
    for pattern in INTENT_PATTERNS["count"]:
        if re.search(pattern, q, re.IGNORECASE):
            target = _detect_count_target(q)
            return "count", target[1] if target else None

    # 2. Explicit Department patterns (e.g. "in Engineering department")
    for pattern in INTENT_PATTERNS["find_by_department"]:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            value = match.group(1).strip() if match.lastindex else None
            if value:
                value = _resolve_department(value) or value
            return "find_by_department", value

    # 3. Explicit Location queries (who lives in / based in / located in / from)
    for pattern in INTENT_PATTERNS["find_by_location"]:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            value = match.group(1).strip() if match.lastindex else None
            return "find_by_location", value

    # 4. General "in / from / at <X>" queries — disambiguate department vs location
    general_in_patterns = [
        r"\bwho (?:works?|is) in (?:the )?([\w\s&.-]+)$",
        r"\b(?:show|list|find) (?:me )?(?:all )?(?:people|employees|staff|persons?|someone|anyone|anybody) (?:in|from|at) (?:the )?([\w\s&.-]+)$",
        r"\b(?:people|employees|staff|persons?) (?:in|from|at) (?:the )?([\w\s&.-]+)$",
    ]
    for pattern in general_in_patterns:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            dept = _resolve_department(val)
            if dept:
                return "find_by_department", dept
            return "find_by_location", val

    # 5. Skills
    for pattern in INTENT_PATTERNS["find_by_skill"]:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            value = match.group(1).strip() if match.lastindex else None
            return "find_by_skill", value

    # 6. List all (must run before generic "show me <person>" pattern)
    for pattern in INTENT_PATTERNS["list_all"]:
        if re.search(pattern, q, re.IGNORECASE):
            return "list_all", None

    # 7. Person lookup
    for pattern in INTENT_PATTERNS["find_person"]:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            value = match.group(1).strip() if match.lastindex else None
            return "find_person", value

    return "unknown", None


def _format_person(person: Person) -> str:
    """Format a Person ORM instance as a readable text block."""
    location_parts = [p for p in (person.city, person.country) if p]
    location_str = ", ".join(location_parts) if location_parts else "N/A"

    if person.education_level and person.education_field:
        education_str = f"{person.education_level} in {person.education_field}"
    else:
        education_str = person.education_level or person.education_field or "N/A"

    lines = [
        f"**{person.full_name}**",
        f"- 📧 Email: {person.email}",
        f"- 📞 Phone: {person.phone or 'N/A'}",
        f"- 🎂 Date of Birth: {person.date_of_birth or 'N/A'}",
        f"- 📍 Location: {location_str}",
        f"- 💼 Job Title: {person.job_title or 'N/A'}",
        f"- 🏢 Department: {person.department or 'N/A'}",
        f"- 💰 Salary: ${person.salary:,.0f}" if person.salary is not None else "- 💰 Salary: N/A",
        f"- 📅 Hire Date: {person.hire_date or 'N/A'}",
        f"- 🎓 Education: {education_str}",
        f"- 🛠️ Skills: {person.skills or 'N/A'}",
        f"- 🎯 Hobbies: {person.hobbies or 'N/A'}",
        f"- 🔗 LinkedIn: {person.linkedin or 'N/A'}",
    ]
    return "\n".join(lines)


def _query_by_filter(db: Session, kind: str, value: str):
    """Build SQLAlchemy query for department, location, or skill filter."""
    pattern = f"%{value}%"
    if kind == "department":
        return db.query(Person).filter(Person.department.ilike(pattern))
    if kind == "location":
        return db.query(Person).filter(
            or_(Person.city.ilike(pattern), Person.country.ilike(pattern))
        )
    return db.query(Person).filter(Person.skills.ilike(pattern))


def answer_question(question: str, db: Session) -> dict:
    """
    Parse a natural language question and return a structured answer.

    Args:
        question: Free-text question from the user.
        db: SQLAlchemy database session.

    Returns:
        Dict with keys:
            - 'answer': Markdown-formatted answer string.
            - 'people': List of Person ORM instances (if applicable).
            - 'intent': Detected intent name.
            - 'query_value': The extracted value from the question.
    """
    intent, value = _detect_intent(question)
    logger.debug(f"Question='{question}' → intent='{intent}', value='{value}'")

    response = {
        "answer": "",
        "people": [],
        "intent": intent,
        "query_value": value,
    }

    # ── Count queries ──────────────────────────────────────────────────────
    if intent == "count":
        q_clean = re.sub(r"[?!.,]+$", "", question.strip()).strip()
        target = _detect_count_target(q_clean)
        if target:
            kind, target_val = target
            filtered_q = _query_by_filter(db, kind, target_val)
            total = filtered_q.count()
            people = filtered_q.limit(settings.max_search_results).all()
            if kind == "department":
                response["answer"] = f"📊 There are **{total:,}** people in **{target_val}** department."
            elif kind == "location":
                response["answer"] = f"📊 There are **{total:,}** people in **{target_val}**."
            else:
                response["answer"] = f"📊 There are **{total:,}** people with **{target_val}** skills."
            response["people"] = people
        else:
            total = db.query(func.count(Person.id)).scalar()
            response["answer"] = f"📊 There are **{total:,}** people in the system."
        return response

    # ── Department / Location / Skill searches ─────────────────────────────
    filter_configs = {
        "find_by_department": ("department", "🏢", lambda v: f"in **{v}** department", lambda p: p.job_title or "N/A", lambda v: f"❌ No people found in '{v}' department."),
        "find_by_location": ("location", "📍", lambda v: f"in '{v}'", lambda p: f"{p.city}, {p.country}" if p.city or p.country else "N/A", lambda v: f"❌ No people found in location '{v}'."),
        "find_by_skill": ("skill", "🛠️", lambda v: f"with '{v}' skills", lambda p: p.job_title or "N/A", lambda v: f"❌ No people found with '{v}' skill."),
    }
    if intent in filter_configs and value:
        kind, icon, label_fn, detail_fn, empty_fn = filter_configs[intent]
        filtered_q = _query_by_filter(db, kind, value)
        total_matches = filtered_q.count()
        people = filtered_q.limit(settings.max_search_results).all()
        if people:
            names = "\n".join(f"- {p.full_name} ({detail_fn(p)})" for p in people[:10])
            suffix = f" (showing top {min(10, len(people))})" if total_matches > 10 else ""
            response["answer"] = (
                f"{icon} Found **{total_matches:,}** people {label_fn(value)}{suffix}:\n{names}"
            )
            response["people"] = people
        else:
            response["answer"] = empty_fn(value)
        return response

    # ── Person lookup by name ───────────────────────────────────────────────
    if intent == "find_person" and value:
        results = search_by_name(query=value, db=db, limit=1)
        if results:
            person = results[0].person
            full_person = db.query(Person).filter(Person.id == person.id).first()
            response["answer"] = _format_person(full_person)
            response["people"] = [full_person]
        else:
            response["answer"] = f"❌ Could not find anyone matching '{value}'."
        return response

    # ── List all ────────────────────────────────────────────────────────────
    if intent == "list_all":
        people = db.query(Person).limit(settings.max_search_results).all()
        names = "\n".join(f"- {p.full_name} ({p.department or 'N/A'})" for p in people)
        response["answer"] = f"👥 Showing first {len(people)} people:\n{names}"
        response["people"] = people
        return response

    # ── Fallback: try fuzzy name search ─────────────────────────────────────
    clean_query = re.sub(r"[?!.,]+$", "", question.strip()).strip()
    results = search_by_name(query=clean_query, db=db, limit=5)
    if results:
        person = results[0].person
        full_person = db.query(Person).filter(Person.id == person.id).first()
        response["answer"] = (
            f"🔍 Best match for '{question}' (score: {results[0].score:.0f}%):\n\n"
            + _format_person(full_person)
        )
        response["people"] = [full_person]
        response["intent"] = "fuzzy_fallback"
    else:
        response["answer"] = (
            f"🤔 I couldn't understand your question or find anyone matching '{question}'.\n\n"
            "Try questions like:\n"
            "- 'Tell me about John Smith'\n"
            "- 'Who works in Engineering?'\n"
            "- 'Who lives in New York?'\n"
            "- 'How many people are in the system?'\n"
            "- 'Show me people with Python skills'"
        )

    return response
