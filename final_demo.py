"""Student Problem OS Pro - feature-complete Streamlit build.

Mirrors the HTML version as closely as Streamlit allows:
- Multi-problem days, each problem with a 3-task program
- AI coach (Ollama Cloud) picks the days for the program based on scope
- Weekly tracker, hero stats, resource library
- Tweaks in the sidebar (accent, density, days, focus length)
- Clear chat / reset week / clear all
- Persistence to a local JSON file
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Page config + persistence file
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Student Problem OS",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

STORE_PATH = Path(os.environ.get("SPOS_STORE", ".spos_store.json"))

DAYS_5 = ["Mon", "Tue", "Wed", "Thu", "Fri"]
DAYS_7 = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

DEFAULT_TWEAKS: dict[str, Any] = {
    "accent": "indigo",
    "density": "comfortable",
    "days": 5,
    "pomodoro": 25,
    "break": 5,
    "show_hero": True,
}

ACCENTS = {
    "indigo": {"hex": "#4f5bd5", "soft": "#e6e8fa", "name": "Indigo"},
    "forest": {"hex": "#2f7a4d", "soft": "#dceee2", "name": "Forest"},
    "clay":   {"hex": "#b65a2e", "soft": "#f3e1d4", "name": "Clay"},
    "graphite": {"hex": "#3b4150", "soft": "#e1e3e8", "name": "Graphite"},
}

ALLOWED_RESOURCES = [
    ("Khan Academy", "Math · Sciences", "https://www.khanacademy.org"),
    ("PMT", "Past papers · Revision", "https://www.physicsandmathstutor.com"),
    ("Quizlet", "Recall · Flashcards", "https://quizlet.com"),
    ("Grammarly", "Writing", "https://www.grammarly.com"),
    ("Anki", "Spaced Repetition", "https://apps.ankiweb.net"),
    ("Desmos", "Graphing", "https://www.desmos.com/calculator"),
    ("Purdue OWL", "Citations · Style", "https://owl.purdue.edu"),
    ("Crash Course", "Survey · Video", "https://thecrashcourse.com"),
]
ALLOWED_RESOURCE_URLS = {url for _, _, url in ALLOWED_RESOURCES}


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def active_days(tweaks: dict[str, Any]) -> list[str]:
    return DAYS_7 if tweaks.get("days") == 7 else DAYS_5


def load_store() -> dict[str, Any]:
    if STORE_PATH.exists():
        try:
            return json.loads(STORE_PATH.read_text())
        except Exception:
            pass
    return {}


def save_store() -> None:
    payload = {
        "by_day": st.session_state.by_day,
        "messages": st.session_state.messages,
        "tweaks": st.session_state.tweaks,
        "active_day": st.session_state.active_day,
    }
    try:
        STORE_PATH.write_text(json.dumps(payload, indent=2))
    except Exception:
        pass  # ephemeral environments — silently fall back to session-only


def init_state() -> None:
    if "tweaks" in st.session_state:
        return
    store = load_store()
    st.session_state.tweaks = {**DEFAULT_TWEAKS, **store.get("tweaks", {})}
    days = active_days(st.session_state.tweaks)
    today = (datetime.now().weekday())  # 0=Mon
    st.session_state.active_day = store.get("active_day", days[min(today, len(days) - 1)])
    st.session_state.messages = store.get("messages", [])
    st.session_state.by_day = store.get("by_day", {d: [] for d in days})
    # ensure every active day has an entry
    for d in days:
        st.session_state.by_day.setdefault(d, [])
    # confirm flags
    for k in ("confirm_clear_chat", "confirm_reset_week", "confirm_clear_all"):
        st.session_state.setdefault(k, False)


init_state()


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
accent = ACCENTS[st.session_state.tweaks["accent"]]
density = st.session_state.tweaks["density"]
base_font_size = "13px" if density == "compact" else "14px"

st.markdown(
    f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
    :root {{
        --bg: #fbfaf6;
        --bg-2: #f4f3ee;
        --panel: #ffffff;
        --ink: #1c1f26;
        --ink-2: #4a4f5a;
        --muted: #8a8f99;
        --line: #e3e2dd;
        --line-2: #ededea;
        --accent: {accent['hex']};
        --accent-soft: {accent['soft']};
        --good: #2f7a4d;
        --sans: "Helvetica Neue", Helvetica, Arial, sans-serif;
        --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
    }}

    #MainMenu, header[data-testid="stHeader"], footer {{ visibility: hidden; height: 0; }}
    .stDeployButton {{ display: none; }}

    html, body, [class*="css"] {{
        font-family: var(--sans) !important;
        color: var(--ink);
        font-size: {base_font_size};
    }}
    .stApp {{ background: var(--bg); }}
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1280px;
    }}

    /* ----- Sidebar (used for Tweaks) ----- */
    [data-testid="stSidebar"] {{
        background: var(--panel);
        border-right: 1px solid var(--line);
    }}
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        font-family: var(--sans) !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--ink) !important;
    }}

    /* ----- Header strip ----- */
    .spos-top {{
        display: flex; align-items: center; justify-content: space-between;
        padding-bottom: 18px; margin-bottom: 28px;
        border-bottom: 1px solid var(--line);
    }}
    .spos-brand {{ display: flex; align-items: center; gap: 12px; }}
    .spos-mark {{
        width: 22px; height: 22px;
        border: 1.5px solid var(--ink);
        border-radius: 4px; position: relative;
    }}
    .spos-mark::after {{
        content: ""; position: absolute;
        top: 4px; right: 4px;
        width: 6px; height: 6px;
        background: var(--accent); border-radius: 1px;
    }}
    .spos-brand h1 {{
        font-size: 15px !important; font-weight: 600;
        margin: 0; letter-spacing: -0.005em;
    }}
    .spos-sub {{
        font-family: var(--mono); font-size: 11px;
        color: var(--muted); letter-spacing: 0.02em;
        text-transform: uppercase;
        padding-left: 12px; margin-left: 12px;
        border-left: 1px solid var(--line);
    }}
    .spos-meta {{
        font-family: var(--mono); font-size: 11px;
        color: var(--muted); letter-spacing: 0.02em;
    }}

    /* ----- Hero ----- */
    .spos-hero h2 {{
        font-size: 36px !important; line-height: 1.05;
        letter-spacing: -0.02em; margin: 0 0 10px;
        font-weight: 500; text-wrap: balance;
    }}
    .spos-hero p {{
        color: var(--ink-2) !important;
        max-width: 56ch; margin: 0;
    }}

    /* ----- Section labels ----- */
    h2, h3 {{
        font-family: var(--sans) !important;
        letter-spacing: -0.01em;
        font-weight: 500 !important;
        color: var(--ink) !important;
    }}
    h2 {{ font-size: 22px !important; margin-top: 0 !important; }}
    h3 {{ font-size: 14px !important; }}
    .spos-label {{
        font-family: var(--mono); font-size: 10px;
        letter-spacing: 0.06em; text-transform: uppercase;
        color: var(--muted); margin-bottom: 6px;
    }}

    /* ----- Day cards in weekly tracker ----- */
    .spos-day {{
        border: 1px solid var(--line);
        background: var(--panel);
        border-radius: 6px;
        padding: 12px 10px;
        height: 100%;
        margin-bottom: 4px;
    }}
    .spos-day.active {{ border-color: var(--ink); background: var(--bg-2); }}
    .spos-day .lab {{
        font-family: var(--mono); font-size: 10px; letter-spacing: 0.06em;
        text-transform: uppercase; color: var(--muted); margin-bottom: 8px;
    }}
    .spos-day .pellets {{
        display: flex; gap: 2px; flex-wrap: wrap; min-height: 6px; margin-bottom: 8px;
    }}
    .spos-day .pellet {{
        flex: 1 0 6px; max-width: 14px;
        height: 6px; border-radius: 2px; background: var(--line);
    }}
    .spos-day .pellet.on {{ background: var(--accent); }}
    .spos-day .pellet.full {{ background: var(--good); }}
    .spos-day .num {{
        font-family: var(--mono); font-size: 11px; color: var(--ink-2);
        display: flex; justify-content: space-between;
        font-variant-numeric: tabular-nums;
    }}
    .spos-day .num .probs {{ color: var(--muted); }}

    /* ----- Buttons ----- */
    .stButton > button {{
        background: var(--ink) !important;
        color: var(--bg) !important;
        border: 1px solid var(--ink) !important;
        border-radius: 6px !important;
        font-family: var(--sans) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 7px 14px !important;
        box-shadow: none !important;
    }}
    .stButton > button:hover {{ opacity: 0.88; transform: none !important; }}
    .stButton > button[kind="secondary"], .stLinkButton > a {{
        background: var(--panel) !important;
        color: var(--ink) !important;
        border: 1px solid var(--line) !important;
        text-decoration: none !important;
    }}
    .stButton > button[kind="secondary"]:hover, .stLinkButton > a:hover {{
        border-color: var(--ink-2) !important;
        background: var(--bg-2) !important;
    }}

    /* ----- Chat ----- */
    [data-testid="stChatMessage"] {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 14px 18px !important;
        margin-bottom: 12px;
    }}
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {{
        font-size: 14px; line-height: 1.55; color: var(--ink-2);
    }}
    [data-testid="stChatMessage"] strong {{ color: var(--ink); font-weight: 600; }}
    .stChatInput textarea {{
        border: 1px solid var(--line) !important;
        background: var(--panel) !important;
        border-radius: 6px !important;
        font-family: var(--sans) !important;
    }}

    /* ----- Inputs / select ----- */
    .stTextInput input, .stSelectbox > div > div, .stTextArea textarea {{
        border: 1px solid var(--line) !important;
        background: var(--panel) !important;
        border-radius: 6px !important;
        font-family: var(--sans) !important;
        font-size: 14px !important;
        color: var(--ink) !important;
    }}

    /* ----- Metrics ----- */
    [data-testid="stMetric"] {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 14px 16px !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-family: var(--mono) !important;
        font-size: 10px !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: var(--muted) !important;
    }}
    [data-testid="stMetricValue"] {{
        font-size: 24px !important;
        font-weight: 500 !important;
        letter-spacing: -0.01em;
        color: var(--ink) !important;
        font-variant-numeric: tabular-nums;
    }}

    /* ----- Expander (problem cards) ----- */
    .streamlit-expanderHeader, [data-testid="stExpander"] summary {{
        background: var(--panel) !important;
        border: 1px solid var(--line) !important;
        border-radius: 6px !important;
        font-family: var(--sans) !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: var(--ink) !important;
        padding: 10px 12px !important;
    }}
    [data-testid="stExpander"] {{
        border: 1px solid var(--line);
        border-radius: 6px;
        margin-bottom: 8px;
        background: var(--panel);
    }}

    /* ----- Dataframe ----- */
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--line);
        border-radius: 10px;
        overflow: hidden;
    }}

    /* ----- Day pills (in coach card output) ----- */
    .day-pill-row {{ display: flex; flex-wrap: wrap; gap: 4px; margin: 6px 0 0; }}
    .day-pill {{
        border: 1px solid var(--line);
        background: var(--panel);
        color: var(--ink-2);
        font-family: var(--mono);
        font-size: 10px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 4px 8px;
        border-radius: 4px;
    }}
    .day-pill.on {{
        background: var(--accent);
        color: #fff;
        border-color: var(--accent);
    }}
    .day-pill.off {{
        color: var(--muted);
        border-color: var(--line-2);
        opacity: 0.55;
    }}

    /* ----- Divider ----- */
    hr {{ border-color: var(--line) !important; margin: 28px 0 !important; }}
    .stCaption, [data-testid="stCaptionContainer"] {{
        font-family: var(--mono) !important;
        font-size: 10px !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: var(--muted) !important;
    }}

    /* Problem meta rows */
    .meta-row {{
        display: grid; grid-template-columns: 90px 1fr; gap: 12px;
        padding: 8px 0; border-bottom: 1px dashed var(--line-2);
    }}
    .meta-row:last-child {{ border-bottom: 0; }}
    .meta-row .k {{
        font-family: var(--mono); font-size: 10px;
        letter-spacing: 0.06em; text-transform: uppercase;
        color: var(--muted);
    }}
    .meta-row .v {{ font-size: 13px; color: var(--ink-2); }}
    .meta-row .v a {{ color: var(--accent); }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# AI coach
# ---------------------------------------------------------------------------
def build_system_prompt() -> str:
    today_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][datetime.now().weekday()]
    week = ", ".join(active_days(st.session_state.tweaks))
    return f"""You are an expert high school academic coach.
