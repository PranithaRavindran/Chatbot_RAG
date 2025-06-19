import streamlit as st
from pdf_utils import extract_text
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime
import filetype

# ======================
# HIDE ALL SPINNERS GLOBALLY
# ======================
st.markdown("""
<style>
    /* Hide all spinners */
    .stSpinner > div,
    .stSpinner > div > div,
    [data-testid="stSpinner"] {
        display: none !important;
    }
    
    /* Optional: Custom loading message style */
    .custom-loading {
        font-size: 16px;
        color: #1e88e5;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ======================
# CONSTANTS & SETUP
# ======================
MAX_FILE_SIZE_MB = 200
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = ['pdf']

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ======================
# SESSION STATE
# ======================
if "app_state" not in st.session_state:
    st.session_state.app_state = {
        "messages": [],
        "pdf_text": "",
        "user_name": "",
        "current_pdf": None,
        "all_chats": {},
        "upload_warning": None,
        "last_valid_file": None
    }

def reset_chat():
    if st.session_state.app_state["current_pdf"] and st.session_state.app_state["messages"]:
        st.session_state.app_state["all_chats"][st.session_state.app_state["current_pdf"]] = st.session_state.app_state["messages"].copy()
    st.session_state.app_state["messages"] = []
    st.session_state.app_state["pdf_text"] = ""

# ======================
# HELPER FUNCTIONS
# ======================
def validate_file(file):
    try:
        if file.size == 0:
            return False, "📛 Empty file (0 bytes). Please upload a valid PDF."
        if file.size > MAX_FILE_SIZE_BYTES:
            return False, f"📛 File too large (>{MAX_FILE_SIZE_MB}MB). Max size: {MAX_FILE_SIZE_MB}MB."
        
        ext = file.name.split('.')[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"📛 Unsupported file type (.{ext}). Only PDFs allowed."
        
        file.seek(0)
        file_type = filetype.guess(file.read(2048))
        file.seek(0)
        
        if not file_type or file_type.extension not in ALLOWED_EXTENSIONS:
            return False, "📛 Invalid PDF content. Please upload a real PDF."
        
        return True, ""
    except Exception as e:
        return False, f"📛 Validation error: {str(e)}"

def display_message(role, content):
    with st.chat_message(role):
        st.markdown(content)

# ======================
# SIDEBAR INTERFACE
# ======================
with st.sidebar:
    st.title("💬 Chat History")
    
    if not st.session_state.app_state["user_name"]:
        with st.form("user_profile"):
            name = st.text_input("Your name?", key="name_input")
            if st.form_submit_button("Save"):
                if name.strip():
                    st.session_state.app_state["user_name"] = name.strip()
                    st.rerun()
    else:
        st.success(f"👋 Welcome, {st.session_state.app_state['user_name']}!")
        if st.button("Change Name"):
            st.session_state.app_state["user_name"] = ""
            st.rerun()
    
    st.divider()
    st.subheader("📚 Your Documents")
    
    if not st.session_state.app_state["all_chats"]:
        st.caption("No history yet")
    else:
        for pdf_name, chat_history in st.session_state.app_state["all_chats"].items():
            with st.expander(f"📄 {pdf_name}"):
                if not chat_history:
                    st.caption("No conversations")
                else:
                    for msg in chat_history:
                        if msg["role"] == "user":
                            st.write(f"• {msg['content']} {msg.get('timestamp', '')}")
                
                if st.button(f"Clear {pdf_name}", key=f"clear_{pdf_name}"):
                    if st.session_state.app_state["current_pdf"] == pdf_name:
                        reset_chat()
                        st.session_state.app_state["current_pdf"] = None
                    del st.session_state.app_state["all_chats"][pdf_name]
                    st.rerun()
    
    st.divider()
    if st.button("🧹 Clear ALL History", type="primary"):
        st.session_state.app_state["all_chats"] = {}
        reset_chat()
        st.session_state.app_state["current_pdf"] = None
        st.rerun()

# ======================
# MAIN INTERFACE
# ======================
st.title("📄 PDF Chatbot")

# File Upload with Validation
uploaded_file = st.file_uploader(
    "Upload PDF file",
    type=ALLOWED_EXTENSIONS,
    key="file_uploader",
    help=f"Max size: {MAX_FILE_SIZE_MB}MB"
)

# Validate immediately
if uploaded_file and uploaded_file != st.session_state.app_state["last_valid_file"]:
    is_valid, warning = validate_file(uploaded_file)
    if not is_valid:
        st.session_state.app_state["upload_warning"] = warning
        st.session_state.app_state["last_valid_file"] = None
        st.rerun()
    else:
        st.session_state.app_state["last_valid_file"] = uploaded_file
        st.session_state.app_state["upload_warning"] = None

# Display warnings
if st.session_state.app_state["upload_warning"]:
    st.warning(st.session_state.app_state["upload_warning"])
    display_message("assistant", st.session_state.app_state["upload_warning"])
    st.session_state.app_state["messages"].append({
        "role": "assistant",
        "content": st.session_state.app_state["upload_warning"]
    })
    st.session_state.app_state["upload_warning"] = None
    st.stop()

# Process valid PDF (WITHOUT SPINNER)
if uploaded_file and st.session_state.app_state["current_pdf"] != uploaded_file.name:
    reset_chat()
    st.session_state.app_state["current_pdf"] = uploaded_file.name
    
    # Custom loading message (no spinner)
    loading = st.empty()
    loading.markdown("📖 **Processing:** _" + uploaded_file.name + "_", help="Reading PDF content...")
    
    try:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.app_state["pdf_text"] = extract_text("temp.pdf")
        
        loading.empty()  # Clear loading message
        welcome_msg = f"Hello{', ' + st.session_state.app_state['user_name'] if st.session_state.app_state['user_name'] else ''}! Ready to discuss **{uploaded_file.name}**."
        display_message("assistant", welcome_msg)
        st.session_state.app_state["messages"].append({
            "role": "assistant",
            "content": welcome_msg
        })
    except Exception as e:
        loading.empty()
        error_msg = "⚠️ Error processing PDF (may be password protected)"
        display_message("assistant", error_msg)
        st.session_state.app_state["messages"].append({
            "role": "assistant",
            "content": error_msg
        })
        st.session_state.app_state["current_pdf"] = None
    st.rerun()

# Display chat history
for message in st.session_state.app_state["messages"]:
    display_message(message["role"], message["content"])

# Chat interaction
if st.session_state.app_state["pdf_text"] and (prompt := st.chat_input("Ask about the PDF...")):
    timestamp = datetime.now().strftime("%H:%M")
    user_msg = {
        "role": "user",
        "content": prompt,
        "timestamp": f"({timestamp})"
    }
    st.session_state.app_state["messages"].append(user_msg)
    display_message("user", prompt)
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_placeholder.markdown("▌")  # Simple typing indicator
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                f"PDF Content:\n{st.session_state.app_state['pdf_text'][:50000]}\n\n"
                f"User: {st.session_state.app_state['user_name'] or 'Guest'}\n"
                f"Question: {prompt}"
            )
            response_placeholder.markdown(response.text)
            st.session_state.app_state["messages"].append({
                "role": "assistant",
                "content": response.text
            })
        except Exception as e:
            error_msg = f"⚠️ Error generating response. Please try again."
            response_placeholder.markdown(error_msg)
            st.session_state.app_state["messages"].append({
                "role": "assistant", 
                "content": error_msg
            })
