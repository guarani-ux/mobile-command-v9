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
st.set_page_config(page_title="Studio V17: Omni-Tool", layout="wide", page_icon="👁️")

# CSS: High-Leverage UI
st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem;}
    .stButton button {height: 3.5em; font-weight: bold; border-radius: 6px; background-color: #FF4B4B; color: white;}
    .brand-sidebar {background-color: #f0f2f6; padding: 20px; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION & MEMORY ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.sidebar.text_input("🔑 API Key", type="password")
    if not api_key: st.stop()

client = OpenAI(api_key=api_key)

if "history" not in st.session_state:
    st.session_state.history = []

# --- 3. HELPER FUNCTIONS ---
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, safe_text)
    return pdf.output(dest="S").encode("latin-1")

def read_file(uploaded_file):
    if not uploaded_file: return ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            return "".join([p.extract_text() for p in PyPDF2.PdfReader(uploaded_file).pages])
        elif uploaded_file.name.endswith('.docx'):
            return "\n".join([p.text for p in Document(uploaded_file).paragraphs])
        elif uploaded_file.name.endswith('.txt') or uploaded_file.name.endswith('.md'):
            return uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file).to_markdown(index=False)
    except: return ""

# --- 4. THE BRAND DNA SIDEBAR (Context Layer) ---
with st.sidebar:
    st.title("🧬 Brand DNA")
    st.info("Persistent Context Layer")
    
    with st.expander("Identity & Voice", expanded=True):
        brand_name = st.text_input("Org Name", placeholder="Apex Media")
        brand_voice = st.text_area("Tone of Voice", placeholder="Professional, Witty...", height=70)
        brand_audience = st.text_area("Target Audience", placeholder="C-Suite, Gen Z...", height=70)
    
    with st.expander("Strategic Goals"):
        north_star = st.text_area("North Star Goal", placeholder="Increase Q3 Revenue...", height=70)

# --- 5. THE OMNI-SWARM ENGINE ---
def run_omni_swarm(protocol, objective, context, image_data=None):
    results = {}
    
    # MASTER CONTEXT BLOCK
    dna_block = f"""
    ORGANIZATION: {brand_name}
    TONE: {brand_voice}
    AUDIENCE: {brand_audience}
    GOAL: {north_star}
    CONTEXT: {context}
    """
    
    with st.status(f"👁️ Executing Protocol: {protocol}", expanded=True) as status:
        
        # --- BRANCH A: VISUAL INTELLIGENCE (The Eye) ---
        if image_data:
            status.write("👁️ Phase 1: Visual Analysis...")
            base64_img = encode_image(image_data)
            
            v_prompts = {
                "👁️ Scout: Location & Safety": "Analyze for: 1. Power/Logistics, 2. Safety Hazards, 3. Lighting Conditions.",
                "👁️ Director: Set Vibe Check": "Analyze lighting/color temp. Does it match our Brand Tone? Suggest improvements.",
                "👁️ OCR: Digitize Document": "Transcribe exactly. Summarize risks.",
                "General Vision": "Analyze this image in the context of our mission."
            }
            v_instruction = v_prompts.get(protocol, v_prompts["General Vision"])
            
            vis_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": f"{dna_block}\nTASK: {v_instruction}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}},
                    ]}
                ]
            )
            results['Visual_Report.md'] = vis_resp.choices[0].message.content
        
        # --- BRANCH B: TEXT STRATEGY (The Brain) ---
        else:
            status.write("🧠 Phase 1: Strategic Synthesis...")
            
            # DYNAMIC PROMPT SELECTION
            text_prompts = {
                "🚀 Full Campaign Launch": "Generate 3 files: 1. Strategic Brief (aligned to North Star), 2. Production Script, 3. Social Distribution Plan.",
                "📢 Crisis Response": "Generate: 1. Public Holding Statement, 2. Internal Memo, 3. FAQ for Stakeholders.",
                "🎥 Video Production Bible": "Generate: 1. Shooting Script (AV Format), 2. Shot List Table, 3. Call Sheet Draft.",
                "💻 Digital/Jira Stack": "Generate: 1. FRD Outline, 2. CSV Table of Jira User Stories (Summary, Desc, Priority)."
            }
            sys_instruction = text_prompts.get(protocol, "Generate a comprehensive strategic response.")
            
            strat_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": f"CONTEXT: {dna_block}\nTASK: {sys_instruction}"}]
            )
            results['Strategy_Core.md'] = strat_resp.choices[0].message.content

            # --- BRANCH C: GENERATIVE ART (Optional) ---
            if "Campaign" in protocol or "Video" in protocol:
                status.write("🎨 Phase 2: Visualizing Concept...")
                try:
                    art_prompt = client.chat.completions.create(
                        model="gpt-4o", 
                        messages=[{"role": "system", "content": f"Create DALL-E 3 prompt for: {objective}"}]
                    ).choices[0].message.content
                    img_url = client.images.generate(model="dall-e-3", prompt=art_prompt, size="1024x1024").data[0].url
                    results['Concept_Art_URL'] = img_url
                except: pass

        status.update(label="✅ Protocol Complete", state="complete", expanded=False)
        
    return results

