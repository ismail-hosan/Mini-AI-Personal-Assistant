"""
AI Assistant page — natural language Q&A interface.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from frontend.utils.api_client import ask_assistant

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")

st.markdown("## 🤖 AI Personal Assistant")
st.markdown(
    "Ask me anything about the people in the database. "
    "I understand natural language questions!"
)
st.divider()

# ─── Example Questions ────────────────────────────────────────────────────────

st.markdown("### 💡 Try asking:")
examples = [
    "Tell me about John Smith",
    "Who works in Engineering?",
    "Who lives in New York?",
    "How many people are in the system?",
    "Show me people with Python skills",
    "Who is in the Sales department?",
    "Find someone in Data Science",
    "Who is based in London?",
]

cols = st.columns(4)
for i, example in enumerate(examples):
    with cols[i % 4]:
        if st.button(example, key=f"example_{i}", use_container_width=True):
            st.session_state["assistant_question"] = example

# ─── Chat Input ───────────────────────────────────────────────────────────────

st.divider()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

question = st.text_input(
    "Ask your question",
    value=st.session_state.get("assistant_question", ""),
    placeholder="e.g. Tell me about Maria Garcia",
    key="question_input",
)

if st.button("Ask 🚀", type="primary", use_container_width=True) and question:
    with st.spinner("Thinking..."):
        result = ask_assistant(question=question)

    if result is None:
        st.error("❌ Could not connect to the backend. Make sure the API server is running.")
    else:
        # Store in history
        st.session_state.chat_history.append({
            "question": question,
            "answer": result["answer"],
            "intent": result["intent"],
            "people_count": result["people_count"],
        })
        # Clear the preset question
        if "assistant_question" in st.session_state:
            del st.session_state["assistant_question"]

# ─── Chat History ─────────────────────────────────────────────────────────────

if st.session_state.chat_history:
    st.divider()
    st.markdown("### 💬 Conversation")

    for entry in reversed(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            st.markdown(entry["answer"])
            st.caption(f"Intent: `{entry['intent']}` | People found: {entry['people_count']}")

    if st.button("🗑️ Clear History"):
        st.session_state.chat_history = []
        st.rerun()
