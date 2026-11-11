"""
Streamlit main app — dashboard and navigation hub.
"""

import sys
from pathlib import Path
# Ensure project root is in path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from frontend.utils.api_client import health_check, list_people

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Mini AI Personal Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("# 🧠 AI Assistant")
    st.markdown("---")
    st.markdown("### 📁 Navigation")
    st.page_link("app.py", label="🏠 Dashboard", icon="🏠")
    st.page_link("pages/search.py", label="🔍 Search People", icon="🔍")
    st.page_link("pages/assistant.py", label="🤖 AI Assistant", icon="🤖")
    st.markdown("---")

    # Backend status
    health = health_check()
    if health:
        st.success(f"✅ API Connected\n\n{health.get('people_count', 0):,} people in DB")
    else:
        st.error("❌ API Offline\n\nStart the backend server first.")

# ─── Dashboard ────────────────────────────────────────────────────────────────

st.markdown("# 🧠 Mini AI Personal Assistant")
st.markdown(
    "Welcome! This assistant helps you find and explore information about **1,000+ people** "
    "stored in the database. Use fuzzy search or ask natural language questions."
)
st.divider()

# ─── Quick Stats ──────────────────────────────────────────────────────────────

if health:
    col1, col2, col3, col4 = st.columns(4)
    total = health.get("people_count", 0)

    with col1:
        st.metric("👥 Total People", f"{total:,}")
    with col2:
        st.metric("🏥 API Status", "Online" if health else "Offline")
    with col3:
        st.metric("🗄️ Database", "SQLite")
    with col4:
        st.metric("🔍 Search", "Fuzzy Match")
else:
    st.warning("⚠️ Backend API is not running. Start it with: `uvicorn backend.main:app --reload`")

st.divider()

# ─── Feature Cards ────────────────────────────────────────────────────────────

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 🔍 Search People")
    st.markdown(
        "Search by name with **fuzzy matching** — handles typos, "
        "partial names, and misspellings. Browse the full directory "
        "with department and country filters."
    )
    if st.button("Go to Search →", key="goto_search", use_container_width=True):
        st.switch_page("pages/search.py")

with col_b:
    st.markdown("### 🤖 AI Assistant")
    st.markdown(
        "Ask natural language questions like *'Who works in Engineering?'* "
        "or *'Tell me about John Smith'*. No ML model — pure NLP "
        "powered by pattern matching and fuzzy search."
    )
    if st.button("Go to Assistant →", key="goto_assistant", use_container_width=True):
        st.switch_page("pages/assistant.py")

# ─── Quick Search ─────────────────────────────────────────────────────────────

st.divider()
st.markdown("### ⚡ Quick Search")
quick_q = st.text_input("Search by name", placeholder="Start typing a name...")
if quick_q:
    st.session_state["quick_search_query"] = quick_q
    st.switch_page("pages/search.py")
