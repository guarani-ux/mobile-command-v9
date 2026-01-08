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
from datetime import datetime
import concurrent.futures

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Studio V27: Final Prime", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    .stButton button {height: 3.5em; font-weight: 800; border-radius: 8px; background-color: #0E1117; color: white; border: 1px solid #333;}
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
if "current_result" not in st.session_state: st.session_state.current_result = None

# --- 3. HELPER FUNCTIONS ---
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def create_ics(events_data):
    c = Calendar()
    for e in events_data:
        event = Event()
        event.name = e.get('summary', 'Task')
        try: event.begin = e.get('date', datetime.now().strftime("%Y-%m-%d"))
        except: event.begin = datetime.now().strftime("%Y-%m-%d")
        c.events.add(event)
    return str(c).encode('utf-8')

def create_audio(text):
    try: return client.audio.speech.create(model="tts-1", voice="onyx", input=text[:4096]).content
    except: return None

def create_pptx(slides_content):
    prs = Presentation()
    for slide_data in slides_content:
        layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(layout)
        slide.shapes.title.text = slide_data.get('title', 'Untitled')
        slide.placeholders[1].text = slide_data.get('body', '')
    out = io.BytesIO()
    prs.save(out)
    return out.getvalue()

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest="S").encode("latin-1")

def web_search(query):
    try: return "\n".join([f"- {r['title']}: {r['body']}" for r in DDGS().text(query, max_results=2)])
    except: return "Web search offline."

def read_file(uploaded_file):
    if not uploaded_file: return ""
    try:
        if uploaded_file.name.endswith('.pdf'): return "".join([p.extract_text() for p in PyPDF2.PdfReader(uploaded_file).pages])
        elif uploaded_file.name.endswith('.docx'): return "\n".join([p.text for p in Document(uploaded_file).paragraphs])
        elif uploaded_file.name.endswith('.txt'): return uploaded_file.read().decode("utf-8")
    except: return ""

def analyze_vision(image_data, prompt):
    if not image_data: return ""
    b64_img = encode_image(image_data)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}]}]
    )
    return f"VISUAL INTEL: {resp.choices[0].message.content}"

def generate_art(prompt):
    try:
        art_p = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": f"Create DALL-E 3 prompt for: {prompt}"}]).choices[0].message.content
        return client.images.generate(model="dall-e-3", prompt=art_p, size="1024x1024").data[0].url
    except: return None

# --- 4. THE PRIME ENGINE (Parallel + Recursive) ---

