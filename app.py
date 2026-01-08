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
st.set_page_config(page_title="Studio V16: The War Room", layout="wide", page_icon="⚔️")

# CSS: Enterprise SaaS Aesthetic
st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem;}
    .stButton button {height: 3.5em; font-weight: bold; border-radius: 6px;}
    .brand-sidebar {background-color: #f0f2f6; padding: 20px; border-radius: 10px;}
    h1 {color: #1E1E1E;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION & SESSION STATE ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.sidebar.text_input("🔑 API Key", type="password")
    if not api_key: st.stop()

client = OpenAI(api_key=api_key)

# Initialize History (The "Memory")
if "history" not in st.session_state:
    st.session_state.history = []

# --- 3. HELPER FUNCTIONS ---
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
        elif uploaded_file.name.endswith('.txt'):
            return uploaded_file.read().decode("utf-8")
    except: return ""

# --- 4. THE BRAND DNA SIDEBAR (The Competitive Advantage) ---
with st.sidebar:
    st.title("🧬 Brand DNA")
    st.info("Set this once. It applies to ALL missions.")
    
    with st.expander("Identity & Voice", expanded=True):
        brand_name = st.text_input("Organization Name", placeholder="e.g. Apex Media")
        brand_voice = st.text_area("Brand Voice/Tone", placeholder="e.g. Professional, Witty, Authoritative...", height=100)
        brand_audience = st.text_area("Target Audience", placeholder="e.g. C-Suite Execs, Gen Z Gamers...", height=100)
    
    with st.expander("Strategic North Star"):
        north_star = st.text_area("Quarterly Goal", placeholder="e.g. Drive 20% leads via Video Series", height=100)
        
    st.divider()
    st.caption(f"Status: {'✅ DNA Active' if brand_name else '⚠️ DNA Missing'}")

# --- 5. THE SWARM ENGINE (Context-Aware) ---
def run_swarm(mission, brief, file_context):
    results = {}
    
    # SYSTEM PROMPT: INJECTING BRAND DNA
    dna_context = f"""
    ORGANIZATION: {brand_name}
    TONE OF VOICE: {brand_voice}
    TARGET AUDIENCE: {brand_audience}
    NORTH STAR GOAL: {north_star}
    """
    
    with st.status(f"⚔️ Executing Mission: {mission}", expanded=True) as status:
        
        # 1. COMMS STRATEGIST
        status.write("🧠 Phase 1: Strategic Alignment...")
        strat_prompt = f"Create a Strategic Brief for '{brief}'. Ensure strictly aligns with our DNA: {brand_voice}."
        strat_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"CONTEXT: {dna_context} {file_context}\nTASK: {strat_prompt}"}]
        )
        results['Strategy.md'] = strat_resp.choices[0].message.content
        
        # 2. CONTENT PRODUCER
        status.write("🎥 Phase 2: Production Assets...")
        prod_prompt = "Generate the Core Asset (Script/Article/Press Release) based on the Strategy."
        prod_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"CONTEXT: {dna_context}\nSTRATEGY: {results['Strategy.md'][:1000]}\nTASK: {prod_prompt}"}]
        )
        results['Production.md'] = prod_resp.choices[0].message.content
        
        # 3. GROWTH MARKETER
        status.write("📢 Phase 3: Distribution...")
        dist_prompt = "Generate Social Copy (LinkedIn/X/IG) and SEO Metadata."
        dist_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"CONTEXT: {dna_context}\nASSET: {results['Production.md'][:1000]}\nTASK: {dist_prompt}"}]
        )
        results['Distribution.md'] = dist_resp.choices[0].message.content
        
        status.update(label="✅ Mission Accomplished", state="complete", expanded=False)
        
    return results

# --- 6. MAIN WAR ROOM INTERFACE ---
st.title(f"⚔️ {brand_name if brand_name else 'Studio'} War Room")
st.caption("End-to-End Media Operations Center")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🚀 New Mission")
    mission_brief = st.text_area("What are we building today?", placeholder="e.g. A launch video for the new X500 product...", height=150)
    uploaded_file = st.file_uploader("Attach Intel (PDF/Docx)", type=["pdf", "docx", "txt"])
    
    if st.button("🔥 IGNITE SWARM", type="primary", use_container_width=True):
        if not brand_name:
            st.error("⚠️ Please define 'Brand DNA' in the sidebar first.")
        elif not mission_brief:
            st.warning("⚠️ Please enter a Mission Brief.")
        else:
            file_txt = read_file(uploaded_file)
            outputs = run_swarm("Custom Mission", mission_brief, file_txt)
            
            # Save to Session History
            st.session_state.history.insert(0, {"brief": mission_brief, "outputs": outputs})
            st.rerun()

with col2:
    st.subheader("🗂️ Mission History")
    if not st.session_state.history:
        st.info("No active missions.")
    else:
        for i, item in enumerate(st.session_state.history):
            with st.expander(f"Mission {len(st.session_state.history)-i}: {item['brief'][:30]}..."):
                # DOWNLOAD BUNDLE
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                    zip_file.writestr("Strategy.md", item['outputs']['Strategy.md'])
                    zip_file.writestr("Production.md", item['outputs']['Production.md'])
                    zip_file.writestr("Distribution.md", item['outputs']['Distribution.md'])
                
                st.download_button("📦 Download Bundle", zip_buffer.getvalue(), f"Mission_{len(st.session_state.history)-i}.zip", "application/zip")
                
                # PREVIEW
                tab_a, tab_b, tab_c = st.tabs(["Strategy", "Prod", "Dist"])
                with tab_a: st.markdown(item['outputs']['Strategy.md'])
                with tab_b: st.markdown(item['outputs']['Production.md'])
                with tab_c: st.markdown(item['outputs']['Distribution.md'])
