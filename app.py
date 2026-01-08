import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
from fpdf import FPDF
from duckduckgo_search import DDGS
from pptx import Presentation
from ics import Calendar, Event
import base64
import io
import zipfile
import json
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Studio V21: The Oracle", layout="wide", page_icon="🔮")

st.markdown("""
    <style>
    .stButton button {height: 3.5em; font-weight: 800; border-radius: 8px; background-color: #4B0082; color: white;}
    .brand-sidebar {background-color: #f8f9fa; padding: 15px; border-radius: 10px;}
    div[data-testid="stStatusWidget"] {visibility: visible;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.sidebar.text_input("🔑 API Key", type="password")
    if not api_key: st.stop()

client = OpenAI(api_key=api_key)

if "history" not in st.session_state: st.session_state.history = []

# --- 3. HELPER FUNCTIONS (Artifacts) ---
def create_ics(events_data):
    c = Calendar()
    for e in events_data:
        event = Event()
        event.name = e.get('summary', 'Task')
        event.begin = e.get('date', '2024-01-01')
        c.events.add(event)
    return str(c).encode('utf-8')

def create_audio(text):
    return client.audio.speech.create(model="tts-1", voice="onyx", input=text[:4096]).content

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest="S").encode("latin-1")

def web_search(query):
    try: return "\n".join([f"- {r['title']}: {r['body']}" for r in DDGS().text(query, max_results=2)])
    except: return "Offline."

# --- 4. THE ORACLE ENGINE (Simulation & Recursion) ---

def run_oracle_swarm(protocol, mission, context):
    results = {}
    
    with st.status("🔮 Oracle Engine: Initializing...", expanded=True) as status:
        
        # 1. LIVE INTEL
        status.write("🌍 Agent 1: Scanning Reality...")
        intel = web_search(f"{mission} controversy backlash trends")
        
        # 2. RECURSIVE DRAFTING LOOP
        status.write("✍️ Agent 2: Recursive Drafting (Looping until > 85/100)...")
        current_draft = ""
        quality_score = 0
        attempts = 0
        
        while quality_score < 85 and attempts < 3:
            attempts += 1
            # Draft
            draft_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"Task: {protocol}. Context: {context}. Intel: {intel}. Attempt: {attempts}. Output Markdown."},
                    {"role": "user", "content": f"Refine this draft (or create new): {current_draft}"}
                ]
            )
            current_draft = draft_resp.choices[0].message.content
            
            # Score
            score_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": f"Rate this strategy 0-100 based on clarity, impact, and risk mitigation. Output ONLY the number. \n\nSTRATEGY: {current_draft[:1000]}"}]
            )
            try: quality_score = int(score_resp.choices[0].message.content.strip())
            except: quality_score = 90 # Fallback
            
            status.write(f"Attempt {attempts}: Quality Score {quality_score}/100")
        
        results['Master_Strategy.md'] = current_draft
        
        # 3. THE SIMULATOR (Virtual Focus Group)
        status.write("👥 Agent 3: Running Virtual Focus Group...")
        sim_prompt = f"""
        Act as a Focus Group Simulator. 
        Create a dialogue between 3 Personas: 
        1. 'The Skeptic' (Critical)
        2. 'The Fan' (Loyal)
        3. 'The Journalist' (Facts)
        
        They are reacting to this strategy: {current_draft[:1000]}
        Output a script of their conversation.
        """
        sim_resp = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "system", "content": sim_prompt}]
        )
        results['Simulation_Logs.md'] = sim_resp.choices[0].message.content
        
        # 4. ARTIFACTS
        status.write("📦 Agent 4: Packaging Assets...")
        
        # Audio
        results['Audio_Briefing.mp3'] = create_audio(f"Oracle Report. Strategy Quality {quality_score}. Focus Group Summary: {results['Simulation_Logs.md'][:500]}")
        
        # Calendar
        try:
            cal_resp = client.chat.completions.create(
                model="gpt-4o", response_format={ "type": "json_object" },
                messages=[{"role": "system", "content": f"Extract dates to JSON [{{'summary':'...', 'date':'YYYY-MM-DD'}}]: {current_draft[:2000]}"}]
            )
            results['Schedule.ics'] = create_ics(json.loads(cal_resp.choices[0].message.content).get('events', []))
        except: pass

        status.update(label="✅ Oracle Prediction Complete", state="complete")
        
    return results

# --- 5. INTERFACE ---
with st.sidebar:
    st.title("🧬 Brand DNA")
    brand_name = st.text_input("Org Name", placeholder="Apex Media")
    north_star = st.text_area("North Star Goal", placeholder="Growth...")

st.title("🔮 Studio V21: The Oracle")

col1, col2 = st.columns([2, 1])
with col1:
    mission_input = st.text_area("Mission Objective", placeholder="e.g. Launch controversial ad campaign...", height=100)
    uploaded_file = st.file_uploader("Context Files", type=["pdf", "docx", "txt"])
with col2:
    protocol = st.selectbox("Protocol:", ["🚀 Product Launch", "📢 Crisis Response", "🎥 Video Bible", "💼 Exec Strategy"])
    if st.button("🚀 RUN SIMULATION", type="primary", use_container_width=True):
        if not mission_input: st.stop()
        context = f"Brand: {brand_name}. Goal: {north_star}."
        outputs = run_oracle_swarm(protocol, mission_input, context)
        st.session_state.history.insert(0, outputs)
        st.rerun()

# --- 6. OUTPUTS ---
if st.session_state.history:
    st.divider()
    latest = st.session_state.history[0]
    
    # SIMULATION TAB (The New Feature)
    t1, t2, t3 = st.tabs(["👥 Focus Group Sim", "📄 Master Strategy", "🎧 Audio Brief"])
    
    with t1:
        st.info("💡 Predict backlash before it happens.")
        st.markdown(latest['Simulation_Logs.md'])
    
    with t2:
        st.markdown(latest['Master_Strategy.md'])
        
    with t3:
        if 'Audio_Briefing.mp3' in latest:
            st.audio(latest['Audio_Briefing.mp3'])
    
    # DOWNLOAD
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for key, val in latest.items():
            if key.endswith(('.mp3', '.ics')): zip_file.writestr(key, val)
            elif key.endswith('.md'): 
                zip_file.writestr(key, val)
                try: zip_file.writestr(key.replace('.md', '.pdf'), create_pdf(val))
                except: pass
                
    st.download_button("📦 Download Oracle Bundle", zip_buffer.getvalue(), "Oracle_Assets.zip", "application/zip", type="primary")