def run_prime_swarm(mission, protocol, context, image_data, voice_transcript, req_outputs, depth):
    results = {}
    
    with st.status(f"💎 Executing {protocol} ({depth})...", expanded=True) as status:
        
        # --- PHASE 1: SENSORY (Parallel) ---
        status.write("👁️ Phase 1: Sensory Uplink (Web + Vision)...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_web = executor.submit(web_search, f"{mission} {protocol} trends")
            future_vis = executor.submit(analyze_vision, image_data, f"Analyze for {protocol} context.")
            intel = future_web.result()
            visual_analysis = future_vis.result()
            
        # --- PHASE 2: STRATEGY (Recursive Oracle Loop) ---
        status.write(f"🧠 Phase 2: Strategic Synthesis (Oracle Loop)...")
        
        protocol_prompts = {
            "Custom Mission": "Follow objective.",
            "🚀 Campaign Launch": "Generate: 1. Strategy Brief, 2. Key Messages, 3. Channel Plan.",
            "📢 Crisis Response": "Generate: 1. Holding Statement, 2. Internal Memo, 3. FAQ.",
            "🎥 Video Production": "Generate: 1. AV Script, 2. Shot List, 3. Logistics.",
            "👁️ Scout: Safety": "Analyze location: Power, Hazards, Lighting, Logistics.",
            "👁️ Director: Vibe": "Analyze visual tone, color, lighting.",
            "💻 Digital Stack": "Generate: 1. Tech Specs, 2. User Stories, 3. Schema."
        }
        
        base_instr = protocol_prompts.get(protocol, "Execute Mission.")
        depth_instr = {"Draft": "Bullet points.", "Standard": "Professional depth.", "Deep Dive": "Extensive analysis."}[depth]
        
        full_context = f"PROTOCOL: {protocol}\nMISSION: {mission}\nVOICE: {voice_transcript}\nINTEL: {intel}\n{visual_analysis}\nCONTEXT: {context}\nINSTRUCTION: {base_instr} {depth_instr}"
        
        # THE ORACLE LOOP (Restored from V21)
        current_draft = ""
        quality_score = 0
        attempts = 0
        max_attempts = 2 if depth == "Deep Dive" else 1 # Only loop on Deep Dive to save time/tokens
        
        while attempts < max_attempts:
            attempts += 1
            # 1. Draft
            draft_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an Elite Media Strategist. Output Markdown."}, 
                    {"role": "user", "content": f"Refine: {current_draft}" if current_draft else full_context}
                ]
            )
            current_draft = draft_resp.choices[0].message.content
            
            # 2. Score (Self-Correction)
            if max_attempts > 1:
                score_resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": f"Rate 0-100 on impact/clarity. Output ONLY number. Text: {current_draft[:1000]}"}]
                )
                try: quality_score = int(score_resp.choices[0].message.content.strip())
                except: quality_score = 90
                status.write(f"Draft {attempts}: Quality Score {quality_score}/100")
        
        results['Master_Strategy.md'] = current_draft
        
        # --- PHASE 3: ARTIFACTS (Parallel) ---
        if req_outputs:
            status.write("📦 Phase 3: Manufacturing Assets...")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {}
                
                if "Simulation" in req_outputs:
                    futures['sim'] = executor.submit(client.chat.completions.create, model="gpt-4o", messages=[{"role": "system", "content": f"Simulate focus group reaction to: {current_draft[:1000]}"}])
                
                if "PPTX" in req_outputs:
                    futures['pptx'] = executor.submit(client.chat.completions.create, model="gpt-4o", response_format={ "type": "json_object" }, messages=[{"role": "system", "content": f"Convert to 5 slides JSON: {current_draft[:2000]}"}])
                
                if "Calendar" in req_outputs:
                    futures['ics'] = executor.submit(client.chat.completions.create, model="gpt-4o", response_format={ "type": "json_object" }, messages=[{"role": "system", "content": f"Extract dates to JSON: {current_draft[:2000]}"}])
                
                if "Audio" in req_outputs:
                    futures['mp3'] = executor.submit(create_audio, f"Briefing for {protocol}. {current_draft[:500]}")
                
                if "Art" in req_outputs:
                    futures['art'] = executor.submit(generate_art, f"{protocol} {mission}")

                if "CSV" in req_outputs:
                    futures['csv'] = executor.submit(client.chat.completions.create, model="gpt-4o", messages=[{"role": "system", "content": f"Extract CSV data table: {current_draft[:2000]}"}])

                for key, future in futures.items():
                    try:
                        res = future.result()
                        if key == 'sim': results['Simulation_Log.md'] = res.choices[0].message.content
                        elif key == 'pptx': results['Presentation.pptx'] = create_pptx(json.loads(res.choices[0].message.content).get('slides', []))
                        elif key == 'ics': results['Schedule.ics'] = create_ics(json.loads(res.choices[0].message.content).get('events', []))
                        elif key == 'mp3': results['Audio_Brief.mp3'] = res
                        elif key == 'art': results['Concept_Art_URL'] = res
                        elif key == 'csv': results['Project_Data.csv'] = res.choices[0].message.content
                    except: pass

        status.update(label="✅ Prime Cycle Complete", state="complete")
        
    return results

# --- 5. INTERFACE ---
with st.sidebar:
    st.title("🧬 Brand DNA")
    brand_name = st.text_input("Org Name", placeholder="Apex Media")
    north_star = st.text_area("North Star Goal", placeholder="Growth...")

st.title("💎 Studio V27: Final Prime")

