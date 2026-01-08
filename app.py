import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document

# --- 1. CONFIGURATION (Mobile Optimized) ---
st.set_page_config(page_title="Studio V10", layout="centered", page_icon="🎬")

# CSS: Better font sizes for mobile tapping
st.markdown("""
    <style>
    .stTextArea textarea {font-size: 16px !important;}
    .stSelectbox div[data-baseweb="select"] > div {font-size: 16px !important;}
    .stButton button {height: 3em !important;}
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Studio V10: Full House")

# --- 2. AUTHENTICATION ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.text_input("🔑 Enter OpenAI API Key:", type="password")
    if not api_key:
        st.warning("Please enter your key to unlock the studio.")
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

# --- 4. MAIN INTERFACE (Vertical Scroll) ---

st.info("👇 **Phase 1: Intel Input**")
uploaded_file = st.file_uploader("Upload Script/Brief/Logistics", type=["pdf", "docx", "txt", "csv"])
text_objective = st.text_area("Context / Notes:", placeholder="e.g. 50 person crew, outdoor shoot, rainy forecast...", height=120)

# EXPANDER: Advanced Constraints
with st.expander("🛠️ Crew & Tech Specs"):
    audience = st.text_input("Audience/Client:", placeholder="e.g. Netflix / Corporate")
    logistics = st.text_input("Logistics/Constraints:", placeholder="e.g. 3 Locations, $10k Budget")
    depth = st.select_slider("Depth:", options=["Quick List", "Standard", "Detailed Protocol"], value="Standard")

st.write("---")
st.info("👇 **Phase 2: Select Role & Output**")

# NEW: CATEGORIZED DROPDOWN
package_type = st.selectbox("Choose Protocol:", [
    # --- PRODUCTION ASSISTANT ---
    "PA: Daily Call Sheet",
    "PA: Gear & Load-in Checklist",
    "PA: Location Scout Report",
    "PA: Crafty & Dietary Log",
    
    # --- CREATIVE DIRECTOR ---
    "CD: Visual Style Guide (Mood Board)",
    "CD: AI Image Prompts (Midjourney/DALL-E)",
    "CD: Script Polish & Tone Check",
    
    # --- DIGITAL LEAD ---
    "Digital: Product Launch (Web/App)",
    "Digital: Jira User Stories",
    "Digital: SEO Strategy",
    
    # --- CONTENT CREATOR ---
    "Social: Multi-Platform Blast",
    "Exec: Strategy Deck Outline"
])

if st.button("🚀 EXECUTE MISSION", type="primary", use_container_width=True):
    
    # B. Combine Inputs
    final_objective = f"{text_objective}\nLogistics: {logistics}"
    file_context = read_file(uploaded_file)
    
    # C. Protocols (Expanded for PA/CD)
    prompts = {
        # PA PROTOCOLS
        "PA: Daily Call Sheet": "Generate a professional Call Sheet Table. Include: Call Times (Crew vs Talent), Location Address, Nearest Hospital, Weather Forecast (Simulated), Parking Instructions, and a detailed schedule grid.",
        "PA: Gear & Load-in Checklist": "Create a categorized checklist for Load-in. Categories: Camera, Lighting, Audio, Grip, Crafty. Include a column for 'Checked Out' and 'Returned'.",
        "PA: Location Scout Report": "Generate a Location Assessment Form. Sections: Lighting Conditions, Power Access (Outlets/Generators), Noise Pollution, Parking Capacity, Permit Requirements, Risk Factors.",
        "PA: Crafty & Dietary Log": "Create a Craft Services plan based on a standard crew. Include a table for Dietary Restrictions (Vegan, GF, Nut Allergy protocols) and a shopping list for Morning, Lunch, and Afternoon slump.",
        
        # CD PROTOCOLS
        "CD: Visual Style Guide (Mood Board)": "Define the Visual Language. Sections: Color Palette (Hex Codes), Lighting References (e.g., 'Rembrandt', 'High Key'), Camera Movement Philosophy, and Set Design Textures.",
        "CD: AI Image Prompts (Midjourney/DALL-E)": "Generate 5 highly detailed AI Image Prompts to visualize the concept. Format: '/imagine prompt: [Subject] + [Art Style] + [Lighting] + [Aspect Ratio]'.",
        "CD: Script Polish & Tone Check": "Act as a Script Doctor. Review the input for tonal consistency. Suggest 3 specific dialogue or scene improvements to elevate the emotional impact.",
        
        # DIGITAL & CONTENT (Legacy)
        "Digital: Product Launch (Web/App)": "Generate FRD Outline, Tech Stack, and Go-Live Runbook.",
        "Digital: Jira User Stories": "Table of User Stories: Summary, Description, Acceptance Criteria, Priority.",
        "Digital: SEO Strategy": "Keyword Cluster, Meta Titles, URL Structure.",
        "Social: Multi-Platform Blast": "3 posts (IG, LinkedIn, X) in code blocks.",
        "Exec: Strategy Deck Outline": "BLUF, SWOT, Roadmap."
    }
    
    # D. The Brain
    system_prompt = f"""
    ROLE: Production Studio AI (PA, CD, & Digital Lead).
    TASK: Generate a {depth} {package_type}.
    
    CONTEXT:
    - Objective: {final_objective}
    - Client/Audience: {audience}
    
    DATA:
    {file_context}
    
    INSTRUCTIONS:
    - Protocol: {prompts[package_type]}
    - Format: Clean Markdown. Use Tables heavily.
    - Tone: Professional, industry-standard terminology.
    """
    
    with st.spinner("🧠 Analyzing Production Data..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}]
            )
            result = response.choices[0].message.content
            
            st.write("---")
            st.success("✅ **Asset Generated**")
            st.markdown(result)
            
            # Download
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
            st.download_button("💾 Save to Files", result, f"StudioV10_Output_{timestamp}.md")
            
        except Exception as e:
            st.error(f"Error: {e}")
