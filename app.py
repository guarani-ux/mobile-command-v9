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
st.set_page_config(page_title="Studio V29: Production Ready", layout="wide", page_icon="🎬")

st.markdown("""
    <style>
    .stButton button {height: 3.5em; font-weight: 800; border-radius: 8px; background-color: #2b2d42; color: white; border: 1px solid #4a4e69;}
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

# --- 4. PRODUCTION DOCS ENGINE (New Feature) ---
def create_production_docs(mission, strategy_text):
    """Generates a .docx Production Pack."""
    doc = Document()
    doc.add_heading(f'PRODUCTION PACK: {mission}', 0)
    
    # 1. Talent Release
    doc.add_heading('1. Talent Appearance Release', level=1)
    doc.add_paragraph(f"PROJECT: {mission}")
    doc.add_paragraph("I hereby grant the Producer the right to use my name, likeness, and voice in the project named above...")
    doc.add_paragraph("_" * 40 + "\nSignature / Date")
    
    # 2. Location Release
    doc.add_page_break()
    doc.add_heading('2. Location Agreement', level=1)
    doc.add_paragraph(f"PROJECT: {mission}")
    doc.add_paragraph("The Property Owner grants permission to the Producer to enter and film on the premises located at: _________________")
    doc.add_paragraph("_" * 40 + "\nOwner Signature / Date")
    
    # 3. Call Sheet Template
    doc.add_page_break()
    doc.add_heading('3. Production Call Sheet', level=1)
    table = doc.add_table(rows=5, cols=2)
    table.style = 'Table Grid'
    table.rows[0].cells[0].text = "PRODUCTION TITLE:"
    table.rows[0].cells[1].text = mission
    table.rows[1].cells[0].text = "CALL TIME:"
    table.rows[1].cells[1].text = "07:00 AM"
    table.rows[2].cells[0].text = "LOCATION:"
    table.rows[2].cells[1].text = "TBD"
    table.rows[3].cells[0].text = "HOSPITAL:"
    table.rows[3].cells[1].text = "Nearest Emergency Room"
    
    # 4. Shot List Extracted from Strategy
    doc.add_page_break()
    doc.add_heading('4. Preliminary Shot List', level=1)
    doc.add_paragraph(strategy_text[:1000]) # Quick context
    
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()

# --- 5. THE GRANDMASTER LOGIC ---

def optimize_prompt(raw_mission):
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": f"ACT AS: Prompt Engineer. REWRITE to be actionable. Input: {raw_mission}"}]
    )
    return resp.choices[0].message.content

def run_grandmaster_swarm(mission, protocol, context, image_data, voice_transcript, req_outputs, depth):
    results = {}
    
    with st.status(f"♟️ Grandmaster Engine ({depth})...", expanded=True) as status:
        
        status.write("🧠 Phase 0: Optimizing Objective...")
        optimized_mission = optimize_prompt(mission) if depth != "Draft" else mission

        status.write("👁️ Phase 1: Sensory Uplink...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_web = executor.submit(web_search, f"{optimized_mission} {protocol} trends")
            future_vis = executor.submit(analyze_vision, image_data, f"Analyze for {protocol} context.")
            intel = future_web.result()
            visual_analysis = future_vis.result()
            
        status.write(f"🧠 Phase 2: Strategic Synthesis...")
        
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
        full_context = f"PROTOCOL: {protocol}\nMISSION: {optimized_mission}\nVOICE: {voice_transcript}\nINTEL: {intel}\n{visual_analysis}\nCONTEXT: {context}\nINSTRUCTION: {base_instr}"
        
        final_strategy = ""

        if depth == "Deep Dive":
            status.write("🌳 Phase 2b: Tree of Thoughts...")
            angles = ["Conservative", "Aggressive", "Data-Driven"]
            drafts = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(client.chat.completions.create, model="gpt-4o", messages=[{"role": "system", "content": f"Generate Strategy. ANGLE: {angle}. Context: {full_context}"}]): angle for angle in angles}
                for future in concurrent.futures.as_completed(futures):
                    drafts.append(future.result().choices[0].message.content)
            
            status.write("⚖️ Phase 2c: The Arbiter...")
            arbiter_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": f"Synthesize these 3 drafts into one Master Strategy.\n\nDRAFTS: {drafts}"}]
            )
            final_strategy = arbiter_resp.choices[0].message.content

        else:
            draft_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "Output Markdown."}, {"role": "user", "content": full_context}]
            )
            current_draft = draft_resp.choices[0].message.content
            
            if depth == "Standard":
                score_resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": f"Rate 0-100 on impact. Output ONLY number. Text: {current_draft[:1000]}"}]
                )
                try: 
                    if int(score_resp.choices[0].message.content.strip()) < 90:
                        status.write("🔄 Refining Strategy...")
                        refine_resp = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "system", "content": "Refine and improve."}, {"role": "user", "content": current_draft}]
                        )
                        current_draft = refine_resp.choices[0].message.content
                except: pass
            
            final_strategy = current_draft

        results['Master_Strategy.md'] = final_strategy
        
        # --- PHASE 3: ARTIFACTS ---
        if req_outputs:
            status.write("📦 Phase 3: Manufacturing Assets...")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {}
                
                if "Simulation" in req_outputs:
                    futures['sim'] = executor.submit(client.chat.completions.create, model="gpt-4o", messages=[{"role": "system", "content": f"Simulate focus group: {final_strategy[:1000]}"}])
                
                if "PPTX" in req_outputs:
                    futures['pptx'] = executor.submit(client.chat.completions.create, model="gpt-4o", response_format={ "type": "json_object" }, messages=[{"role": "system", "content": f"Convert to 5 slides JSON: {final_strategy[:2000]}"}])
                
                if "Calendar" in req_outputs:
                    futures['ics'] = executor.submit(client.chat.completions.create, model="gpt-4o", response_format={ "type": "json_object" }, messages=[{"role": "system", "content": f"Extract dates to JSON: {final_strategy[:2000]}"}])
                
                if "Audio" in req_outputs:
                    futures['mp3'] = executor.submit(create_audio, f"Briefing. {final_strategy[:500]}")
                
                if "Art" in req_outputs:
                    futures['art'] = executor.submit(generate_art, f"{protocol} {mission}")

                if "CSV" in req_outputs:
                    futures['csv'] = executor.submit(client.chat.completions.create, model="gpt-4o", messages=[{"role": "system", "content": f"Extract CSV data table: {final_strategy[:2000]}"}])

                # NEW: PRODUCTION DOCS
                if "Prod Docs (.docx)" in req_outputs:
                    futures['docx'] = executor.submit(create_production_docs, mission, final_strategy)

                for key, future in futures.items():
                    try:
                        res = future.result()
                        if key == 'sim': results['Simulation_Log.md'] = res.choices[0].message.content
                        elif key == 'pptx': results['Presentation.pptx'] = create_pptx(json.loads(res.choices[0].message.content).get('slides', []))
                        elif key == 'ics': results['Schedule.ics'] = create_ics(json.loads(res.choices[0].message.content).get('events', []))
                        elif key == 'mp3': results['Audio_Brief.mp3'] = res
                        elif key == 'art': results['Concept_Art_URL'] = res
                        elif key == 'csv': results['Project_Data.csv'] = res.choices[0].message.content
                        elif key == 'docx': results['Production_Pack.docx'] = res
                    except: pass

        status.update(label="✅ Grandmaster Cycle Complete", state="complete")
        
    return results

# --- 6. INTERFACE ---
with st.sidebar:
    st.title("🧬 Brand DNA")
    brand_name = st.text_input("Org Name", placeholder="Apex Media")
    north_star = st.text_area("North Star Goal", placeholder="Growth...")

st.title("🎬 Studio V29: Production Ready")

tab_text, tab_vis, tab_voice = st.tabs(["📝 Mission Control", "👁️ Vision Uplink", "🎙️ Voice Command"])
with tab_text:
    protocol = st.selectbox("Select Protocol:", [
        "Custom Mission", "🚀 Campaign Launch", "📢 Crisis Response", 
        "🎥 Video Production", "👁️ Scout: Safety", "👁️ Director: Vibe", "💻 Digital Stack"
    ])
    mission_input = st.text_area("Objective", placeholder="e.g. Launch Q3 Strategy...", height=100)
    uploaded_file = st.file_uploader("Intel Files", type=["pdf", "docx", "txt"])

with tab_vis:
    camera_img = st.camera_input("Scan Target")
    uploaded_img = st.file_uploader("Upload Visual", type=["jpg", "png"])

with tab_voice:
    voice_cmd = st.audio_input("Record Instruction")

st.divider()

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("🎚️ Intelligence Level")
    depth_setting = st.select_slider("Reasoning Depth", options=["Draft", "Standard", "Deep Dive"], value="Standard")

with col2:
    st.subheader("📦 Output Selection")
    selected_outputs = st.multiselect(
        "Select Artifacts:",
        ["Simulation", "PPTX", "Calendar", "Audio", "Art", "CSV", "Prod Docs (.docx)"],
        default=["PPTX", "Calendar", "Prod Docs (.docx)"]
    )

if st.button("🚀 IGNITE ENGINE", type="primary", use_container_width=True):
    active_img = camera_img if camera_img else uploaded_img
    file_txt = read_file(uploaded_file)
    voice_txt = ""
    if voice_cmd:
        voice_txt = client.audio.transcriptions.create(model="whisper-1", file=voice_cmd).text
    
    context = f"Brand: {brand_name}. Goal: {north_star}. File Data: {file_txt}"
    
    if mission_input or voice_txt or active_img:
        outputs = run_grandmaster_swarm(mission_input, protocol, context, active_img, voice_txt, selected_outputs, depth_setting)
        st.session_state.current_result = outputs
        st.session_state.history.insert(0, outputs)
        st.rerun()
    else:
        st.warning("⚠️ Input Required")

if st.session_state.current_result:
    st.divider()
    latest = st.session_state.current_result
    
    if 'Concept_Art_URL' in latest:
        st.image(latest['Concept_Art_URL'], caption="Visual Concept", width=400)
        
    st.subheader("🧪 Refinement Lab")
    st.markdown(latest.get('Master_Strategy.md', ''))
    
    refine_q = st.chat_input("Refine this strategy...")
    if refine_q:
        with st.spinner("🔄 Refining..."):
            new_resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "assistant", "content": latest['Master_Strategy.md']}, {"role": "user", "content": f"Modify: {refine_q}"}]
            )
            st.session_state.current_result['Master_Strategy.md'] = new_resp.choices[0].message.content
            st.rerun()

    tabs = ["📦 Download"]
    if "Simulation_Log.md" in latest: tabs.append("👥 Sim")
    if "Audio_Brief.mp3" in latest: tabs.append("🎧 Audio")
    
    active_tabs = st.tabs(tabs)
    
    with active_tabs[0]:
        st.success("Assets Ready")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for key, val in latest.items():
                if key.endswith(('.pptx', '.mp3', '.ics', '.docx')): zip_file.writestr(key, val)
                elif key.endswith('.md') or key.endswith('.csv'): 
                    zip_file.writestr(key, val)
                    if key.endswith('.md'):
                        try: zip_file.writestr(key.replace('.md', '.pdf'), create_pdf(val))
                        except: pass
        
        st.download_button("📦 Download Production Bundle (.ZIP)", zip_buffer.getvalue(), "Production_Assets.zip", "application/zip", type="primary", use_container_width=True)

    if "👥 Sim" in tabs:
        with active_tabs[tabs.index("👥 Sim")]: st.info(latest['Simulation_Log.md'])
    if "🎧 Audio" in tabs:
        with active_tabs[tabs.index("🎧 Audio")]: st.audio(latest['Audio_Brief.mp3'])
