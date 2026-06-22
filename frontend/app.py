import os

import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Phase 8 Frontend Demo",
    page_icon="AI",
    layout="wide",
)

st.title("Phase 8 Frontend Demo")
st.caption("Simple Streamlit demo for chat, RAG, research, and observability.")

with st.sidebar:
    st.header("Settings")
    st.write(f"Backend: `{BACKEND_URL}`")
    st.info("Use the pages in the sidebar to try each flow.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Included pages")
    st.markdown(
        """
        - Chat: streaming reply from `/api/v1/chat/stream`
        - RAG: upload a file, then ask a question
        - Research: choose a mode and inspect report steps
        - Observability: recent traces, agent runs, and cost summary
        """
    )

with col2:
    st.subheader("How to run")
    st.code("streamlit run frontend/app.py", language="bash")
    st.markdown(
        """
        Set `BACKEND_URL` if your API is not on `http://localhost:8000`.
        """
    )
