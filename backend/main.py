"""
FastAPI application entry point.

Startup sequence:
1. Load settings from .env
2. Initialize database tables
3. Seed database from CSV if empty
4. Register API routers
5. Expose health check endpoint
"""

import csv
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.api.people import router as people_router
from backend.api.assistant import router as assistant_router
from backend.config import get_settings
from backend.database.session import init_db, SessionLocal, get_db
from backend.models.person import Person
from backend.schemas.person import RootResponse, HealthResponse
from utils.logger import get_logger
from utils.data_loader import generate_csv

logger = get_logger(__name__)
settings = get_settings()


# ─── Startup / Shutdown ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info(f"🚀 Starting [bold]{settings.app_name}[/bold] v{settings.app_version}")

    # 1. Create all DB tables
    init_db()

    # 2. Seed DB if empty
    db = SessionLocal()
    try:
        count = db.query(Person).count()
        if count == 0:
            logger.info("📦 Database is empty — seeding from CSV...")
            _seed_database(db)
        else:
            logger.info(f"✅ Database already has {count:,} records. Skipping seed.")
    finally:
        db.close()

    yield  # Application is running

    logger.info("👋 Shutting down...")


def _seed_database(db) -> None:
    """Generate CSV data and bulk-insert into the database."""
    csv_path = Path("data/sample_people.csv")

    # Generate the CSV if it doesn't exist
    if not csv_path.exists():
        generate_csv(output_path=csv_path, count=1000)

    # Bulk insert from CSV
    inserted = 0
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            batch.append(
                Person(
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                    full_name=row["full_name"],
                    email=row["email"],
                    phone=row["phone"],
                    date_of_birth=row["date_of_birth"],
                    city=row["city"],
                    country=row["country"],
                    department=row["department"],
                    job_title=row["job_title"],
                    salary=float(row["salary"]) if row["salary"] else None,
                    hire_date=row["hire_date"],
                    education_level=row["education_level"],
                    education_field=row["education_field"],
                    skills=row["skills"],
                    hobbies=row["hobbies"],
                    linkedin=row["linkedin"],
                    notes=row["notes"],
                )
            )
            if len(batch) >= 100:
                db.bulk_save_objects(batch)
                db.commit()
                inserted += len(batch)
                batch = []

        if batch:
            db.bulk_save_objects(batch)
            db.commit()
            inserted += len(batch)

    logger.info(f"[green]✓[/green] Seeded {inserted:,} records into the database.")


# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "A personal assistant API that stores information about 1,000+ people "
        "and answers natural language questions about them."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Allow Streamlit frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(people_router, prefix="/api/v1")
app.include_router(assistant_router, prefix="/api/v1")


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/", response_model=RootResponse, tags=["Health"])
def root():
    """Root health check — confirms the API is live."""
    return RootResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        docs="/docs",
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Detailed health status including database record count."""
    people_count = db.query(Person).count()

    return HealthResponse(
        status="healthy",
        app=settings.app_name,
        version=settings.app_version,
        database="connected",
        people_count=people_count,
    )