Today is {today_name}. The student's tracked week is: {week}.
Always respond as STRICT JSON with these keys (and ONLY these keys):
{{
  "title": "3-6 word label naming the problem",
  "diagnosis": "single sentence describing the root issue",
  "plan": [
    {{ "task": "task 1 - foundation", "est": "15m" }},
    {{ "task": "task 2 - deep work", "est": "45m" }},
    {{ "task": "task 3 - review/practice", "est": "20m" }}
  ],
  "days": ["Mon", "Wed", "Fri"],
  "tip": "one-sentence tactic",
  "resource": {{ "title": "short name", "url": "https://..." }}
}}

CRITICAL RULES FOR "days":
- The 3-task program is the SAME daily routine. Pick which days the student should run it.
- DO NOT default to today or to a single day. Actually JUDGE the problem.
- One-day scope: a quick fix or assignment due tomorrow.
- Multi-day scope (2-5 days): a test in N days, a skill build.
- Whole-week scope (5-7 days): a chronic struggle.
- Use day names from this set ONLY: Mon, Tue, Wed, Thu, Fri, Sat, Sun.

"plan" MUST contain exactly 3 tasks: foundation, deep work, review.
"resource.url" MUST be one of: https://www.khanacademy.org, https://www.physicsandmathstutor.com,
https://quizlet.com, https://www.grammarly.com, https://apps.ankiweb.net,
https://www.desmos.com/calculator, https://owl.purdue.edu, https://thecrashcourse.com.

