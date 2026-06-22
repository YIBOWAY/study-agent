import streamlit as st

from utils.api_client import APIClient, APIError


st.set_page_config(page_title="Observability", page_icon="AI", layout="wide")
st.title("Observability")
st.caption("Inspect recent traces, agent runs, and cost summary.")

client = APIClient()

with st.sidebar:
    st.subheader("Filters")
    trace_limit = st.slider("Trace limit", min_value=1, max_value=100, value=20)
    run_limit = st.slider("Agent run limit", min_value=1, max_value=50, value=10)
    trace_name = st.text_input("Trace name", value="")
    since = st.text_input("Cost since (ISO time)", value="")

if st.button("Refresh", use_container_width=True):
    st.rerun()

try:
    cost = client.get_cost(since=since.strip() or None)
    traces = client.get_traces(limit=trace_limit, name=trace_name.strip() or None)
    runs = client.get_agent_runs(limit=run_limit)

    st.subheader("Cost summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total cost (USD)", f"{cost.get('total_cost_usd', 0.0):.6f}")
    col2.metric("Total calls", cost.get("total_calls", 0))
    tokens = cost.get("total_tokens", {})
    col3.metric(
        "Total tokens",
        int(tokens.get("prompt", 0)) + int(tokens.get("completion", 0)),
    )
    st.json(cost)

    st.subheader(f"Recent traces ({traces.get('total', 0)})")
    for trace in traces.get("traces", []):
        title = (
            f"{trace['name']} | {trace['status']} | "
            f"{trace.get('latency_ms') or 0:.1f} ms"
        )
        with st.expander(title):
            st.json(trace)

    st.subheader(f"Agent runs ({runs.get('total', 0)})")
    for run in runs.get("runs", []):
        root = run.get("root", {})
        children = run.get("children", [])
        title = f"{root.get('name', 'agent_run')} | {root.get('status', '')}"
        with st.expander(title):
            st.write("Root")
            st.json(root)
            st.write("Children")
            st.json(children)
except APIError as exc:
    st.error(f"Observability request failed: {exc}")
