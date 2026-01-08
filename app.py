import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
import io

# --- 1. MOBILE CONFIGURATION ---
st.set_page_config(page_title="Studio V9.2", layout="wide", page_icon="📱")

# CSS Hack to hide top bar for cleaner mobile look
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
div.block-container {padding-top: 1rem;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("📱 Studio V9.2: Digital Command")

# --- 2. AUTHENTICATION ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    if not api_key:
        st.info("🔒 Enter API Key to activate.")
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
    
    st.header("2. Strategy & Constraints")
    # AUDIO INPUT
    audio_brief = st.audio_input("🎙️ Voice Brief (Objective)")
    
    # TEXT FALLBACK
    with st.expander("📝 Written Context (Click to Expand)"):
        text_objective = st.text_area("Objective:", placeholder="e.g. Increase sign-ups...")
        audience = st.text_input("Audience:", placeholder="e.g. Stakeholders...")
    
    # LENGTH & DEPTH CONTROLS
    duration = st.text_input("⏱️ Length/Time Constraint:", placeholder="e.g. 2 mins, 500 words...")
    depth = st.select_slider("🎚️ Output Depth:", options=["Draft", "Standard", "Comprehensive"], value="Standard")

    # NEW: DIGITAL PROJECT CONTROLS
    with st.expander("💻 Tech & Resources (New)"):
        tech_stack = st.text_input("Tech Stack / Platform:", placeholder="e.g. WordPress, React, Shopify")
        budget = st.text_input("Budget / Resources:", placeholder="e.g. $50k cap, 2 Developers")

    st.header("3. Select Package")
    # UPDATED PACKAGE LIST
    package_type = st.selectbox("📦 Output Suite:", [
        "Project Brief / Scope of Work",
        "Digital Product Launch (Web/App)",     # <-- NEW
        "Jira/Asana Ticket Generator",          # <-- NEW
        "SEO & Metadata Strategy",              # <-- NEW
        "Full Video Production Bible",
        "Marketing Campaign Launch",
        "Crisis Communications Suite",
        "Executive Strategy Deck",
        "Social Media Blast (Mobile Optimized)"
    ])
    
    generate_btn = st.button("🚀 EXECUTE MISSION", type="primary", use_container_width=True)

# --- 5. LOGIC ENGINE ---
if generate_btn:
    # A. Transcribe Audio
    audio_text = ""
    if audio_brief:
        with st.spinner("🎙️ Transcribing Voice..."):
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_brief
            )
            audio_text = transcription.text
            st.success(f"🗣️ Heard: {audio_text[:50]}...")
    
    # B. Combine Inputs
    final_objective = f"{text_objective}\n{audio_text}"
    file_context = read_file(uploaded_file)
    
    # C. Protocols (Updated with Digital Suites)
    prompts = {
        "Project Brief / Scope of Work": "Generate a formal Project Brief including: 1. Executive Summary, 2. Deliverables List, 3. Timeline/Phasing, 4. Resource Requirements, 5. Success Metrics (KPIs).",
        "Digital Product Launch (Web/App)": "Generate: 1. Functional Requirements Document (FRD) outline, 2. Tech Stack Recommendations (rationale), 3. User Acceptance Testing (UAT) Checklist, 4. Go-Live Runbook.",
        "Jira/Asana Ticket Generator": "Analyze the brief and break it down into 'User Stories' for developers. Format as a CSV-ready Table with columns: 'Summary', 'Description (As a user I want...)', 'Acceptance Criteria', 'Priority'.",
        "SEO & Metadata Strategy": "Generate: 1. Primary Keyword Cluster, 2. Meta Titles & Descriptions (for Home, About, Services), 3. URL Structure recommendations, 4. Content Gap Analysis.",
        "Full Video Production Bible": "Generate: 1. Shooting Script (AV Format), 2. Shot List (Table), 3. Call Sheet, 4. Risk Assessment.",
        "Marketing Campaign Launch": "Generate: 1. Strategy Overview, 2. Content Calendar (Table), 3. Email Sequence, 4. Ad Creative Specs.",
        "Crisis Communications Suite": "Generate: 1. Holding Statement, 2. Internal Memo, 3. Q&A Key Messages, 4. Press Release.",
        "Executive Strategy Deck": "Generate: 1. BLUF (Bottom Line Up Front), 2. SWOT Analysis, 3. Financial Projections (Table), 4. Roadmap.",
        "Social Media Blast (Mobile Optimized)": "Create 3 variations (IG, LinkedIn, Twitter). Format inside Code Blocks (```) for one-tap copying."
    }
    
    # D. The Brain
    system_prompt = f"""
    ROLE: Elite Digital Project Lead & Strategist.
    TASK: Generate a {depth} {package_type}.
    
    STRATEGIC CONTEXT:
    - Objective: {final_objective}
    - Audience: {audience}
    - Constraints: {duration}
    - Depth Mode: {depth}
    
    DIGITAL CONSTRAINTS:
    - Tech Stack: {tech_stack}
    - Budget/Resources: {budget}
    
    INPUT DATA:
    {file_context}
    
    INSTRUCTIONS:
    - Follow this Protocol: {prompts[package_type]}
    - Use clear Markdown headers.
    - Use Tables for any lists, calendars, or ticket exports.
    - If 'Comprehensive' is selected, include a 'Rationale' section explaining the strategy.
    """
    
    with st.spinner("🧠 Processing Strategy..."):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}]
        )
        result = response.choices[0].message.content
        
        st.markdown("---")
        st.markdown("### ✅ Generated Output")
        st.markdown(result)
        
        # Download Option
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
        st.download_button("💾 Save Masterfile", result, f"Output_{timestamp}.md")
