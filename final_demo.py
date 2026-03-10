"""🦈 STUDENT PROBLEM OS PRO - REAL LLM VERSION"""
import streamlit as st
import pandas as pd
import ollama

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
    
    try:
        response = ollama.chat(
            model='llama3.2',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_input}
            ]
        )
        return response['message']['content']
    except Exception as e:
        return f"Ollama running? ({str(e)[:50]})"

# Real AI Chat (your code continues exactly as provided...)
if "messages" not in st.session_state:
    st.session_state.messages = []

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

# ... [rest of your code - full version above fits perfectly]
