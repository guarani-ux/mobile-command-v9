import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
from fpdf import FPDF
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Studio V12: Panopticon", layout="centered", page_icon="👁️")

# CSS: High-Contrast "Nuclear" Aesthetic
st.markdown("""
    <style>
    .stTextArea textarea {font-size: 16px !important;}
    .stSelectbox div[data-baseweb="select"] > div {font-size: 16px !important;}
    .stButton button {height: 3.5em !important; font-weight: 800; border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)

st.title("👁️ Studio V12: Panopticon")

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

# --- 5. THE PANOPTICON INTERFACE ---

st.info("👇 **Phase 1: Sensory Input**")

# TAB SYSTEM for switching between TEXT input and VISION input
tab1, tab2 = st.tabs(["📝 Text/File Intel", "👁️ Visual Intel (The Eye)"])

with tab1:
    uploaded_file = st.file_uploader("Upload Brief/Script", type=["pdf", "docx", "txt", "csv"])
    text_context = st.text_area("Context:", placeholder="e.g. Scouting report for warehouse location...", height=100)

with tab2:
    st.warning("⚠️ **Camera Active.** Analyze physical reality.")
    camera_img = st.camera_input("Scan Target")
    uploaded_img = st.file_uploader("Or Upload Photo", type=["jpg", "png", "jpeg"])
    visual_prompt = st.text_input("Visual Query:", placeholder="e.g. 'Analyze safety risks' or 'Describe lighting conditions'")

st.write("---")
st.info("👇 **Phase 2: Protocol Selection**")

# ADVANCED "SWARM" PROTOCOLS
protocol = st.selectbox("Activate Protocol:", [
    # VISUAL PROTOCOLS (New)
    "👁️ Scout: Location Safety & Logistics Analysis",
    "👁️ Director: Set Vibe & Lighting Critique",
    "👁️ Stylist: Wardrobe & Color Analysis",
    "👁️ OCR: Digitize Paper Contract/Script",
    
    # GENERATIVE PROTOCOLS (Legacy)
    "🎨 CD: DALL-E 3 Concept Art",
    "📄 PA: Daily Call Sheet (PDF)",
    "📋 PA: Load-in Checklist",
    "🚀 Digital: Product Launch Stack",
    "💼 Exec: Strategy Deck"
])

# --- 6. EXECUTION ENGINE ---
if st.button("🚀 EXECUTE", type="primary", use_container_width=True):
    
    # A. VISUAL ANALYSIS PATH (The Nuclear Leap)
    if camera_img or uploaded_img:
        active_img = camera_img if camera_img else uploaded_img
        base64_image = encode_image(active_img)
        
        with st.spinner("👁️ The Eye is Analyzing..."):
            
            # Specialized Visual System Prompts
            v_prompts = {
                "👁️ Scout: Location Safety & Logistics Analysis": "Act as a veteran Location Manager. Analyze this image for: 1. Power access points, 2. Trip/Fall hazards, 3. Lighting conditions, 4. Parking/Load-in feasibility.",
                "👁️ Director: Set Vibe & Lighting Critique": "Act as a Cinematographer. Analyze the lighting in this shot. Describe the current color temperature, practical sources, and suggest 3 ways to enhance the mood.",
                "👁️ Stylist: Wardrobe & Color Analysis": "Act as a Costume Designer. Analyze the clothing/colors in this image. Do they clash? What is the emotional tone? Suggest accessories.",
                "👁️ OCR: Digitize Paper Contract/Script": "Transcribe this document exactly into Markdown. Fix any obvious typos. Summarize the key risks at the bottom."
            }
            
            default_v_prompt = f"Analyze this image. Context: {visual_prompt}"
            system_v_instruction = v_prompts.get(protocol, default_v_prompt)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": system_v_instruction},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        ],
                    }
                ],
                max_tokens=1000,
            )
            result = response.choices[0].message.content
            st.session_state.output_log.append(result)
            
            st.write("---")
            st.image(active_img, caption="Target Acquired", width=300)
            st.markdown(result)
            
            # PDF Export for Visual Reports
            try:
                pdf_bytes = create_pdf(result)
                st.download_button("📄 Download Visual Report", pdf_bytes, "visual_intel.pdf", mime="application/pdf")
            except:
                st.download_button("💾 Download Text", result, "visual_intel.md")

    # B. STANDARD GENERATIVE PATH (Legacy V11)
    else:
        # (This is the text-only logic from V11)
        file_content = read_file(uploaded_file)
        full_context = f"{text_context}\nData: {file_content}"
        
        if protocol == "🎨 CD: DALL-E 3 Concept Art":
            with st.spinner("🎨 Generating Art..."):
                design_prompt = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[{"role": "system", "content": f"Create DALL-E 3 prompt for: {full_context}"}]
                ).choices[0].message.content
                
                img_resp = client.images.generate(model="dall-e-3", prompt=design_prompt, size="1024x1024")
                st.image(img_resp.data[0].url)
        else:
            with st.spinner("🧠 Thinking..."):
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": f"Execute Protocol: {protocol}. Context: {full_context}"}]
                )
                txt = resp.choices[0].message.content
                st.markdown(txt)
                st.download_button("💾 Download", txt, "output.md")
