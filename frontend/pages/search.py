"""
Search & Browse page — fuzzy name search + paginated people directory.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from frontend.utils.api_client import search_people, list_people

st.set_page_config(page_title="Search People", page_icon="🔍", layout="wide")

# ─── Page Header ──────────────────────────────────────────────────────────────

st.markdown("## 🔍 Search People")
st.markdown("Search by name using fuzzy matching — handles typos and partial names gracefully.")
st.divider()

# ─── Search Bar ───────────────────────────────────────────────────────────────

default_query = st.session_state.pop("quick_search_query", "")

col1, col2, col3 = st.columns([4, 1, 1])
with col1:
    query = st.text_input(
        "Name search",
        value=default_query,
        placeholder="e.g. John Smith, Mary, Rodriguez...",
        label_visibility="collapsed",
    )
with col2:
    threshold = st.slider("Min. match %", min_value=0, max_value=100, value=70)
with col3:
    limit = st.selectbox("Max results", [10, 20, 50, 100], index=1)

# ─── Search Results ───────────────────────────────────────────────────────────

if query:
    with st.spinner("Searching..."):
        data = search_people(query=query, threshold=threshold, limit=limit)

    if data is None:
        st.error("❌ Could not connect to the backend. Make sure the API server is running.")
    elif data["total"] == 0:
        st.warning(f"No results found for **'{query}'** (threshold: {threshold}%)")
    else:
        st.success(f"Found **{data['total']}** result(s) for **'{query}'**")
        for item in data["results"]:
            person = item["person"]
            score = item["score"]
            loc_parts = [p for p in (person.get("city"), person.get("country")) if p]
            loc_str = ", ".join(loc_parts) if loc_parts else "N/A"
            with st.expander(f"🧑 {person['full_name']} — {person.get('job_title') or 'N/A'} | Score: {score:.0f}%"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**📧 Email:** {person.get('email') or 'N/A'}")
                    st.write(f"**📞 Phone:** {person.get('phone') or 'N/A'}")
                    st.write(f"**📍 Location:** {loc_str}")
                    st.write(f"**🏢 Department:** {person.get('department') or 'N/A'}")
                    salary = person.get("salary")
                    salary_str = f"${salary:,.0f}" if salary is not None else "N/A"
                    st.write(f"**💰 Salary:** {salary_str}")
                with col_b:
                    st.write(f"**🎂 Date of Birth:** {person.get('date_of_birth') or 'N/A'}")
                    st.write(f"**📅 Hire Date:** {person.get('hire_date') or 'N/A'}")
                    edu_level = person.get("education_level")
                    edu_field = person.get("education_field")
                    if edu_level and edu_field:
                        edu_str = f"{edu_level} in {edu_field}"
                    else:
                        edu_str = edu_level or edu_field or "N/A"
                    st.write(f"**🎓 Education:** {edu_str}")
                    st.write(f"**🛠️ Skills:** {person.get('skills') or 'N/A'}")
                    st.write(f"**🎯 Hobbies:** {person.get('hobbies') or 'N/A'}")

else:
    # ── Directory Browser ─────────────────────────────────────────────────────
    st.markdown("### 📂 People Directory")

    col_dept, col_country = st.columns(2)
    with col_dept:
        department_filter = st.text_input("Filter by Department", placeholder="e.g. Engineering")
    with col_country:
        country_filter = st.text_input("Filter by Country", placeholder="e.g. USA")

    page = st.number_input("Page", min_value=1, value=1, step=1)
    page_size = 20
    skip = (page - 1) * page_size

    data = list_people(
        skip=skip,
        limit=page_size,
        department=department_filter or None,
        country=country_filter or None,
    )

    if data is None:
        st.error("❌ Could not connect to the backend.")
    else:
        total = data["total"]
        if total == 0:
            st.caption("Showing 0 of 0 people")
        else:
            st.caption(f"Showing {skip + 1}–{min(skip + page_size, total)} of {total:,} people")

        import pandas as pd
        if data["results"]:
            df = pd.DataFrame(data["results"])
            display_cols = ["id", "full_name", "job_title", "department", "city", "country", "email"]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No records found with the current filters.")
