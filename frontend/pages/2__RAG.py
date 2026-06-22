import streamlit as st

from utils.api_client import APIClient, APIError


st.set_page_config(page_title="RAG", page_icon="AI", layout="wide")
st.title("RAG")
st.caption("Upload a file, then ask a question against the indexed content.")

client = APIClient()

if "rag_document_id" not in st.session_state:
    st.session_state.rag_document_id = ""
if "rag_filename" not in st.session_state:
    st.session_state.rag_filename = ""

with st.sidebar:
    st.subheader("Ask settings")
    top_k = st.slider("Top K", min_value=1, max_value=20, value=5)
    final_k = st.slider("Final K", min_value=1, max_value=10, value=3)
    if final_k > top_k:
        st.warning("Final K should not be larger than Top K.")

upload = st.file_uploader("Upload PDF, Markdown, or text", type=["pdf", "md", "txt"])

if st.button("Ingest file", disabled=upload is None):
    try:
        response = client.ingest_file(upload)
        st.session_state.rag_document_id = response["document_id"]
        st.session_state.rag_filename = response["filename"]
        st.success(
            f"Indexed {response['filename']} with {response['chunk_count']} chunks."
        )
    except APIError as exc:
        st.error(f"Ingest failed: {exc}")

if st.session_state.rag_document_id:
    st.info(
        f"Current document: {st.session_state.rag_filename} "
        f"({st.session_state.rag_document_id})"
    )

question = st.text_area("Question", placeholder="What is this file about?")

if st.button(
    "Ask RAG",
    disabled=not question.strip()
    or not st.session_state.rag_document_id
    or final_k > top_k,
):
    try:
        answer = client.ask_rag(
            query=question.strip(),
            top_k=top_k,
            final_k=final_k,
            document_id=st.session_state.rag_document_id,
        )
        st.subheader("Answer")
        st.write(answer["answer"])

        st.subheader("Sources")
        for index, source in enumerate(answer.get("sources", []), start=1):
            with st.expander(
                f"{index}. {source['source_name']} | score={source['score']:.3f}"
            ):
                st.write(source["text"])
                st.caption(
                    f"document_id={source['document_id']} chunk_id={source['chunk_id']}"
                )
    except APIError as exc:
        st.error(f"Ask failed: {exc}")
