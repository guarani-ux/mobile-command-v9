import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
from fpdf import FPDF
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Studio V13: Strategy Core", layout="centered", page_icon="👁️")

# CSS: High-Contrast & Mobile Optimization
st.markdown("""
    <style>
    .stTextArea textarea {font-size: 16px !important;}
    .stSelectbox div[data-baseweb="select"] > div {font-size: 16px !important;}
    .stButton button {height: 3.5em !important; font-weight: 800; border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)

st.title("👁️ Studio V13: Strategy Core")

# --- 2. AUTHENTICATION ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.text_input("🔑 Enter OpenAI API Key:", type="password")
    if not api_key:
        st.stop()

client = OpenAI(api_key=api_key)

# --- 3. HELPER FUNCTIONS ---
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

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

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, safe_text)
    return pdf.output(dest="S").encode("latin-1")

# --- 4. SESSION STATE ---
if "output_log" not in st.session_state:
    st.session_state.output_log = []

# --- 5. THE INTERFACE ---

st.info("👇 **Phase 1: Strategic Input**")

# TAB SYSTEM: Split Text Intel vs Visual Intel
tab1, tab2 = st.tabs(["📝 Strategy Briefing", "👁️ Visual Intel (The Eye)"])

with tab1:
    # --- DUAL GOAL INPUT SYSTEM ---
    st.write("**1. The Campaign (Tactical)**")
    campaign_objective = st.text_area("What are we building/launching?", placeholder="e.g. A 30-second YouTube ad series...", height=100)
    
    st.write("**2. The Organization (Strategic)**")
    org_goal = st.text_input("What is the larger business goal?", placeholder="e.g. Increase Q3 Revenue by 10% OR Brand Awareness")
    
    uploaded_file = st.file_uploader("📂 Upload Supporting Docs", type=["pdf", "docx", "txt", "csv"])

with tab2:
    st.warning("⚠️ **Camera Active.** Analyze physical reality.")
    camera_img = st.camera_input("Scan Target")
    uploaded_img = st.file_uploader("Or Upload Photo", type=["jpg", "png", "jpeg"])
    visual_prompt = st.text_input("Visual Query:", placeholder="e.g. 'Analyze safety risks' or 'Describe lighting conditions'")

st.write("---")
st.info("👇 **Phase 2: Protocol Selection**")

# PROTOCOL LIST
protocol = st.selectbox("Activate Protocol:", [
    # --- STRATEGY ---
    "📝 Strategy: Strategic Project Brief (Goal-Aligned)",
    
    # --- VISUAL ---
    "👁️ Scout: Location Safety & Logistics Analysis",
    "👁️ Director: Set Vibe & Lighting Critique",
    "👁️ Stylist: Wardrobe & Color Analysis",
    "👁️ OCR: Digitize Paper Contract/Script",
    
    # --- CREATIVE / EXECUTION ---
    "🎨 CD: DALL-E 3 Concept Art",
    "📄 PA: Daily Call Sheet (PDF)",
    "📋 PA: Load-in Checklist",
    "🚀 Digital: Product Launch Stack",
    "💼 Exec: Strategy Deck"
])

# --- 6. EXECUTION ENGINE ---
if st.button("🚀 EXECUTE", type="primary", use_container_width=True):
    
    # A. VISUAL ANALYSIS PATH
    if (camera_img or uploaded_img) and "👁️" in protocol:
        active_img = camera_img if camera_img else uploaded_img
        base64_image = encode_image(active_img)
        
        with st.spinner("👁️ The Eye is Analyzing..."):
            v_prompts = {
                "👁️ Scout: Location Safety & Logistics Analysis": "Act as a veteran Location Manager. Analyze this image for: 1. Power access, 2. Trip hazards, 3. Lighting conditions, 4. Load-in feasibility.",
                "👁️ Director: Set Vibe & Lighting Critique": "Act as a Cinematographer. Analyze the lighting. Describe color temperature, practical sources, and suggest 3 enhancements.",
                "👁️ Stylist: Wardrobe & Color Analysis": "Act as a Costume Designer. Analyze clothing/colors. Do they clash? What is the tone? Suggest accessories.",
                "👁️ OCR: Digitize Paper Contract/Script": "Transcribe this document exactly. Fix typos. Summarize key points at the bottom."
            }
            default_v_prompt = f"Analyze this image. Context: {visual_prompt}"
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": v_prompts.get(protocol, default_v_prompt)},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        ],
                    }
                ],
                max_tokens=1000,
            )
            result = response.choices[0].message.content
            
            st.write("---")
            st.image(active_img, caption="Target Acquired", width=300)
            st.markdown(result)
            try:
                pdf_bytes = create_pdf(result)
                st.download_button("📄 Download Report (PDF)", pdf_bytes, "visual_intel.pdf", mime="application/pdf")
            except:
                st.download_button("💾 Download Text", result, "visual_intel.md")

    # B. TEXT / GENERATIVE PATH
    else:
        file_content = read_file(uploaded_file)
        full_context = f"""
        CAMPAIGN OBJECTIVE (Tactical): {campaign_objective}
        ORGANIZATION GOAL (Strategic): {org_goal}
        FILE DATA: {file_content}
        """
        
        if protocol == "🎨 CD: DALL-E 3 Concept Art":
            with st.spinner("🎨 Generating Art..."):
                design_prompt = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[{"role": "system", "content": f"Create DALL-E 3 prompt for: {full_context}"}]
                ).choices[0].message.content
                
                img_resp = client.images.generate(model="dall-e-3", prompt=design_prompt, size="1024x1024")
                st.image(img_resp.data[0].url)
        
        else:
            # --- UPDATED PROMPTS WITH ALIGNMENT CHECK ---
            text_prompts = {
                "📝 Strategy: Strategic Project Brief (Goal-Aligned)": """
                Generate a Master Project Brief.
                CRITICAL STEP: First, evaluate if the 'Campaign Objective' actually supports the 'Organization Goal'.
                - If YES: Proceed.
                - If NO/WEAK: Include a '⚠️ STRATEGIC GAP WARNING' section at the top explaining the misalignment.
                
                Structure:
                1. STRATEGIC ALIGNMENT: How this campaign moves the Org Goal.
                2. EXECUTIVE SUMMARY (BLUF).
                3. TACTICAL DELIVERABLES (The 'What').
                4. SUCCESS METRICS (KPIs - tied to Org Goal).
                5. RISKS & MITIGATION.
                6. TIMELINE.
                """,
                "📄 PA: Daily Call Sheet (PDF)": "Generate a Call Sheet Table (Crew Call, Talent Call, Hospital, Lunch).",
                "📋 PA: Load-in Checklist": "Checklist for Camera, Audio, G&E, Crafty.",
                "🚀 Digital: Product Launch Stack": "FRD Outline, Tech Stack, Runbook.",
                "💼 Exec: Strategy Deck": "BLUF, SWOT, Roadmap."
            }
            
            system_instr = text_prompts.get(protocol, "Generate a detailed professional response.")
            
            with st.spinner("🧠 Strategizing..."):
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": f"ROLE: Elite Strategist. {system_instr} \n\nCONTEXT: {full_context}"}]
                )
                txt = resp.choices[0].message.content
                st.markdown(txt)
                
                # DUAL EXPORT
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("💾 Download .MD", txt, "output.md")
                with col2:
                    try:
                        pdf_bytes = create_pdf(txt)
                        st.download_button("📄 Download PDF", pdf_bytes, "output.pdf", mime="application/pdf")
                    except:
                        st.warning("PDF Generation failed (Text encoding). Use MD.")
