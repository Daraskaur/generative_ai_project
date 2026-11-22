"""
Chat page for the Streamlit application.
"""

import streamlit as st
from streamlit_mic_recorder import speech_to_text

from utils.api_client import query_backend_with_suggestions, document_upload_rag

# Configure page settings
st.set_page_config(
    page_title="LangGraph Chat",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a Bug": None,
        "About": None
    }
)

# Initialize logout confirmation state
if "show_logout_confirm" not in st.session_state:
    st.session_state.show_logout_confirm = False

# Header with logout button
col1, col2 = st.columns([10, 2])
with col2:
    st.write("")  # Spacer
    if st.button("🔒 Logout", use_container_width=True):
        st.session_state.show_logout_confirm = True

# Logout confirmation dialog
if st.session_state.show_logout_confirm:
    st.warning("Are you sure you want to logout?")
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("✅ Yes, logout"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Redirect to home page
            st.switch_page("Home.py")
    with col_cancel:
        if st.button("❌ Cancel"):
            st.session_state.show_logout_confirm = False

st.title("💬 LangGraph Chat")

# Document upload section
with st.sidebar:
    st.header("📂 Upload Documents")

    uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])

    file_description = None
    if uploaded_file:
        file_description = st.text_input(
            "📄 Describe your document (required)",
            max_chars=300,
            placeholder="E.g. LangGraph tutorial with workflows and code examples"
        )

        if "uploaded_files" not in st.session_state:
            st.session_state.uploaded_files = {}

        file_key = f"{uploaded_file.name}_{file_description}"

        if file_description:
            if file_key not in st.session_state.uploaded_files:
                # Upload file if not already uploaded
                success = document_upload_rag(uploaded_file, file_description)
                if success:
                    st.success(f"Uploaded: {uploaded_file.name}")
                    st.session_state.uploaded_files[file_key] = True
                else:
                    st.error(f"Document Upload Failed: {uploaded_file.name}")
            else:
                st.info(f"Uploaded: {uploaded_file.name}")
        else:
            st.warning("Please describe your document before uploading.")

# Check authentication
if "session_id" not in st.session_state:
    st.warning("Please login first.")
    st.stop()

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Keep suggestions and clicked-suggestion in session state
if "suggestions" not in st.session_state:
    st.session_state.suggestions = []
if "clicked_suggestion" not in st.session_state:
    st.session_state.clicked_suggestion = None

# Voice input (uses the browser's Web Speech API, works in Chrome and Edge)
with st.sidebar:
    st.divider()
    st.header("🎙️ Voice Input")
    voice_choice = st.radio("Speak in", ["English", "Hinglish"], horizontal=True)
    voice_lang = "en-IN" if voice_choice == "English" else "hi-IN"

    voice_text = speech_to_text(
        language=voice_lang,
        start_prompt="🎤 Start speaking",
        stop_prompt="⏹️ Stop",
        just_once=True,
        use_container_width=True,
        key=f"voice_{voice_lang}",
    )

# User input
typed_input = st.chat_input("Ask a question...")

# A clicked suggestion or spoken text works exactly like a typed question
clicked = st.session_state.clicked_suggestion
st.session_state.clicked_suggestion = None
user_input = typed_input or clicked or voice_text

# Process user input and get response
if user_input:
    st.session_state.chat_history.append(("user", user_input))
    response, suggestions = query_backend_with_suggestions(
        user_input, st.session_state["jwt_token"]
    )
    st.session_state.chat_history.append(("assistant", response))
    st.session_state.suggestions = suggestions
    st.rerun()  # Rerun script to display updated messages

# Display chat history
for role, text in st.session_state.chat_history:
    st.chat_message(role).write(text)

# Show suggested follow-up questions under the latest answer
if st.session_state.suggestions:
    st.caption("💡 You might also ask:")
    for i, suggestion in enumerate(st.session_state.suggestions):
        if st.button(suggestion, key=f"suggestion_{i}_{len(st.session_state.chat_history)}"):
            st.session_state.clicked_suggestion = suggestion
            st.rerun()