# --- 6. MAIN INTERFACE ---
st.title("👁️ Studio V17: Omni-Tool")

# TABS FOR INPUT MODES
tab_text, tab_vision = st.tabs(["📝 Command (Text)", "👁️ Vision (Camera)"])

with tab_text:
    mission_brief = st.text_area("Mission Objective", placeholder="e.g. Launch the Fall Campaign...", height=100)
    uploaded_file = st.file_uploader("Attach Intel", type=["pdf", "docx", "txt"])

with tab_vision:
    camera_img = st.camera_input("Visual Scan")
    uploaded_img = st.file_uploader("Upload Image", type=["jpg", "png"])
    visual_context = st.text_input("Visual Query", placeholder="e.g. Is this location safe?")

st.divider()

# PROTOCOL SELECTOR (Restored)
protocol = st.selectbox("Select Protocol:", [
    "🚀 Full Campaign Launch",
    "🎥 Video Production Bible",
    "📢 Crisis Response",
    "💻 Digital/Jira Stack",
    "👁️ Scout: Location & Safety",
    "👁️ Director: Set Vibe Check",
    "👁️ OCR: Digitize Document"
])

# ACTION BUTTON
if st.button("⚡ EXECUTE PROTOCOL", type="primary", use_container_width=True):
    # Determine Input Source
    active_img = camera_img if camera_img else uploaded_img
    active_text = mission_brief if mission_brief else visual_context
    file_txt = read_file(uploaded_file)
    
    if active_img and "👁️" not in protocol:
        st.warning("⚠️ You have an image but selected a Text Protocol. Switching to Visual Analysis...")
    
    outputs = run_omni_swarm(protocol, active_text, file_txt, active_img)
    
    # Save to History
    st.session_state.history.insert(0, {"protocol": protocol, "outputs": outputs})
    st.rerun()

# --- 7. HISTORY & OUTPUTS ---
st.subheader("🗂️ Mission Log")

if st.session_state.history:
    for i, item in enumerate(st.session_state.history):
        with st.expander(f"{item['protocol']} (Mission {len(st.session_state.history)-i})"):
            
            ops = item['outputs']
            
            # Show Art
            if 'Concept_Art_URL' in ops:
                st.image(ops['Concept_Art_URL'], caption="Generated Asset", width=300)
            
            # Show Text/Markdown
            for key, val in ops.items():
                if key.endswith('.md'):
                    st.markdown(val)
            
            # ZIP DOWNLOADER
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for key, val in ops.items():
                    if key.endswith('.md'):
                        zip_file.writestr(key, val)
                        # Auto-convert to PDF for the bundle
                        try:
                            pdf_bytes = create_pdf(val)
                            zip_file.writestr(key.replace('.md', '.pdf'), pdf_bytes)
                        except: pass
            
            st.download_button(
                "📦 Download Mission Bundle (.ZIP)", 
                zip_buffer.getvalue(), 
                f"Mission_{len(st.session_state.history)-i}.zip", 
                "application/zip"
            )
else:
    st.info("Ready for input.")
