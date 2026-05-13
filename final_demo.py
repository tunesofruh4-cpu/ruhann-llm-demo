"""Student Problem OS Pro - Cloud LLM Version"""
import os
import requests
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Student Problem OS Pro",
    page_icon=None,
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { padding: 2rem; }
    .stMetric { font-size: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Student Problem OS Pro")
st.markdown("**Real AI Academic Coach + Tasks + Resources**")


# ---------------------------------------------------------------------------
# AI coach
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert high school academic coach.
Respond ALWAYS with:
1. **Diagnosis:** (1 sentence)
2. **3-Task Daily Plan:** (numbered 1-3)
3. **Pro Tip:** (1 sentence)
4. **Resource:** (1 link)

Specific, actionable, encouraging for students."""


def ai_coach_response(user_input: str) -> str:
    """Call the Ollama Cloud API. Falls back to a clear error if not configured."""
    api_key = os.environ.get("OLLAMA_API_KEY")
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")

    if not api_key:
        return (
            "Add `OLLAMA_API_KEY` (and optionally `OLLAMA_MODEL`) to your environment "
            "variables to enable the coach."
        )

    url = "https://ollama.com/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", str(data)[:400])
    except requests.exceptions.RequestException as e:
        return f"API error: {str(e)[:160]}"


# ---------------------------------------------------------------------------
# 1. Chat
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

st.header("AI Academic Coach")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Describe your academic struggle..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = ai_coach_response(prompt)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

st.divider()


# ---------------------------------------------------------------------------
# 2. Resources
# ---------------------------------------------------------------------------
st.header("1-Click Resources")
resources = [
    ("Khan Academy", "https://www.khanacademy.org"),
    ("PMT", "https://www.physicsandmathstutor.com"),
    ("Quizlet", "https://quizlet.com"),
    ("Grammarly", "https://www.grammarly.com"),
]
cols = st.columns(len(resources))
for col, (name, url) in zip(cols, resources):
    with col:
        st.link_button(name, url, use_container_width=True)

st.divider()


# ---------------------------------------------------------------------------
# 3. Task tracker
# ---------------------------------------------------------------------------
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

if "tasks" not in st.session_state:
    st.session_state.tasks = [0] * len(DAYS)

col1, col2 = st.columns(2)

with col1:
    st.header("Task Tracker")
    day_idx = st.selectbox("Day:", DAYS, index=0)
    current = st.session_state.tasks[DAYS.index(day_idx)]
    st.metric("Progress", f"{current}/3")

with col2:
    st.header("Mark complete")
    for n in range(1, 4):
        if st.button(f"Task {n}", use_container_width=True, key=f"task-{n}"):
            i = DAYS.index(day_idx)
            if st.session_state.tasks[i] < 3:
                st.session_state.tasks[i] += 1
                if st.session_state.tasks[i] == 3:
                    st.balloons()
                st.rerun()

st.divider()


# ---------------------------------------------------------------------------
# 4. Dashboard
# ---------------------------------------------------------------------------
st.header("Progress Dashboard")

data = [
    {
        "Day": day,
        "Tasks": f"{t}/3",
        "Status": "Complete" if t == 3 else "In progress",
    }
    for day, t in zip(DAYS, st.session_state.tasks)
]
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True, hide_index=True)

total_tasks = sum(st.session_state.tasks)
success_rate = sum(1 for x in st.session_state.tasks if x == 3) / len(DAYS) * 100

col1, col2 = st.columns(2)
col1.metric("Total Tasks", total_tasks)
col2.metric("Success Rate", f"{success_rate:.0f}%")

if st.button("Reset Week"):
    st.session_state.tasks = [0] * len(DAYS)
    st.rerun()

st.markdown("---")
st.caption("Cloud LLM via Ollama API")
