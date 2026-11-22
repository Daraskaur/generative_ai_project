
import streamlit as st
import uuid

st.set_page_config(
    page_title="Adaptive RAG Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Create a local session instead of using the missing Rust authentication server
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# The existing chat page uses jwt_token as its session identifier
if "jwt_token" not in st.session_state:
    st.session_state["jwt_token"] = st.session_state["session_id"]

st.title("🤖 Adaptive RAG Chatbot")

st.write(
    "Welcome! Ask questions, upload documents, "
    "and interact with your AI-powered RAG assistant."
)

st.success("Your local session is ready!")

if st.button("Start Chatting", type="primary"):
    st.switch_page("pages/chat.py")
