import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
from fpdf import FPDF
from duckduckgo_search import DDGS
from pptx import Presentation
from pptx.util import Inches, Pt
import base64
import io
import zipfile

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Studio V19: Chief of Staff", layout="wide", page_icon="👔")

st.markdown("""
    <style>
    .stButton button {height: 3.5em; font-weight: 800; border-radius: 8px; background-color: #2E2E2E; color: white;}
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

# Session State
if "history" not in st.session_state: st.session_state.history = []
if "clarifying_questions" not in st.session_state: st.session_state.clarifying_questions = None
if "pending_mission" not in st.session_state: st.session_state.pending_mission = None

# --- 3. ARTIFACT ENGINES (The "Hands") ---

def create_pptx(slides_content):
    """Generates a real PowerPoint file."""
    prs = Presentation()
    for slide_data in slides_content:
        slide_layout = prs.slide_layouts[1] # Title and Content
        slide = prs.slides.add_slide(slide_layout)
        
        # Title
        title = slide.shapes.title
        title.text = slide_data.get('title', 'Untitled')
        
        # Content
        content = slide.placeholders[1]
        content.text = slide_data.get('body', '')
        
    binary_output = io.BytesIO()
    prs.save(binary_output)
    return binary_output.getvalue()

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, safe_text)
    return pdf.output(dest="S").encode("latin-1")

def web_search(query):
    try:
        results = DDGS().text(query, max_results=4)
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except: return "Web search unavailable."

# --- 4. LOGIC CORE (The "Brain") ---

def generate_clarifications(mission, context):
    """The Interviewer: Asks questions to sharpen the brief."""
    prompt = f"""
    CONTEXT: {context}
    MISSION: {mission}
    TASK: Ask 3 critical clarifying questions to ensure this mission succeeds. 
    Output purely the questions, numbered 1-3.
    """
    resp = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "system", "content": prompt}]
    )
    return resp.choices[0].message.content

def run_chief_swarm(protocol, mission, answers, context, image_data=None):
    results = {}
    
    # 1. RESEARCH PHASE
    with st.status("🕵️ Chief of Staff: Gathering Intelligence...", expanded=True) as status:
        web_intel = web_search(f"{mission} industry trends stats")
        status.write("Found Market Data")
        
        # 2. STRATEGY PHASE
        status.write("🧠 Synthesizing Strategy...")
        full_context = f"MISSION: {mission}\nUSER ANSWERS: {answers}\nINTEL: {web_intel}\nCONTEXT: {context}"
        
        strat_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"Execute Protocol: {protocol}. \nCONTEXT: {full_context}. \nOutput: Detailed Strategic Brief in Markdown."}]
        )
        results['Strategy_Brief.md'] = strat_resp.choices[0].message.content
        
        # 3. ARTIFACT PHASE (PPTX / ASSETS)
        status.write("💼 Building Executive Artifacts...")
        
        if "Presentation" in protocol or "Launch" in protocol:
            # Generate Slide Content Structure
            slide_prompt = f"Convert this strategy into 5 PowerPoint slides. Output JSON format: [{{'title': '...', 'body': '...'}}]. \nSTRATEGY: {results['Strategy_Brief.md'][:2000]}"
            slide_resp = client.chat.completions.create(
                model="gpt-4o", response_format={ "type": "json_object" },
                messages=[{"role": "system", "content": slide_prompt}]
            )
            import json
            slides_json = json.loads(slide_resp.choices[0].message.content)
            
            # Build PPTX
            pptx_bytes = create_pptx(slides_json.get('slides', []))
            results['Executive_Deck.pptx'] = pptx_bytes

        status.update(label="✅ Mission Complete", state="complete")
        
    return results

# --- 5. INTERFACE ---
with st.sidebar:
    st.title("🧬 Brand DNA")
    brand_name = st.text_input("Org Name", placeholder="Apex Media")
    north_star = st.text_area("North Star Goal", placeholder="Growth...")

st.title("👔 Studio V19: Chief of Staff")

# INPUT
col1, col2 = st.columns([2, 1])
with col1:
    mission_input = st.text_area("Mission Objective", placeholder="e.g. Pitch the Q3 Marketing Plan to the Board...", height=100)
    uploaded_file = st.file_uploader("Intel", type=["pdf", "docx", "txt"])
with col2:
    st.info("💡 **Interviewer Mode**")
    use_clarification = st.toggle("Clarify before executing?", value=True)
    protocol = st.selectbox("Protocol:", [
        "💼 Executive Strategy Presentation (.pptx)",
        "🚀 Full Product Launch",
        "📢 Crisis Response Suite",
        "🎥 Video Production Bible"
    ])

# ACTION
if st.button("🚀 INITIATE", type="primary", use_container_width=True):
    if not mission_input:
        st.warning("Mission Objective Required.")
        st.stop()
        
    st.session_state.pending_mission = {
        "protocol": protocol,
        "mission": mission_input,
        "context": f"Brand: {brand_name}. Goal: {north_star}."
    }
    
    if use_clarification:
        questions = generate_clarifications(mission_input, st.session_state.pending_mission['context'])
        st.session_state.clarifying_questions = questions
    else:
        # Skip straight to execution
        outputs = run_chief_swarm(protocol, mission_input, "N/A", st.session_state.pending_mission['context'])
        st.session_state.history.insert(0, outputs)
        st.rerun()

# CLARIFICATION LOOP
if st.session_state.clarifying_questions:
    st.divider()
    st.subheader("🕵️ The Interviewer")
    st.markdown(st.session_state.clarifying_questions)
    user_answers = st.text_area("Your Answers (Provide details for better results):")
    
    if st.button("✅ Confirm & Execute"):
        outputs = run_chief_swarm(
            st.session_state.pending_mission['protocol'], 
            st.session_state.pending_mission['mission'], 
            user_answers, 
            st.session_state.pending_mission['context']
        )
        st.session_state.history.insert(0, outputs)
        st.session_state.clarifying_questions = None # Reset
        st.rerun()

# OUTPUTS
if st.session_state.history:
    st.divider()
    latest = st.session_state.history[0]
    
    st.success("✅ Output Ready")
    
    # Bundle Download
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for key, val in latest.items():
            if key.endswith('.pptx'):
                zip_file.writestr(key, val) # Binary
            elif key.endswith('.md'):
                zip_file.writestr(key, val) # Text
                try: zip_file.writestr(key.replace('.md', '.pdf'), create_pdf(val))
                except: pass
                
    st.download_button("📦 Download Chief Bundle (.ZIP)", zip_buffer.getvalue(), "Chief_Artifacts.zip", "application/zip", type="primary")

    # Preview
    for key, val in latest.items():
        if key.endswith('.md'):
            with st.expander(f"📄 Preview: {key}"):
                st.markdown(val)
