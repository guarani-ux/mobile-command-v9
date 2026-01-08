import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
import io

# --- 1. MOBILE CONFIGURATION ---
st.set_page_config(page_title="Studio V9", layout="wide", page_icon="📱")

# CSS Hack to hide the top bar on mobile for cleaner look
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
div.block-container {padding-top: 1rem;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("📱 Studio V9: Mobile Command")

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

# --- 4. INPUT ZONE (Mobile Optimized) ---
with st.sidebar:
    st.header("1. Input Data")
    uploaded_file = st.file_uploader("📂 Upload Brief/CSV", type=["pdf", "docx", "txt", "csv"])
    
    st.header("2. Strategy")
    # NEW: Audio Input for fast mobile briefing
    audio_brief = st.audio_input("🎙️ Record Objective/Context")
    
    # Fallback text input
    with st.expander("📝 Or Type Context (Click to Expand)"):
        text_objective = st.text_area("Objective:", placeholder="e.g. Launch Q3 Campaign")
        audience = st.text_input("Audience:", placeholder="e.g. Gen Z")
        
    package_type = st.selectbox("📦 Select Package:", [
        "Social Media Blast (IG/LinkedIn)",
        "Executive Summary",
        "Video Script (Short Form)",
        "Crisis Response",
        "Email Sequence"
    ])
    
    generate_btn = st.button("🚀 EXECUTE", type="primary", use_container_width=True)

# --- 5. LOGIC ENGINE ---
if generate_btn:
    # A. Transcribe Audio if present
    audio_text = ""
    if audio_brief:
        with st.spinner("🎙️ Transcribing Voice Note..."):
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_brief
            )
            audio_text = transcription.text
            st.success(f"🗣️ Heard: {audio_text[:50]}...")
    
    # B. Combine Inputs
    final_objective = f"{text_objective}\n{audio_text}"
    file_context = read_file(uploaded_file)
    
    # C. Protocols
    prompts = {
        "Social Media Blast (IG/LinkedIn)": "Create 3 variations: 1. LinkedIn Professional, 2. Instagram Casual, 3. Twitter Thread. Format in code blocks for easy copying.",
        "Executive Summary": "Create a BLUF (Bottom Line Up Front) summary, followed by Key Risks and Financial Impact.",
        "Video Script (Short Form)": "Create a 60-second vertical video script. Split into Visual/Audio columns.",
        "Crisis Response": "Draft a Holding Statement (Internal) and a Press Release (External).",
        "Email Sequence": "Draft 3 emails: 1. Value Add, 2. Soft Pitch, 3. Hard Close."
    }
    
    # D. The Brain
    system_prompt = f"""
    ROLE: Elite Mobile Marketing Strategist.
    TASK: Generate {package_type}.
    
    CONTEXT:
    - Objective: {final_objective}
    - Audience: {audience}
    - File Data: {file_context}
    
    INSTRUCTIONS:
    - Use clear headers.
    - {prompts[package_type]}
    - IMPORTANT: If the output is social copy, put the final text in a markdown code block (```) so the user can one-tap copy it.
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
        st.download_button("💾 Save as File", result, "output.md")
