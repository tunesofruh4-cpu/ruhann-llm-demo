"""🦈 STUDENT PROBLEM OS PRO - CLOUD LLM VERSION"""
import streamlit as st
import pandas as pd
import os
import requests

st.set_page_config(page_title="Student Problem OS Pro", page_icon="🦈", layout="wide")

st.markdown("""
<style>
.main {padding: 2rem}
.stMetric {font-size: 1.5rem}
</style>
""", unsafe_allow_html=True)

st.title("🦈 Student Problem OS Pro")
st.markdown("**Real AI Academic Coach + Tasks + Resources**")

def ai_coach_response(user_input):
    system_prompt = """You are expert high school academic coach.
    Respond ALWAYS with:
    1. **Diagnosis:** (1 sentence)
    2. **3-Task Daily Plan:** (numbered 1-3)  
    3. **Pro Tip:** (1 sentence)
    4. **Resource:** (1 link)
    
    Specific, actionable, encouraging for students."""
    
    api_key = os.environ.get("OLLAMA_API_KEY")
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    
    if not api_key:
        return "Add OLLAMA_API_KEY + OLLAMA_MODEL in Render Environment first."
    
    url = "https://ollama.com/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "stream": False
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        data = resp.json()
        return data.get("message", {}).get("content", str(data)[:400])
    except Exception as e:
        return f"API error: {str(e)[:120]}"

# 1. REAL AI CHAT
if "messages" not in st.session_state:
    st.session_state.messages = []

st.header("🤖 Real AI Academic Coach")

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

# 2. EMBEDDED RESOURCES
st.header("📚 1-Click Resources")
cols = st.columns(4)
resources = [
    ("Khan Academy", "https://khanacademy.org/math"),
    ("Wolfram Alpha", "https://wolframalpha.com"), 
    ("Quizlet", "https://quizlet.com"),
    ("Grammarly", "https://grammarly.com")
]

for i, (name, url) in enumerate(resources):
    with cols[i]:
        if st.button(name, use_container_width=True):
            st.markdown(f"[Open {name}]({url})")
            st.balloons()

st.divider()

# 3. TASK EXECUTION
col1, col2 = st.columns(2)
with col1:
    st.header("✅ Task Tracker")
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    day_idx = st.selectbox("Day:", days, index=0)
    
    if 'tasks' not in st.session_state:
        st.session_state.tasks = [0] * 5
    
    current = st.session_state.tasks[days.index(day_idx)]
    st.metric("Progress", f"{current}/3")

with col2:
    if st.button("Task 1 ✓", use_container_width=True):
        if current < 3:
            st.session_state.tasks[days.index(day_idx)] += 1
            st.experimental_rerun()
    if st.button("Task 2 ✓", use_container_width=True):
        if current < 3:
            st.session_state.tasks[days.index(day_idx)] += 1
            st.experimental_rerun()
    if st.button("Task 3 ✓", use_container_width=True):
        if current < 3:
            st.session_state.tasks[days.index(day_idx)] += 1
            st.balloons()
            st.experimental_rerun()

st.divider()

# 4. DASHBOARD
st.header("📊 Progress Dashboard")
data = [{"Day": day, "Tasks": f"{t}/3", "Status": "✅" if t==3 else "⚠️"}
        for day, t in zip(days, st.session_state.tasks)]
df = pd.DataFrame(data)
st.dataframe(df, use_container_width=True)

col1, col2 = st.columns(2)
col1.metric("Total Tasks", sum(st.session_state.tasks))
col2.metric("Success Rate", f"{sum(1 for x in st.session_state.tasks if x==3)/5*100:.0f}%")

if st.button("🔄 Reset Week"):
    st.session_state.tasks = [0]*5
    st.experimental_rerun()

st.markdown("---")
st.caption("Cloud LLM via Ollama API")
