import json

import streamlit as st

from utils.api_client import APIClient, APIError


st.set_page_config(page_title="Research", page_icon="AI", layout="wide")
st.title("Research")
st.caption("Run a research mode and inspect the report, plan, and steps.")

client = APIClient()

with st.sidebar:
    st.subheader("Mode")
    mode = st.selectbox(
        "Research mode",
        options=["workflow", "agent", "agent_v2", "multi_agent"],
        index=0,
    )
    max_iterations = st.slider("Max iterations", min_value=1, max_value=10, value=3)
    top_k = st.slider("Top K", min_value=1, max_value=20, value=5)
    session_id = st.text_input("Session ID", value="")

topic = st.text_area("Topic", placeholder="Research the tradeoffs of local tracing.")

if st.button("Run research", disabled=not topic.strip(), use_container_width=True):
    try:
        result = client.run_research(
            topic=topic.strip(),
            mode=mode,
            max_iterations=max_iterations,
            top_k=top_k,
            session_id=session_id.strip(),
        )
        st.subheader("Report")
        st.write(result["report"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Iterations", result.get("iterations_used", 0))
        col2.metric("Search results", result.get("search_result_count", 0))
        col3.metric("Insights used", result.get("insights_used", 0))

        if result.get("plan"):
            st.subheader("Plan")
            for item in result["plan"]:
                st.write(f"- {item}")

        if result.get("queries"):
            st.subheader("Queries")
            st.write(result["queries"])

        if result.get("agents_involved"):
            st.subheader("Agents involved")
            st.write(result["agents_involved"])

        extra_fields = {
            "analysis": result.get("analysis", ""),
            "reflection_history": result.get("reflection_history", ""),
            "review_verdict": result.get("review_verdict", ""),
        }
        if any(extra_fields.values()):
            st.subheader("Extra details")
            st.json(extra_fields)

        st.subheader("Steps")
        for idx, step in enumerate(result.get("steps", []), start=1):
            with st.expander(f"{idx}. {step['node']} -> {step['action']}"):
                st.write(step["output_summary"])
                st.caption(step["timestamp"])

        with st.expander("Raw response"):
            st.code(json.dumps(result, ensure_ascii=False, indent=2), language="json")
    except APIError as exc:
        st.error(f"Research failed: {exc}")
