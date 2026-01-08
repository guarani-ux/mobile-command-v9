import streamlit as st
from openai import OpenAI
import pandas as pd
import PyPDF2
from docx import Document

# --- 1. BARE METAL CONFIG (No Audio, No CSS) ---
st.set_page_config(page_title="Studio V9.4", layout="wide")
st.title("✅ Studio V9.4: Connection Test")
st.write("If you can read this, the mobile connection is stable.")

# --- 2. AUTHENTICATION ---
if "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]
else:
    api_key = st.text_input("Enter OpenAI API Key:", type="password")
    if not api_key:
        st.warning("Waiting for Key...")
        st.stop()

client = OpenAI(api_key=api_key)

# --- 3. BASIC FILE READER ---
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

# --- 4. SIMPLE INTERFACE (No Sidebar Complexities) ---
st.header("1. Strategy Inputs")
uploaded_file = st.file_uploader("Upload Brief", type=["pdf", "docx", "txt", "csv"])

text_objective = st.text_area("Objective / Context:", height=150)
package_type = st.selectbox("Select Output:", [
    "Project Brief",
    "Social Media Post",
    "Executive Summary",
    "Digital Product Specs"
])

if st.button("🚀 RUN", type="primary"):
    file_context = read_file(uploaded_file)
    
    system_prompt = f"""
    ROLE: Elite Strategist.
    TASK: Generate a {package_type}.
    CONTEXT: {text_objective}
    DATA: {file_context}
    """
    
    with st.spinner("Generating..."):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}]
            )
            result = response.choices[0].message.content
            st.markdown("### Output:")
            st.markdown(result)
        except Exception as e:
            st.error(f"Generation Error: {e}")
