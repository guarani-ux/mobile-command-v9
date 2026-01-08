import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Studio V9.5", layout="wide", page_icon="📱")
st.title("📱 Studio V9.5: Command Center")

# --- 2. AUTHENTICATION ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    if not api_key:
        st.warning("⚠️ Enter API Key in Sidebar to Start")
        st.stop()

client = OpenAI(api_key=api_key)

# --- 3. HELPER FUNCTIONS ---
def read_file(uploaded_file):
    if not uploaded_file: return ""
    file_type = uploaded_file.name.split('.')[-1].lower()
    text = ""
    try:
        if file_type == 'pdf':
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages: text += page.extract_text() + "\n"
        elif file_type == 'docx':
            doc = Document(uploaded_file)
            for para in doc.paragraphs: text += para.text + "\n"
        elif file_type in ['txt', 'md']:
            text = uploaded_file.read().decode("utf-8")
        elif file_type == 'csv':
            df = pd.read_csv(uploaded_file)
            text = df.to_markdown(index=False)
    except Exception as e:
        return f"Error: {e}"
    return text

# --- 4. MISSION CONTROL (Sidebar) ---
with st.sidebar:
    st.header("1. Input Data")
    uploaded_file = st.file_uploader("📂 Upload Brief/CSV", type=["pdf", "docx", "txt", "csv"])
    
    st.header("2. Strategy & Context")
    
    # SAFE AUDIO: Wrapped to prevent crashes
    audio_brief = None
    try:
        audio_brief = st.audio_input("🎙️ Voice Brief (Tap to Record)")
    except:
        st.warning("Audio unavailable on this browser.")

    # TEXT FALLBACK
    with st.expander("📝 Written Context", expanded=True):
        text_objective = st.text_area("Objective:", placeholder="e.g. Launch new website...")
        audience = st.text_input("Audience:", placeholder="e.g. Stakeholders...")

    # DIGITAL CONTROLS (Restored)
    with st.expander("💻 Tech & Resources"):
        tech_stack = st.text_input("Tech Stack:", placeholder="e.g. React, WordPress")
        budget = st.text_input("Budget/Team:", placeholder="e.g. 2 Devs, $50k")
    
    # CONTROLS
    depth = st.select_slider("Depth:", options=["Draft", "Standard", "Comprehensive"], value="Standard")
    
    st.header("3. Select Package")
    package_type = st.selectbox("📦 Output Suite:", [
        "Project Brief / Scope of Work",
        "Digital Product Launch (Web/App)",
        "Jira/Asana Ticket Generator",
        "SEO & Metadata Strategy",
        "Full Video Production Bible",
        "Marketing Campaign Launch",
        "Crisis Communications Suite",
        "Executive Strategy Deck",
        "Social Media Blast (Mobile)"
    ])
    
    generate_btn = st.button("🚀 EXECUTE", type="primary", use_container_width=True)

# --- 5. LOGIC ENGINE ---
if generate_btn:
    # A. Transcribe Audio (Safe Mode)
    audio_text = ""
    if audio_brief:
        with st.spinner("🎙️ Transcribing Voice..."):
            try:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_brief
                )
                audio_text = transcription.text
                st.success(f"