# UNIFIED INPUT
tab_text, tab_vis, tab_voice = st.tabs(["📝 Mission Control", "👁️ Vision Uplink", "🎙️ Voice Command"])
with tab_text:
    protocol = st.selectbox("Select Protocol:", [
        "Custom Mission",
        "🚀 Campaign Launch",
        "📢 Crisis Response",
        "🎥 Video Production",
        "👁️ Scout: Safety",
        "👁️ Director: Vibe",
        "💻 Digital Stack"
    ])
    mission_input = st.text_area("Specific Objective", placeholder="e.g. Launch Q3 Strategy...", height=100)
    uploaded_file = st.file_uploader("Intel Files", type=["pdf", "docx", "txt"])

with tab_vis:
    camera_img = st.camera_input("Scan Target")
    uploaded_img = st.file_uploader("Upload Visual", type=["jpg", "png"])

with tab_voice:
    voice_cmd = st.audio_input("Record Instruction")

st.divider()

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("🎚️ Depth Control")
    depth_setting = st.select_slider("Analysis Depth", options=["Draft", "Standard", "Deep Dive"], value="Standard")

with col2:
    st.subheader("📦 Output Selection")
    selected_outputs = st.multiselect(
        "Select Artifacts:",
        ["Simulation", "PPTX", "Calendar", "Audio", "Art", "CSV"],
        default=["PPTX", "Calendar", "Art"]
    )

if st.button("🚀 IGNITE ENGINE", type="primary", use_container_width=True):
    active_img = camera_img if camera_img else uploaded_img
    file_txt = read_file(uploaded_file)
    voice_txt = ""
    if voice_cmd:
        voice_txt = client.audio.transcriptions.create(model="whisper-1", file=voice_cmd).text
    
    context = f"Brand: {brand_name}. Goal: {north_star}. File Data: {file_txt}"
    
    if mission_input or voice_txt or active_img:
        outputs = run_prime_swarm(mission_input, protocol, context, active_img, voice_txt, selected_outputs, depth_setting)
        st.session_state.current_result = outputs
        st.session_state.history.insert(0, outputs)
        st.rerun()
    else:
        st.warning("⚠️ Input Required")

# --- 6. OUTPUTS & REFINEMENT ---
if st.session_state.current_result:
    st.divider()
    latest = st.session_state.current_result
    
    if 'Concept_Art_URL' in latest:
        st.image(latest['Concept_Art_URL'], caption="Visual Concept", width=400)
        
    st.subheader("🧪 Refinement Lab")
    st.markdown(latest.get('Master_Strategy.md', ''))
    
    refine_q = st.chat_input("Refine this strategy (e.g., 'Make it punchier', 'Add TikTok plan')")
    if refine_q:
        with st.spinner("🔄 Refining..."):
            new_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "assistant", "content": latest['Master_Strategy.md']},
                    {"role": "user", "content": f"Modify the above strategy: {refine_q}"}
                ]
            )
            st.session_state.current_result['Master_Strategy.md'] = new_resp.choices[0].message.content
            st.rerun()

    # DYNAMIC DASHBOARD
    tabs = ["📦 Download"]
    if "Simulation_Log.md" in latest: tabs.append("👥 Sim")
    if "Audio_Brief.mp3" in latest: tabs.append("🎧 Audio")
    
    active_tabs = st.tabs(tabs)
    
    with active_tabs[0]:
        st.success("Assets Ready")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for key, val in latest.items():
                if key.endswith(('.pptx', '.mp3', '.ics')): zip_file.writestr(key, val)
                elif key.endswith('.md') or key.endswith('.csv'): 
                    zip_file.writestr(key, val)
                    if key.endswith('.md'):
                        try: zip_file.writestr(key.replace('.md', '.pdf'), create_pdf(val))
                        except: pass
        
        st.download_button("📦 Download Archive Bundle (.ZIP)", zip_buffer.getvalue(), "Prime_Assets.zip", "application/zip", type="primary", use_container_width=True)

    if "👥 Sim" in tabs:
        with active_tabs[tabs.index("👥 Sim")]: st.info(latest['Simulation_Log.md'])
    if "🎧 Audio" in tabs:
        with active_tabs[tabs.index("🎧 Audio")]: st.audio(latest['Audio_Brief.mp3'])
