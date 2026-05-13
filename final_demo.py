"""Student Problem OS Pro - polished Streamlit build."""
import os
import requests
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Student Problem OS",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Heavy custom CSS — pulls the look toward the editorial HTML design.
# Streamlit's chrome can't be fully removed, but we can paint over most of it.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
    :root {
        --bg: #fbfaf6;
        --bg-2: #f4f3ee;
        --panel: #ffffff;
        --ink: #1c1f26;
        --ink-2: #4a4f5a;
        --muted: #8a8f99;
        --line: #e3e2dd;
        --line-2: #ededea;
        --accent: #4f5bd5;
        --accent-soft: #e6e8fa;
        --good: #2f7a4d;
        --sans: "Helvetica Neue", Helvetica, Arial, sans-serif;
        --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
    }

    /* Hide Streamlit chrome */
    #MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; height: 0; }
    .stDeployButton { display: none; }

    html, body, [class*="css"] {
        font-family: var(--sans) !important;
        color: var(--ink);
        background: var(--bg);
    }
    .stApp { background: var(--bg); }
    .block-container {
        padding-top: 2.2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1200px;
    }

    /* ----- Custom header strip ----- */
    .spos-top {
        display: flex; align-items: center; justify-content: space-between;
        padding-bottom: 18px; margin-bottom: 28px;
        border-bottom: 1px solid var(--line);
    }
    .spos-brand { display: flex; align-items: center; gap: 12px; }
    .spos-mark {
        width: 22px; height: 22px;
        border: 1.5px solid var(--ink);
        border-radius: 4px; position: relative;
    }
    .spos-mark::after {
        content: ""; position: absolute;
        top: 4px; right: 4px;
        width: 6px; height: 6px;
        background: var(--accent); border-radius: 1px;
    }
    .spos-brand h1 {
        font-size: 15px !important; font-weight: 600;
        margin: 0; letter-spacing: -0.005em;
    }
    .spos-sub {
        font-family: var(--mono); font-size: 11px;
        color: var(--muted); letter-spacing: 0.02em;
        text-transform: uppercase;
        padding-left: 12px; margin-left: 12px;
        border-left: 1px solid var(--line);
    }
    .spos-meta {
        font-family: var(--mono); font-size: 11px;
        color: var(--muted); letter-spacing: 0.02em;
    }

    /* ----- Hero ----- */
    .spos-hero h2 {
        font-size: 36px !important; line-height: 1.05;
        letter-spacing: -0.02em; margin: 0 0 10px;
        font-weight: 500; text-wrap: balance;
    }
    .spos-hero p {
        color: var(--ink-2) !important;
        max-width: 56ch; margin: 0;
    }

    /* ----- Headings ----- */
    h2, h3 {
        font-family: var(--sans) !important;
        letter-spacing: -0.01em;
        font-weight: 500 !important;
        color: var(--ink) !important;
    }
    h2 { font-size: 22px !important; margin-top: 0 !important; }
    h3 { font-size: 14px !important; }
    .spos-label {
        font-family: var(--mono); font-size: 10px;
        letter-spacing: 0.06em; text-transform: uppercase;
        color: var(--muted); margin-bottom: 8px;
    }

    /* ----- Buttons ----- */
    .stButton > button, .stLinkButton > a {
        background: var(--ink) !important;
        color: var(--bg) !important;
        border: 1px solid var(--ink) !important;
        border-radius: 6px !important;
        font-family: var(--sans) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 8px 14px !important;
        box-shadow: none !important;
        transition: opacity 120ms;
    }
    .stButton > button:hover, .stLinkButton > a:hover {
        opacity: 0.88; transform: none !important;
    }
    .stLinkButton > a {
        background: var(--panel) !important;
        color: var(--ink) !important;
        border: 1px solid var(--line) !important;
        text-decoration: none !important;
    }
    .stLinkButton > a:hover {
        border-color: var(--ink-2) !important;
        background: var(--bg-2) !important;
    }

    /* ----- Inputs / select / chat ----- */
    .stTextInput input, .stSelectbox > div > div, .stChatInput textarea {
        border: 1px solid var(--line) !important;
        background: var(--panel) !important;
        border-radius: 6px !important;
        font-family: var(--sans) !important;
        font-size: 14px !important;
        color: var(--ink) !important;
    }
    .stChatInput { background: var(--bg) !important; }
    .stChatInput textarea:focus { border-color: var(--ink-2) !important; box-shadow: none !important; }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 14px 18px !important;
        margin-bottom: 12px;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
        font-size: 14px; line-height: 1.55;
        color: var(--ink-2);
    }
    [data-testid="stChatMessage"] strong {
        color: var(--ink); font-weight: 600;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 14px 16px !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: var(--mono) !important;
        font-size: 10px !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: var(--muted) !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 500 !important;
        letter-spacing: -0.01em;
        color: var(--ink) !important;
        font-variant-numeric: tabular-nums;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 10px;
        overflow: hidden;
    }

    /* Divider */
    hr {
        border-color: var(--line) !important;
        margin: 28px 0 !important;
    }

    /* Caption */
    .stCaption, [data-testid="stCaptionContainer"] {
        font-family: var(--mono) !important;
        font-size: 10px !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: var(--muted) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Custom header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="spos-top">
      <div class="spos-brand">
        <div class="spos-mark"></div>
        <h1>Student Problem OS</h1>
        <span class="spos-sub">v 2.0 / academic coach</span>
      </div>
      <div class="spos-meta">CLOUD LLM · OLLAMA</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="spos-hero">
      <h2>An operating system for students who want to actually finish what they start.</h2>
      <p>Diagnose what's stuck, get a three-task plan, and watch the week add up. Built for high-school workloads, designed to be quiet.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")


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
    api_key = os.environ.get("OLLAMA_API_KEY")
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")

    if not api_key:
        return (
            "Add `OLLAMA_API_KEY` (and optionally `OLLAMA_MODEL`) to your "
            "environment variables to enable the coach."
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


if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown('<div class="spos-label">Academic Coach</div>', unsafe_allow_html=True)
st.markdown("## Tell the coach what's stuck.")

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
# Resources
# ---------------------------------------------------------------------------
st.markdown('<div class="spos-label">Resource Library</div>', unsafe_allow_html=True)
st.markdown("## Curated 1-click resources")

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
# Task tracker
# ---------------------------------------------------------------------------
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

if "tasks" not in st.session_state:
    st.session_state.tasks = [0] * len(DAYS)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="spos-label">Task Tracker</div>', unsafe_allow_html=True)
    st.markdown("## Daily progress")
    day_idx = st.selectbox("Day", DAYS, index=0, label_visibility="collapsed")
    current = st.session_state.tasks[DAYS.index(day_idx)]
    st.metric("Tasks complete", f"{current}/3")

with col2:
    st.markdown('<div class="spos-label">Mark Complete</div>', unsafe_allow_html=True)
    st.markdown("## Three tasks per day")
    for n in range(1, 4):
        if st.button(f"Mark task {n} complete", use_container_width=True, key=f"task-{n}"):
            i = DAYS.index(day_idx)
            if st.session_state.tasks[i] < 3:
                st.session_state.tasks[i] += 1
                st.rerun()

st.divider()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
st.markdown('<div class="spos-label">Progress Dashboard</div>', unsafe_allow_html=True)
st.markdown("## Weekly view")

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

m1, m2, m3 = st.columns(3)
m1.metric("Total tasks", total_tasks)
m2.metric("Days complete", sum(1 for x in st.session_state.tasks if x == 3))
m3.metric("Success rate", f"{success_rate:.0f}%")

st.write("")
if st.button("Reset week"):
    st.session_state.tasks = [0] * len(DAYS)
    st.rerun()

st.markdown("---")
st.caption("Student Problem OS · 2.0 · Cloud LLM via Ollama API")