No emojis. No preamble. No code fences. Output JSON only."""


def ai_coach_response(user_input: str) -> dict[str, Any] | str:
    api_key = os.environ.get("OLLAMA_API_KEY")
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")

    if not api_key:
        return "Add `OLLAMA_API_KEY` to environment variables to enable the coach."

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": user_input},
        ],
        "stream": False,
        "format": "json",
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        resp = requests.post(
            "https://ollama.com/api/chat", json=payload, headers=headers, timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        return parse_coach_json(content) or content
    except requests.exceptions.RequestException as e:
        return f"API error: {str(e)[:160]}"


def parse_coach_json(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        pass
    # try fenced block
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    # try first {...}
    i, j = raw.find("{"), raw.rfind("}")
    if i >= 0 and j > i:
        try:
            return json.loads(raw[i : j + 1])
        except Exception:
            pass
    return None


def sanitize_resource(res: Any) -> dict[str, str] | None:
    if not isinstance(res, dict) or not res.get("url"):
        return None
    url = res["url"].rstrip("/")
    if url in ALLOWED_RESOURCE_URLS:
        return {"title": res.get("title", url), "url": url}
    # try origin match
    for allowed in ALLOWED_RESOURCE_URLS:
        if url.startswith(allowed.rsplit("/", 1)[0]):
            return {"title": res.get("title", "Resource"), "url": allowed}
    return {"title": res.get("title", "Resource"), "url": "https://www.khanacademy.org"}


def normalize_plan(plan: Any) -> list[dict[str, str]]:
    fallback_est = ["15m", "45m", "20m"]
    out: list[dict[str, str]] = []
    if isinstance(plan, list):
        for i, item in enumerate(plan):
            if isinstance(item, str):
                out.append({"task": item, "est": fallback_est[i] if i < 3 else "10m"})
            elif isinstance(item, dict) and item.get("task"):
                out.append(
                    {
                        "task": item["task"],
                        "est": item.get("est", fallback_est[i] if i < 3 else "10m"),
                    }
                )
    while len(out) < 3:
        out.append({"task": "Review and reflect on progress", "est": "10m"})
    return out[:3]


def make_problem(
    title: str,
    plan: list[dict[str, str]],
    diagnosis: str = "",
    tip: str = "",
    resource: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "title": title or "Untitled problem",
        "diagnosis": diagnosis,
        "tip": tip,
        "resource": resource,
        "created_at": datetime.now().isoformat(),
        "tasks": [
            {"id": str(uuid.uuid4()), "text": p["task"], "done": False, "est": p["est"]}
            for p in plan
        ],
    }


# ---------------------------------------------------------------------------
# Sidebar — Tweaks
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Tweaks")

    accent_name = st.selectbox(
        "Accent",
        options=list(ACCENTS.keys()),
        format_func=lambda k: ACCENTS[k]["name"],
        index=list(ACCENTS.keys()).index(st.session_state.tweaks["accent"]),
    )
    if accent_name != st.session_state.tweaks["accent"]:
        st.session_state.tweaks["accent"] = accent_name
        save_store()
        st.rerun()

    density_choice = st.radio(
        "Density",
        ["comfortable", "compact"],
        index=["comfortable", "compact"].index(st.session_state.tweaks["density"]),
        horizontal=True,
    )
    if density_choice != st.session_state.tweaks["density"]:
        st.session_state.tweaks["density"] = density_choice
        save_store()
        st.rerun()

    days_choice = st.radio(
        "Days shown",
        [5, 7],
        index=[5, 7].index(st.session_state.tweaks["days"]),
        horizontal=True,
        format_func=lambda x: "Mon–Fri" if x == 5 else "Mon–Sun",
    )
    if days_choice != st.session_state.tweaks["days"]:
        st.session_state.tweaks["days"] = days_choice
        # ensure new days exist
        for d in active_days(st.session_state.tweaks):
            st.session_state.by_day.setdefault(d, [])
        if st.session_state.active_day not in active_days(st.session_state.tweaks):
            st.session_state.active_day = active_days(st.session_state.tweaks)[0]
        save_store()
        st.rerun()

    st.session_state.tweaks["pomodoro"] = st.slider(
        "Focus session (min)", 10, 60, st.session_state.tweaks["pomodoro"], step=5
    )
    st.session_state.tweaks["break"] = st.slider(
        "Break (min)", 3, 20, st.session_state.tweaks["break"]
    )
    st.session_state.tweaks["show_hero"] = st.toggle(
        "Show hero stats", value=st.session_state.tweaks["show_hero"]
    )

    st.markdown("---")
    st.markdown("### Maintenance")

    # Click-twice patterns using flags
    def confirm_button(label: str, flag_key: str, danger: bool = False) -> bool:
        armed = st.session_state.get(flag_key, False)
        btn_label = "Click again to confirm" if armed else label
        clicked = st.button(btn_label, key=f"btn_{flag_key}", use_container_width=True)
        if clicked and not armed:
            st.session_state[flag_key] = True
            st.rerun()
        if clicked and armed:
            st.session_state[flag_key] = False
            return True
        return False

    if confirm_button("Clear chat", "confirm_clear_chat"):
        st.session_state.messages = []
        save_store()
        st.rerun()
    if confirm_button("Reset week (uncheck all)", "confirm_reset_week"):
        for d in active_days(st.session_state.tweaks):
            for p in st.session_state.by_day.get(d, []):
                for t in p["tasks"]:
                    t["done"] = False
        save_store()
        st.rerun()
    if confirm_button("Clear all problems", "confirm_clear_all", danger=True):
        for d in active_days(st.session_state.tweaks):
            st.session_state.by_day[d] = []
        save_store()
        st.rerun()


# ---------------------------------------------------------------------------
# Top strip
# ---------------------------------------------------------------------------
today_meta = datetime.now().strftime("%a · %b %-d").upper() if hasattr(datetime, "strftime") else ""
st.markdown(
    f"""
    <div class="spos-top">
      <div class="spos-brand">
        <div class="spos-mark"></div>
        <h1>Student Problem OS</h1>
        <span class="spos-sub">v 2.0 / academic coach</span>
      </div>
      <div class="spos-meta">{today_meta}</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
