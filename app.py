import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
from fpdf import FPDF
import base64
import io
import zipfile

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="Studio V15: Media Engine", layout="centered", page_icon="🎬")

# CSS: Professional, Clean, High-Leverage
st.markdown("""
    <style>
    .stTextArea textarea {font-size: 16px !important;}
    .stButton button {height: 4em !important; font-weight: 800; border-radius: 8px; background-color: #0068C9; color: white;}
    div[data-testid="stStatusWidget"] {visibility: visible;}
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Studio V15: Media Engine")
st.caption("End-to-End: Comms • Production • Marketing")

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
    try:
        if uploaded_file.name.endswith('.pdf'):
            pdf = PyPDF2.PdfReader(uploaded_file)
            return "".join([p.extract_text() for p in pdf.pages])
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif uploaded_file.name.endswith('.txt') or uploaded_file.name.endswith('.md'):
            return uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file).to_markdown(index=False)
    except: return "Error reading file."

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, safe_text)
    return pdf.output(dest="S").encode("latin-1")

# --- 4. THE LIFECYCLE SWARM (The Brain) ---
def run_lifecycle_swarm(mission_type, objective, goal, context, image_data=None):
    results = {}
    
    # SYSTEM PROMPT INJECTION (The "North Star")
    base_instruction = f"""
    PROJECT: {mission_type}
    OBJECTIVE: {objective}
    NORTH STAR GOAL: {goal}
    CONTEXT: {context}
    """

    with st.status(f"🚀 Initializing Lifecycle Swarm: {mission_type}", expanded=True) as status:
        
        # --- PHASE 1: COMMS & STRATEGY ---
        status.write("🧠 Phase 1: Communications Strategy...")
        comms_prompt = f"""
        Act as a Communications Director. Based on the NORTH STAR GOAL, generate a Strategic Brief.
        Include:
        1. Core Messaging Framework (Key Messages).
        2. Audience Persona Analysis.
        3. Risk/Crisis Mitigation.
        4. Success KPIs.
        """
        comms_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"{base_instruction}\n\nTASK: {comms_prompt}"}]
        )
        results['1_Comms_Strategy.md'] = comms_resp.choices[0].message.content
        results['1_Comms_Strategy.pdf'] = create_pdf(results['1_Comms_Strategy.md'])

        # --- PHASE 2: VIDEO PRODUCTION ---
        status.write("🎥 Phase 2: Video Production Assets...")
        prod_prompt = f"""
        Act as an Executive Producer. Based on the Comms Strategy, generate production assets.
        1. A Video Script (AV Format) aligned with the Key Messages.
        2. A Shot List / Visual Guide.
        3. A detailed Production Timeline.
        """
        prod_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"{base_instruction}\n\nSTRATEGY CONTEXT: {results['1_Comms_Strategy.md'][:500]}\n\nTASK: {prod_prompt}"}]
        )
        results['2_Production_Bible.md'] = prod_resp.choices[0].message.content
        
        # (Optional Visual Generation)
        status.write("🎨 Phase 2b: Visualizing Concept...")
        try:
            art_prompt = client.chat.completions.create(
                model="gpt-4o", 
                messages=[{"role": "system", "content": f"Create a DALL-E 3 prompt for a key visual frame of this video: {objective}"}]
            ).choices[0].message.content
            img_url = client.images.generate(model="dall-e-3", prompt=art_prompt, size="1024x1024").data[0].url
            results['concept_art_url'] = img_url
        except: pass

        # --- PHASE 3: MARKETING & DISTRIBUTION ---
        status.write("📢 Phase 3: Marketing Distribution...")
        mktg_prompt = f"""
        Act as a Digital Marketing Lead. Plan the distribution.
        1. Social Media Copy (LinkedIn, IG, X) - customized for each platform.
        2. Email Newsletter Blurb.
        3. YouTube Metadata (Title, Description, Tags for SEO).
        """
        mktg_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"{base_instruction}\n\nTASK: {mktg_prompt}"}]
        )
        results['3_Marketing_Plan.md'] = mktg_resp.choices[0].message.content

        status.update(label="✅ Lifecycle Complete", state="complete", expanded=False)
    
    return results

# --- 5. INTERFACE (Input Layer) ---

st.info("📡 **Campaign Command**")

# DUAL INPUT (Strategy Core)
col1, col2 = st.columns([3, 1])
with col1:
    objective = st.text_area("Campaign Objective", placeholder="e.g. Launch the 'Future of Energy' video series...", height=100)
    goal = st.text_input("North Star Goal (The 'Why')", placeholder="e.g. Increase Brand Sentiment by 15%")
with col2:
    uploaded_file = st.file_uploader("📎 Research", type=["pdf", "docx", "txt"])
    uploaded_img = st.file_uploader("📷 Visuals", type=["jpg", "png"])

# LIFECYCLE SELECTOR
mission = st.selectbox("Select Operation Type:", [
    "🚀 Full Campaign Launch (End-to-End)",
    "📢 Crisis / PR Response",
    "🎥 Content Series Production",
    "🤝 Internal Comms & Town Hall"
])

# --- 6. EXECUTION ---
if st.button("⚡ IGNITE ENGINE", type="primary", use_container_width=True):
    if not objective:
        st.warning("⚠️ Objective Required")
        st.stop()
        
    context = read_file(uploaded_file)
    
    # RUN SWARM
    outputs = run_lifecycle_swarm(mission, objective, goal, context, uploaded_img)
    
    st.divider()
    
    # VISUAL PROOF
    if 'concept_art_url' in outputs:
        st.image(outputs['concept_art_url'], caption="Campaign Visual Key")

    # PREVIEW TABS
    tab1, tab2, tab3 = st.tabs(["🧠 Comms Strategy", "🎥 Production Bible", "📢 Marketing Plan"])
    with tab1: st.markdown(outputs['1_Comms_Strategy.md'])
    with tab2: st.markdown(outputs['2_Production_Bible.md'])
    with tab3: st.markdown(outputs['3_Marketing_Plan.md'])

    # ZIP PACKAGE
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr("01_Comms_Strategy.md", outputs['1_Comms_Strategy.md'])
        zip_file.writestr("01_Comms_Strategy.pdf", outputs['1_Comms_Strategy.pdf'])
        zip_file.writestr("02_Production_Bible.md", outputs['2_Production_Bible.md'])
        zip_file.writestr("03_Marketing_Plan.md", outputs['3_Marketing_Plan.md'])
            
    st.download_button(
        label="📦 DOWNLOAD PROJECT BUNDLE (.ZIP)",
        data=zip_buffer.getvalue(),
        file_name="Campaign_Assets.zip",
        mime="application/zip",
        use_container_width=True
    )
