import streamlit as st
from pdf_utils import extract_text
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Streamlit UI
st.title("📄 PDF Chatbot")
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:
    with st.spinner("Processing PDF..."):
        # Save uploaded file temporarily
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        text = extract_text("temp.pdf", st.sidebar.checkbox("Scanned PDF?"))
    
    if prompt := st.chat_input("Ask about the PDF"):
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"PDF Content:\n{text[:50000]}\n\nQuestion: {prompt}")
        st.write("Answer:", response.text)