days = active_days(st.session_state.tweaks)

if st.session_state.tweaks["show_hero"]:
    all_tasks = [t for d in days for p in st.session_state.by_day.get(d, []) for t in p["tasks"]]
    done_tasks = [t for t in all_tasks if t["done"]]
    pct = round(len(done_tasks) / len(all_tasks) * 100) if all_tasks else 0
    active_problems = len(st.session_state.by_day.get(st.session_state.active_day, []))

    st.markdown(
        """
        <div class="spos-hero">
          <h2>An operating system for students who want to actually finish what they start.</h2>
          <p>Diagnose what's stuck, get a three-task plan, and watch the week add up. Each day can hold as many problems as you bring to it.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    m1, m2, m3 = st.columns(3)
    m1.metric("Week progress", f"{pct}%")
    m2.metric("Tasks done", f"{len(done_tasks)} / {len(all_tasks)}")
    m3.metric("Active problems", f"{active_problems} today")

st.divider()


# ---------------------------------------------------------------------------
# Coach
# ---------------------------------------------------------------------------
st.markdown('<div class="spos-label">Academic Coach</div>', unsafe_allow_html=True)
st.markdown("## Tell the coach what's stuck.")

# Empty state suggestions
if not st.session_state.messages:
    st.markdown(
        "Get a one-line diagnosis, a 3-step program (foundation → deep work → review), "
        "and the days to run it — picked by the coach based on the problem's scope."
    )
    sug_cols = st.columns(4)
    suggestions = [
        "Cramming for a chem test in 3 days",
        "Can't start a history essay",
        "Behind in AP Calc — limits",
        "Always start homework at 11pm",
    ]
    full_prompts = [
        "I have a chemistry test on stoichiometry in three days and I keep blanking on mole conversions.",
        "I can't start my history essay. I've been staring at the prompt for two hours.",
        "I'm behind on AP Calc — limits and continuity are not making sense.",
        "I procrastinate on homework every night and only start at 11pm.",
    ]
    for col, label, prompt in zip(sug_cols, suggestions, full_prompts):
        with col:
            if st.button(label, key=f"sug_{label}", use_container_width=True):
                st.session_state._auto_prompt = prompt
                st.rerun()

# Render chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message.get("content"), dict):
            d = message["content"]
            parts = []
            if d.get("title"):
                parts.append(f"**Problem:** {d['title']}")
            if d.get("diagnosis"):
                parts.append(f"**Diagnosis:** {d['diagnosis']}")
            if d.get("plan"):
                plan_lines = "\n".join(
                    f"{i+1}. {p['task']} _({p['est']})_"
                    for i, p in enumerate(d["plan"])
                )
                parts.append("**Program:**\n" + plan_lines)
            if d.get("days"):
                pills = "".join(
                    f'<span class="day-pill {"on" if day in d["days"] else "off"}">{day}</span>'
                    for day in active_days(st.session_state.tweaks)
                )
                parts.append(f'**Days:**\n<div class="day-pill-row">{pills}</div>')
            if d.get("tip"):
                parts.append(f"**Tactic:** {d['tip']}")
            if d.get("resource") and d["resource"].get("url"):
                parts.append(f"**Resource:** [{d['resource'].get('title', d['resource']['url'])}]({d['resource']['url']})")
            st.markdown("\n\n".join(parts), unsafe_allow_html=True)

            # Apply button (only for the most recent assistant message)
            is_latest = message is st.session_state.messages[-1]
            already_applied = message.get("applied", False)
            if is_latest and not already_applied and d.get("plan") and d.get("days"):
                valid_days = [day for day in d["days"] if day in active_days(st.session_state.tweaks)]
                if not valid_days:
                    valid_days = [st.session_state.active_day]
                label = (
                    f"Schedule program on {valid_days[0]}"
                    if len(valid_days) == 1
                    else f"Schedule program across {len(valid_days)} days"
                )
                if st.button(label, key=f"apply_{id(message)}"):
                    title = d.get("title") or "Coached problem"
                    res = sanitize_resource(d.get("resource"))
                    plan = normalize_plan(d.get("plan"))
                    for day in valid_days:
                        st.session_state.by_day.setdefault(day, [])
                        st.session_state.by_day[day].append(
                            make_problem(title, plan, d.get("diagnosis", ""), d.get("tip", ""), res)
                        )
                    message["applied"] = True
                    save_store()
                    st.rerun()
        else:
            st.markdown(str(message["content"]))


# Coach input
prompt_to_send = st.session_state.pop("_auto_prompt", None)
typed = st.chat_input("Describe your academic struggle...")
if typed:
    prompt_to_send = typed

if prompt_to_send:
    st.session_state.messages.append({"role": "user", "content": prompt_to_send})
    with st.chat_message("user"):
        st.markdown(prompt_to_send)
    with st.chat_message("assistant"):
        with st.spinner("Coach is thinking..."):
            response = ai_coach_response(prompt_to_send)
        if isinstance(response, dict):
            # Sanitize resource immediately
            response["resource"] = sanitize_resource(response.get("resource"))
            response["plan"] = normalize_plan(response.get("plan"))
            st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            st.session_state.messages.append({"role": "assistant", "content": response})
    save_store()
    st.rerun()

st.divider()


# ---------------------------------------------------------------------------
# Weekly tracker
# ---------------------------------------------------------------------------
st.markdown('<div class="spos-label">Weekly Tracker</div>', unsafe_allow_html=True)
st.markdown("## Your week")

def render_day_card(day: str) -> str:
    probs = st.session_state.by_day.get(day, [])
    tasks = [t for p in probs for t in p["tasks"]]
    done = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    all_done = total > 0 and done == total
    pellets_html = ""
    if total == 0:
        pellets_html = '<span class="pellet"></span>'
    else:
        for t in tasks:
            if all_done:
                pellets_html += '<span class="pellet full"></span>'
            else:
                pellets_html += f'<span class="pellet {"on" if t["done"] else ""}"></span>'
    active_cls = " active" if day == st.session_state.active_day else ""
    return f"""
    <div class="spos-day{active_cls}">
      <div class="lab">{day}</div>
      <div class="pellets">{pellets_html}</div>
      <div class="num">
        <span>{done}/{total}</span>
        <span class="probs">{len(probs)} prob{'s' if len(probs) != 1 else ''}</span>
      </div>
    </div>
    """

day_cols = st.columns(len(days))
for col, day in zip(day_cols, days):
    with col:
        st.markdown(render_day_card(day), unsafe_allow_html=True)
        if st.button(f"Open {day}", key=f"open_{day}", use_container_width=True):
            st.session_state.active_day = day
            save_store()
            st.rerun()


# ---------------------------------------------------------------------------
# Problems for active day
# ---------------------------------------------------------------------------
st.write("")
active_problems = st.session_state.by_day.get(st.session_state.active_day, [])
st.markdown(
    f'<div class="spos-label">Problems for {st.session_state.active_day} · {len(active_problems)}</div>',
    unsafe_allow_html=True,
)
st.markdown("## Today's problems")

# Manual add
with st.expander("+ Add a problem manually", expanded=False):
    new_title = st.text_input("Problem title", key="manual_title")
    new_t1 = st.text_input("Task 1 (foundation)", key="manual_t1", value="")
    new_t2 = st.text_input("Task 2 (deep work)", key="manual_t2", value="")
    new_t3 = st.text_input("Task 3 (review)", key="manual_t3", value="")
    if st.button("Add problem", key="add_manual"):
        if new_title.strip():
            tasks = []
            for n, est in [(new_t1, "15m"), (new_t2, "45m"), (new_t3, "20m")]:
                tasks.append({"task": n.strip() or "Task", "est": est})
            prob = make_problem(new_title.strip(), tasks)
            st.session_state.by_day[st.session_state.active_day].append(prob)
            save_store()
            for k in ("manual_title", "manual_t1", "manual_t2", "manual_t3"):
                st.session_state.pop(k, None)
            st.rerun()

if not active_problems:
    st.markdown(
        f"_No problems yet for {st.session_state.active_day}. Ask the coach above, "
        "or add one manually._"
    )

for prob in active_problems:
    done_count = sum(1 for t in prob["tasks"] if t["done"])
    total = len(prob["tasks"])
    expander_label = f"{prob['title']}  ·  {done_count}/{total}"
    with st.expander(expander_label, expanded=False):
        if prob.get("diagnosis"):
            st.markdown(
                f'<div class="meta-row"><div class="k">Diagnosis</div><div class="v">{prob["diagnosis"]}</div></div>',
                unsafe_allow_html=True,
            )

        # Tasks with checkboxes
        for t in prob["tasks"]:
            cols = st.columns([0.06, 0.84, 0.10])
            with cols[0]:
                new_done = st.checkbox(
                    "",
                    value=t["done"],
                    key=f"chk_{prob['id']}_{t['id']}",
                    label_visibility="collapsed",
                )
                if new_done != t["done"]:
                    t["done"] = new_done
                    save_store()
                    st.rerun()
            with cols[1]:
                if t["done"]:
                    st.markdown(f"~~{t['text']}~~")
                else:
                    st.markdown(t["text"])
            with cols[2]:
                st.markdown(
                    f'<span style="font-family: var(--mono); font-size: 10px; color: var(--muted); letter-spacing: 0.04em; text-transform: uppercase;">{t["est"]}</span>',
                    unsafe_allow_html=True,
                )

        if prob.get("tip"):
            st.markdown(
                f'<div class="meta-row"><div class="k">Tactic</div><div class="v">{prob["tip"]}</div></div>',
                unsafe_allow_html=True,
            )
        if prob.get("resource") and prob["resource"].get("url"):
            res = prob["resource"]
            st.markdown(
                f'<div class="meta-row"><div class="k">Resource</div><div class="v"><a href="{res["url"]}" target="_blank">{res.get("title", res["url"])}</a></div></div>',
                unsafe_allow_html=True,
            )

        # Delete
        cols = st.columns([0.7, 0.3])
        with cols[1]:
            if st.button("Delete problem", key=f"del_{prob['id']}", use_container_width=True):
                st.session_state.by_day[st.session_state.active_day] = [
                    p for p in active_problems if p["id"] != prob["id"]
                ]
                save_store()
                st.rerun()

st.divider()


# ---------------------------------------------------------------------------
# Focus session (static — no live ticking in Streamlit)
# ---------------------------------------------------------------------------
st.markdown('<div class="spos-label">Focus Session</div>', unsafe_allow_html=True)
st.markdown(f"## Pomodoro · {st.session_state.tweaks['pomodoro']} / {st.session_state.tweaks['break']} cycle")
st.markdown(
    f"Run a **{st.session_state.tweaks['pomodoro']}-minute** focused block, then take a "
    f"**{st.session_state.tweaks['break']}-minute** break. Adjust in the sidebar."
)
st.markdown(
    "> _Streamlit can't run a live ticking timer (every interaction reloads the page). "
    "Use your phone or an external Pomodoro tool — the recommended cadence is shown above._"
)

st.divider()


# ---------------------------------------------------------------------------
# Resource library
# ---------------------------------------------------------------------------
st.markdown('<div class="spos-label">Resource Library</div>', unsafe_allow_html=True)
st.markdown("## Curated tools")

cols_per_row = 4
for row_start in range(0, len(ALLOWED_RESOURCES), cols_per_row):
    cols = st.columns(cols_per_row)
    for col, (name, cat, url) in zip(cols, ALLOWED_RESOURCES[row_start : row_start + cols_per_row]):
        with col:
            st.markdown(
                f'<div style="border:1px solid var(--line); border-radius:6px; padding:12px 14px; background:var(--panel);">'
                f'<div style="font-size:13px; font-weight:500; color:var(--ink); margin-bottom:2px;">{name}</div>'
                f'<div style="font-family:var(--mono); font-size:10px; letter-spacing:0.06em; text-transform:uppercase; color:var(--muted); margin-bottom:8px;">{cat}</div>'
                f'<a href="{url}" target="_blank" style="font-size:12px; color:var(--accent); text-decoration:none;">Open ↗</a>'
                f"</div>",
                unsafe_allow_html=True,
            )

st.divider()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
st.markdown('<div class="spos-label">Dashboard</div>', unsafe_allow_html=True)
st.markdown("## Weekly view")

rows = []
for day in days:
    probs = st.session_state.by_day.get(day, [])
    tasks = [t for p in probs for t in p["tasks"]]
    done = sum(1 for t in tasks if t["done"])
    total = len(tasks)
    status = "Complete" if total > 0 and done == total else ("Empty" if total == 0 else "In progress")
    rows.append({
        "Day": day,
        "Problems": len(probs),
        "Tasks": f"{done}/{total}",
        "Status": status,
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Student Problem OS · 2.0 · Cloud LLM via Ollama API")
