import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
from fpdf import FPDF
from duckduckgo_search import DDGS
import base64
import io
import zipfile

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="Studio V18: The Nexus", layout="wide", page_icon="📡")

# CSS: Nexus UI (Futuristic & Clean)
st.markdown("""
    <style>
    .main .block-container {padding-top: 1rem;}
    .stButton button {height: 3.5em; font-weight: 800; border-radius: 8px; background-color: #0068C9; color: white;}
    .brand-sidebar {background-color: #f8f9fa; padding: 15px; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION & STATE ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.sidebar.text_input("🔑 API Key", type="password")
    if not api_key: st.stop()

client = OpenAI(api_key=api_key)

# Initialize Session State
if "history" not in st.session_state: st.session_state.history = []
if "current_draft" not in st.session_state: st.session_state.current_draft = ""
if "refinement_mode" not in st.session_state: st.session_state.refinement_mode = False

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

def web_search(query):
    """The Eye of the Web: Fetches live data."""
    try:
        results = DDGS().text(query, max_results=3)
        return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
    except:
        return "Web search unavailable (Rate Limit)."

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

# --- 4. BRAND DNA (Persistent Context) ---
with st.sidebar:
    st.title("🧬 Brand DNA")
    with st.expander("Identity", expanded=True):
        brand_name = st.text_input("Org Name", placeholder="Apex Media")
        brand_voice = st.text_area("Tone", placeholder="Professional, Witty...", height=70)
        north_star = st.text_area("North Star Goal", placeholder="Increase Revenue...", height=70)

# --- 5. THE NEXUS ENGINE ---
def run_nexus_swarm(protocol, user_input, file_data, image_data=None, audio_data=None, use_web=False):
    results = {}
    
    # 1. CONTEXT ASSEMBLY
    dna_block = f"ORG: {brand_name}\nTONE: {brand_voice}\nGOAL: {north_star}"
    
    # 2. LIVE INTEL (Web Search)
    web_context = ""
    if use_web:
        with st.status("🌍 Agent 1: Scanning Global Intel...", expanded=True) as status:
            search_q = f"{user_input} {brand_name} industry trends"
            web_context = web_search(search_q)
            status.write(f"Found intel: {web_context[:100]}...")
            status.update(label="✅ Intel Secured", state="complete")

    # 3. TRANSCRIPTION (If Audio)
    audio_transcript = ""
    if audio_data:
        with st.spinner("🎙️ Transcribing Command..."):
            audio_transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_data
            ).text

    # 4. MASTER PROMPT
    final_input = f"{user_input}\n{audio_transcript}"
    full_context = f"{dna_block}\nWEB INTEL: {web_context}\nFILE DATA: {file_data}\nCONTEXT: {final_input}"

    with st.status(f"📡 Executing Protocol: {protocol}", expanded=True) as status:
        
        # --- VISION BRANCH ---
        if image_data:
            status.write("👁️ Agent 2: Visual Analysis...")
            base64_img = encode_image(image_data)
            v_prompt = "Analyze this image in detail regarding the objective."
            
            vis_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": f"{full_context}\nTASK: {v_prompt}"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}},
                    ]}
                ]
            )
            results['Visual_Report.md'] = vis_resp.choices[0].message.content
        
        # --- STRATEGY BRANCH ---
        else:
            status.write("🧠 Agent 2: Strategic Synthesis...")
            prompts = {
                "🚀 Full Campaign Launch": "Generate: 1. Strategic Brief (Data-Backed), 2. Script, 3. Social Plan.",
                "📢 Crisis Response": "Generate: 1. Holding Statement, 2. Internal Memo, 3. FAQ.",
                "🎥 Video Production Bible": "Generate: 1. Script (AV), 2. Shot List, 3. Call Sheet.",
                "💻 Digital/Jira Stack": "Generate: 1. FRD, 2. Jira Tickets (CSV format)."
            }
            task = prompts.get(protocol, "Generate comprehensive response.")
            
            strat_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": f"CONTEXT: {full_context}\nTASK: {task}"}]
            )
            results['Strategy_Core.md'] = strat_resp.choices[0].message.content

            # --- ART BRANCH ---
            if "Campaign" in protocol or "Video" in protocol:
                status.write("🎨 Agent 3: Generative Art...")
                try:
                    art_p = client.chat.completions.create(
                        model="gpt-4o", 
                        messages=[{"role": "system", "content": f"Create DALL-E 3 prompt for: {user_input}"}]
                    ).choices[0].message.content
                    img_url = client.images.generate(model="dall-e-3", prompt=art_p, size="1024x1024").data[0].url
                    results['Concept_Art_URL'] = img_url
                except: pass

        status.update(label="✅ Nexus Cycle Complete", state="complete")
    
    return results

# --- 6. NEXUS INTERFACE ---
st.title("📡 Studio V18: The Nexus")

# INPUT HUB (Tabs for Modes)
tab_cmd, tab_vis, tab_voice = st.tabs(["📝 Text Command", "👁️ Vision", "🎙️ Voice Uplink"])

with tab_cmd:
    mission_text = st.text_area("Mission Objective", placeholder="e.g. Launch Q3 Campaign...", height=100)
    uploaded_file = st.file_uploader("Attach Files", type=["pdf", "docx", "txt"])
    use_web_search = st.checkbox("🌍 Enable Live Web Research", value=True)

with tab_vis:
    camera_img = st.camera_input("Scan Target")
    uploaded_img = st.file_uploader("Upload Visual", type=["jpg", "png"])

with tab_voice:
    audio_cmd = st.audio_input("Record Command")

st.divider()

col_a, col_b = st.columns([3, 1])
with col_a:
    protocol = st.selectbox("Select Protocol:", [
        "🚀 Full Campaign Launch",
        "🎥 Video Production Bible",
        "📢 Crisis Response",
        "💻 Digital/Jira Stack",
        "👁️ Scout: Location & Safety",
        "👁️ Director: Set Vibe Check"
    ])
with col_b:
    st.write("") # Spacer
    if st.button("⚡ EXECUTE", type="primary", use_container_width=True):
        # Determine inputs
        active_img = camera_img if camera_img else uploaded_img
        active_txt = mission_text
        
        # Run Swarm
        outputs = run_nexus_swarm(protocol, active_txt, read_file(uploaded_file), active_img, audio_cmd, use_web_search)
        
        # Save to Session
        st.session_state.current_draft = outputs
        st.session_state.refinement_mode = True
        st.rerun()

# --- 7. REFINEMENT LAB (The New Feature) ---
if st.session_state.refinement_mode and st.session_state.current_draft:
    st.subheader("🧪 Refinement Lab")
    
    draft = st.session_state.current_draft
    
    # DISPLAY CURRENT RESULTS
    if 'Concept_Art_URL' in draft:
        st.image(draft['Concept_Art_URL'], width=400)
    
    if 'Strategy_Core.md' in draft:
        st.markdown(draft['Strategy_Core.md'])
        
        # REFINEMENT CHAT
        refine_q = st.chat_input("Tweak this draft (e.g., 'Make the tone punchier' or 'Add a TikTok section')")
        if refine_q:
            with st.spinner("🔄 Refining Strategy..."):
                new_resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "assistant", "content": draft['Strategy_Core.md']},
                        {"role": "user", "content": f"Refine the above text. Request: {refine_q}"}
                    ]
                )
                st.session_state.current_draft['Strategy_Core.md'] = new_resp.choices[0].message.content
                st.rerun()

    # DOWNLOAD BUNDLE
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for key, val in st.session_state.current_draft.items():
            if key.endswith('.md'):
                zip_file.writestr(key, val)
                try: zip_file.writestr(key.replace('.md', '.pdf'), create_pdf(val))
                except: pass
    
    st.download_button("📦 Download Final Bundle", zip_buffer.getvalue(), "Nexus_Bundle.zip", "application/zip", type="primary")
