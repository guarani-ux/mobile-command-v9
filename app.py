import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document
from fpdf import FPDF
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Studio V11", layout="centered", page_icon="🎬")

# CSS: Mobile Optimization
st.markdown("""
    <style>
    .stTextArea textarea {font-size: 16px !important;}
    .stSelectbox div[data-baseweb="select"] > div {font-size: 16px !important;}
    .stButton button {height: 3em !important; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Studio V11: God Mode")

# --- 2. AUTHENTICATION ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.text_input("🔑 Enter OpenAI API Key:", type="password")
    if not api_key:
        st.warning("Please enter your key.")
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

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    # Filter out unsupported unicode characters for FPDF (Safe Mode)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, safe_text)
    return pdf.output(dest="S").encode("latin-1")

# --- 4. SESSION STATE (Memory) ---
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "generated_image" not in st.session_state:
    st.session_state.generated_image = None

# --- 5. INTERFACE ---

st.info("👇 **Phase 1: Intel Input**")
uploaded_file = st.file_uploader("Upload Script/Brief", type=["pdf", "docx", "txt", "csv"])
text_objective = st.text_area("Context:", placeholder="e.g. 50 person crew, sci-fi theme...", height=100)

with st.expander("🛠️ Advanced Settings"):
    audience = st.text_input("Client:", placeholder="Netflix / Corporate")
    logistics = st.text_input("Constraints:", placeholder="Budget/Locations")
    depth = st.select_slider("Depth:", options=["Quick List", "Standard", "Detailed Protocol"], value="Standard")

st.write("---")
st.info("👇 **Phase 2: Select Role**")

package_type = st.selectbox("Choose Protocol:", [
    "PA: Daily Call Sheet",
    "PA: Gear & Load-in Checklist",
    "PA: Location Scout Report",
    "CD: Visual Style Guide (Mood Board)",
    "CD: DALL-E 3 Concept Art Generator", # <-- NEW FEATURE
    "Digital: Product Launch (Web/App)",
    "Digital: Jira User Stories",
    "Social: Multi-Platform Blast",
    "Exec: Strategy Deck Outline"
])

# --- 6. EXECUTION ENGINE ---
if st.button("🚀 EXECUTE MISSION", type="primary", use_container_width=True):
    
    final_objective = f"{text_objective}\nLogistics: {logistics}"
    file_context = read_file(uploaded_file)
    
    # A. IMAGE GENERATION BRANCH
    if package_type == "CD: DALL-E 3 Concept Art Generator":
        with st.spinner("🎨 Painting Concept Art..."):
            try:
                # 1. Optimize Prompt first
                design_prompt = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": f"Create a perfect DALL-E 3 prompt for: {final_objective}. Style: Cinematic, Photorealistic."}]
                ).choices[0].message.content
                
                # 2. Generate Image
                image_response = client.images.generate(
                    model="dall-e-3",
                    prompt=design_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                image_url = image_response.data[0].url
                st.session_state.generated_image = image_url
                st.session_state.generated_text = f"**Prompt Used:** {design_prompt}"
            except Exception as e:
                st.error(f"Image Error: {e}")

    # B. TEXT GENERATION BRANCH
    else:
        prompts = {
            "PA: Daily Call Sheet": "Generate a Call Sheet Table (Crew Call, Talent Call, Nearest Hospital, Lunch Time).",
            "PA: Gear & Load-in Checklist": "Checklist for Camera, Audio, G&E, Crafty.",
            "PA: Location Scout Report": "Assessment: Power, Noise, Parking, Risk.",
            "CD: Visual Style Guide (Mood Board)": "Color Palette (Hex), Lighting Style, Set Textures.",
            "Digital: Product Launch (Web/App)": "FRD Outline, Tech Stack, Runbook.",
            "Digital: Jira User Stories": "CSV Table: Summary, Description, Acceptance Criteria.",
            "Social: Multi-Platform Blast": "3 Posts (IG/LinkedIn/X) in code blocks.",
            "Exec: Strategy Deck Outline": "BLUF, SWOT, Roadmap."
        }
        
        system_prompt = f"""
        ROLE: Production Studio AI.
        TASK: Generate a {depth} {package_type}.
        CONTEXT: {final_objective}
        DATA: {file_context}
        INSTRUCTIONS: {prompts.get(package_type, "Standard Gen")}
        """
        
        with st.spinner("🧠 Analyzing..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": system_prompt}]
                )
                st.session_state.generated_text = response.choices[0].message.content
                st.session_state.generated_image = None
            except Exception as e:
                st.error(f"Text Error: {e}")

# --- 7. OUTPUT DISPLAY ---
if st.session_state.generated_image:
    st.write("---")
    st.image(st.session_state.generated_image, caption="Generated Concept Art")
    st.info("Tip: Long-press the image to save it to Photos.")

if st.session_state.generated_text:
    st.write("---")
    st.markdown(st.session_state.generated_text)
    
    # DUAL EXPORT OPTIONS
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("💾 Download .MD", st.session_state.generated_text, "output.md")
    with col2:
        # PDF GENERATION ON THE FLY
        try:
            pdf_bytes = create_pdf(st.session_state.generated_text)
            st.download_button("📄 Download PDF", pdf_bytes, "output.pdf", mime="application/pdf")
        except Exception as e:
            st.warning("PDF unavailable for this text (Special characters). Use MD.")
