import streamlit as st

from utils.api_client import APIClient, APIError
from utils.streaming import stream_chat_response


st.set_page_config(page_title="Chat", page_icon="AI", layout="wide")
st.title("Chat")
st.caption("Stream a reply from the backend chat endpoint.")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

client = APIClient()

with st.sidebar:
    st.subheader("Options")
    system_prompt = st.text_area("System prompt", placeholder="Optional")
    if st.button("Clear chat", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask something")

if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        reply = ""
        try:
            for chunk in stream_chat_response(
                client=client,
                message=prompt,
                system_prompt=system_prompt or None,
            ):
                reply += chunk
                placeholder.markdown(reply or "...")
        except APIError as exc:
            reply = f"Request failed: {exc}"
            placeholder.error(reply)

    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
