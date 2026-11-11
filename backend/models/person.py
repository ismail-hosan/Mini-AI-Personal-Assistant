"""
SQLAlchemy ORM model for the Person entity.
Represents a single person record stored in the database.
"""

from sqlalchemy import Column, Integer, String, Date, Float, Text
from backend.database.session import Base


class Person(Base):
    """
    ORM model mapping to the 'people' table in SQLite.

    Columns cover personal info, employment details, education,
    skills, hobbies, and miscellaneous metadata.
    """

    __tablename__ = "people"

    # ─── Identity ──────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    full_name = Column(String(200), nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(String(10), nullable=True)  # ISO 8601: YYYY-MM-DD

    # ─── Location ──────────────────────────────────────────────────────────
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    # ─── Employment ────────────────────────────────────────────────────────
    department = Column(String(100), nullable=True, index=True)
    job_title = Column(String(150), nullable=True)
    salary = Column(Float, nullable=True)
    hire_date = Column(String(10), nullable=True)  # ISO 8601: YYYY-MM-DD

    # ─── Education ─────────────────────────────────────────────────────────
    education_level = Column(String(50), nullable=True)
    education_field = Column(String(100), nullable=True)

    # ─── Professional Details ──────────────────────────────────────────────
    skills = Column(Text, nullable=True)   # comma-separated list
    hobbies = Column(Text, nullable=True)  # comma-separated list
    linkedin = Column(String(300), nullable=True)
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Person id={self.id} name='{self.full_name}' dept='{self.department}'>"
