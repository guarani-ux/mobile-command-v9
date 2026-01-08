import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document

# --- 1. CONFIGURATION (Mobile Optimized) ---
st.set_page_config(page_title="Content Creator", layout="centered", page_icon="📱")

# CSS to make inputs look better on mobile
st.markdown("""
    <style>
    .stTextArea textarea {font-size: 16px !important;}
    .stSelectbox div[data-baseweb="select"] > div {font-size: 16px !important;}
    </style>
    """, unsafe_allow_html=True)

st.title("📱 Content Creator")

# --- 2. AUTHENTICATION ---
# Check for secrets first, then fallback to manual entry
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    # If no secret, ask for key in the main body (not sidebar)
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

# --- 4. MAIN MOBILE INTERFACE (Vertical Scroll) ---

st.info("👇 **Phase 1: Input Data**")
uploaded_file = st.file_uploader("Upload Brief / Context", type=["pdf", "docx", "txt", "csv"])

text_objective = st.text_area("Objective / Context:", placeholder="Describe what you need to build...", height=120)

# DIGITAL LEAD CONTROLS (Hidden in Expander to save space)
with st.expander("🛠️ Advanced Settings (Tech & Budget)"):
    audience = st.text_input("Target Audience:", placeholder="e.g. Stakeholders")
    tech_stack = st.text_input("Tech Stack:", placeholder="e.g. React, WordPress")
    budget = st.text_input("Budget/Resources:", placeholder="e.g. 2 Devs, $50k")
    depth = st.select_slider("Depth:", options=["Draft", "Standard", "Comprehensive"], value="Standard")

st.write("---")
st.info("👇 **Phase 2: Select Output**")

package_type = st.selectbox("Choose Protocol:", [
    "Project Brief / Scope of Work",
    "Digital Product Launch (Web/App)",
    "Jira/Asana Ticket Generator",
    "SEO & Metadata Strategy",
    "Full Video Production Bible",
    "Marketing Campaign Launch",
    "Crisis Communications Suite",
    "Executive Strategy Deck",
    "Social Media Blast (Mobile)"
])

if st.button("🚀 GENERATE ASSETS", type="primary", use_container_width=True):
    
    # B. Combine Inputs
    final_objective = f"{text_objective}"
    file_context = read_file(uploaded_file)
    
    # C. Protocols
    prompts = {
        "Project Brief / Scope of Work": "Generate a Project Brief: 1. Exec Summary, 2. Deliverables, 3. Timeline, 4. Resources, 5. Success Metrics.",
        "Digital Product Launch (Web/App)": "Generate: 1. FRD Outline, 2. Tech Stack Analysis, 3. UAT Checklist, 4. Go-Live Runbook.",
        "Jira/Asana Ticket Generator": "Create a CSV-ready table of User Stories. Columns: Summary, Description (As a user...), Acceptance Criteria, Priority.",
        "SEO & Metadata Strategy": "Generate: 1. Keyword Cluster, 2. Meta Titles/Descriptions, 3. URL Structure, 4. Content Gap Analysis.",
        "Full Video Production Bible": "Generate: 1. Shooting Script, 2. Shot List, 3. Call Sheet, 4. Risk Assessment.",
        "Marketing Campaign Launch": "Generate: 1. Strategy, 2. Content Calendar, 3. Email Sequence, 4. Ad Creative Specs.",
        "Crisis Communications Suite": "Generate: 1. Holding Statement, 2. Internal Memo, 3. Q&A, 4. Press Release.",
        "Executive Strategy Deck": "Generate: 1. BLUF, 2. SWOT, 3. Financials, 4. Roadmap.",
        "Social Media Blast (Mobile)": "Create 3 posts (IG, LinkedIn, X). Put final text in ```code blocks``` for easy copying."
    }
    
    # D. The Brain
    system_prompt = f"""
    ROLE: Elite Digital Project Lead & Content Creator.
    TASK: Generate a {depth} {package_type}.
    
    CONTEXT:
    - Objective: {final_objective}
    - Audience: {audience}
    - Tech Stack: {tech_stack}
    - Budget: {budget}
    
    DATA:
    {file_context}
    
    INSTRUCTIONS:
    - Protocol: {prompts[package_type]}
    - Use Markdown Headers.
    - Use Tables for lists.
    - Prioritize clarity for mobile reading.
    """
    
    with st.spinner("🧠 Processing Strategy..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}]
            )
            result = response.choices[0].message.content
            
            st.write("---")
            st.success("✅ **Generation Complete**")
            st.markdown(result)
            
            # Download Button
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M")
            st.download_button("💾 Save to Files", result, f"Output_{timestamp}.md")
            
        except Exception as e:
            st.error(f"Error: {e}")
