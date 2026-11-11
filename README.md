# 🧠 Mini AI Personal Assistant

A Python-based personal assistant that stores information about **1,000+ people** and answers natural language questions about them. Built with FastAPI, SQLite, SQLAlchemy, and Streamlit.

---

## 📁 Project Structure

```
ai-assistant/
├── backend/                    # FastAPI backend
│   ├── api/                    # Route handlers (people, assistant)
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # Business logic (search, assistant NLP)
│   ├── database/               # DB engine, session factory
│   ├── config.py               # Settings loaded from .env
│   └── main.py                 # FastAPI app entry point
├── frontend/                   # Streamlit UI
│   ├── app.py                  # Dashboard (main page)
│   ├── pages/
│   │   ├── search.py           # Fuzzy name search + directory browser
│   │   └── assistant.py        # AI Q&A chat interface
│   └── utils/
│       └── api_client.py       # HTTP client for backend API
├── data/                       # SQLite DB + generated CSV (gitignored)
├── utils/                      # Shared utilities
│   ├── logger.py               # Rich-formatted logging
│   └── data_loader.py          # CSV generator + DB seeder
├── tests/                      # Pytest test suite
│   ├── test_api.py             # FastAPI endpoint tests
│   └── test_services.py        # Service-layer unit tests
├── .env                        # Environment variables (local)
├── .env.example                # Template for .env
├── pytest.ini                  # Pytest configuration
└── requirements.txt            # Python dependencies
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- pip

### 2. Create & Activate Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example env file (already done — .env exists)
cp .env.example .env
# Edit .env if needed (defaults work out of the box)
```

### 5. Start the Backend API

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The first startup will:
- Create all database tables
- Generate 1,000 dummy person records
- Seed the SQLite database automatically

### 6. Start the Frontend

Open a **second terminal** (with venv activated):

```bash
streamlit run frontend/app.py
```

---

## 🌐 Access Points

| Service | URL |
|---------|-----|
| Streamlit Frontend | http://localhost:8501 |
| FastAPI Backend | http://localhost:8000 |
| Interactive API Docs | http://localhost:8000/docs |
| ReDoc API Docs | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

---

## 🔍 Features

### Fuzzy Name Search
- Handles typos, partial names, and misspellings
- Powered by **RapidFuzz** (WRatio algorithm)
- Configurable confidence threshold (default: 70%)
- Returns ranked results with match scores

### AI Assistant (Natural Language Q&A)
Ask questions like:
- `"Tell me about John Smith"` → Full profile
- `"Who works in Engineering?"` → Department list
- `"Who lives in New York?"` → Location search
- `"How many people are in the system?"` → Count
- `"Show me people with Python skills"` → Skill search

### People Directory
- Paginated list of all 1,000+ people
- Filter by department and country
- Full CRUD API (create, read, update, delete)

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# With verbose output
pytest -v

# Run only service tests (no HTTP)
pytest tests/test_services.py -v

# Run only API tests
pytest tests/test_api.py -v
```

---

## 🔌 API Reference

### People Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/people/` | List all people (paginated) |
| `GET` | `/api/v1/people/search?q=name` | Fuzzy name search |
| `GET` | `/api/v1/people/{id}` | Get person by ID |
| `POST` | `/api/v1/people/` | Create new person |
| `PATCH` | `/api/v1/people/{id}` | Update person (partial) |
| `DELETE` | `/api/v1/people/{id}` | Delete person |

### Assistant Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/assistant/ask` | Ask a natural language question |
| `GET` | `/api/v1/assistant/ask?q=question` | Same (for browser/testing) |

---

## ⚙️ Configuration

All settings live in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./data/assistant.db` | SQLite database path |
| `API_HOST` | `127.0.0.1` | Backend host |
| `API_PORT` | `8000` | Backend port |
| `BACKEND_URL` | `http://127.0.0.1:8000` | Frontend uses this to call backend |
| `FUZZY_MATCH_THRESHOLD` | `70` | Minimum fuzzy score (0–100) |
| `MAX_SEARCH_RESULTS` | `20` | Max results returned |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI + Uvicorn | REST API server |
| Database | SQLite + SQLAlchemy | Persistent storage & ORM |
| Validation | Pydantic v2 | Request/response schemas |
| Search | RapidFuzz | Fuzzy name matching |
| Frontend | Streamlit | Interactive web UI |
| Data | Pandas + CSV | Dummy data generation |
| Logging | Rich | Beautiful console output |
| Testing | Pytest + HTTPX | API & unit tests |

---

## 📝 Notes

- No ML model is used — the assistant uses rule-based NLP (regex pattern matching)
- All 1,000 dummy records are generated with `random.seed(42)` for reproducibility
- The SQLite database is auto-created and auto-seeded on first startup
- Tests use a separate in-memory SQLite database — they won't affect your data
# Mini-AI-Personal-Assistant
