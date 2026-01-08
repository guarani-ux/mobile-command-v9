import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
import io

# --- 1. CONFIGURATION ---
# UPDATED: Page Title set to "Content Creator"
st.set_page_config(page_title="Content Creator", layout="wide", page_icon="📱")
st.title("📱 Content Creator")

# --- 2. AUTHENTICATION ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    if not api_key:
        st.warning("⚠️ Enter API Key to Start")
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

# --- 4. MISSION CONTROL ---
with st.sidebar:
    st.header("1. Input Data")
    uploaded_file = st.file_uploader("📂 Upload Brief", type=["pdf", "docx", "txt", "csv"])
    
    st.header("2. Strategy & Context")
    
    # --- CRASH PROTECTION: AUDIO TOGGLE ---
    enable_audio = st.checkbox("🎙️ Enable Voice Mode (Experimental)")
    
    audio_brief = None
    if enable_audio:
        try:
            st.info("Microphone Active. Tap to record.")
            audio_brief = st.audio_input("Record Voice Brief")
        except:
            st.error("Your browser does not support this widget.")

    # TEXT INPUTS
    with st.expander("📝 Written Context", expanded=True):
        text_objective = st.text_area("Objective:", placeholder="e.g. Launch new website...")
        audience = st.text_input("Audience:", placeholder="e.g. Stakeholders...")

    # DIGITAL CONTROLS
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
                st.success(f"🗣️ Heard: {audio_text[:50]}...")
            except Exception as e:
                st.error(f"Audio Transcription Failed: {e}")
    
    # B. Combine Inputs
    final_objective = f"{text_objective}\n{audio_text}"
    file_context = read_file(uploaded_file)
    
    # C. Protocols
    prompts = {
        "Project Brief / Scope of Work": "Generate a Project Brief: 1. Exec Summary, 2. Deliverables, 3. Timeline, 4. Resources, 5. Success Metrics.",
        "Digital Product Launch (Web/App)": "Generate: 1. FRD Outline, 2. Tech Stack Analysis, 3. UAT Checklist, 4. Go-Live Runbook.",
        "Jira/Asana Ticket Generator": "Create a CSV-ready table of User Stories. Columns: Summary, Description (As a user...), Acceptance Criteria, Priority.",
        "SEO & Metadata Strategy": "Generate: 1. Keyword Cluster, 2. Meta Titles/Descriptions, 3. URL Structure, 4. Content Gap Analysis.",
        "Full Video Production Bible": "Generate: 1. Shooting Script, 2. Shot List, 3. Call Sheet, 4. Risk Assessment.",
        "Marketing Campaign Launch": "Generate: 1. Strategy, 2. Content Calendar, 3. Email Sequence, 4. Ad Creative Specs.",
        "Crisis Communications Suite": "Generate: 1. Holding Statement, 2. Internal Memo, 3. Q&A, 4. Press Release.",
        "Executive Strategy Deck": "Generate: 1. BLUF, 2. SWOT, 3. Financials, 4. Roadmap.",
        "Social Media Blast (Mobile)": "Create 3 posts (IG, LinkedIn, X). Put final text in ```code blocks``` for easy copying."
    }
    
    # D. The Brain
    system_prompt = f"""
    ROLE: Elite Digital Project Lead.
    TASK: Generate a {depth} {package_type}.
    
    CONTEXT:
    - Objective: {final_objective}
    - Audience: {audience}
    - Tech Stack: {tech_stack}
    - Budget: {budget}
    
    DATA:
    {file_context}
    
    INSTRUCTIONS:
    - Protocol: {prompts[package_type]}
    - Use Markdown Headers.
    - Use Tables for lists.
    """
    
    with st.spinner("🧠 Processing..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}]
            )
            result = response.choices[0].message.content
            
            st.markdown("---")
            st.markdown("### ✅ Generated Output")
            st.markdown(result)
            
            # Download Button
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
            st.download_button("💾 Save File", result, f"Output_{timestamp}.md")
            
        except Exception as e:
            st.error(f"Generation Error: {e}")
