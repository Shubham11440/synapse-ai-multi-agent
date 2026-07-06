"""
dashboard.py — Streamlit monitoring dashboard for the Synapse AI Company System.

Run with:
  streamlit run synapse_agents/dashboard.py
"""
from __future__ import annotations

import sys
import os
import json
import time

# Ensure the package is importable from any cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from monitoring import get_logs, get_summary
from orchestrator import run_company_system, run_4agent, run_2agent

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Synapse AI — Monitoring Dashboard",
    page_icon="🤖",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=80)
    st.title("Synapse AI")
    st.caption("Multi-Agent System Dashboard")
    st.divider()

    mode = st.selectbox(
        "Pipeline Mode",
        options=["company", "4agent", "2agent"],
        index=0,
        help="Select which agent pipeline to run.",
    )
    query = st.text_area(
        "Business Query",
        value="Create a go-to-market strategy for an AI customer support product.",
        height=120,
    )
    run_btn = st.button("🚀 Run Workflow", use_container_width=True, type="primary")
    st.divider()
    st.caption("v1.0.0 | Synapse AI Labs")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🤖 Synapse AI — Multi-Agent System")
st.markdown(
    "A production-ready multi-agent AI system with real-time monitoring, "
    "shared memory, and reviewer-validated outputs."
)
st.divider()

# ---------------------------------------------------------------------------
# Workflow Execution
# ---------------------------------------------------------------------------
if run_btn:
    if not query.strip():
        st.error("Please enter a business query.")
    else:
        with st.spinner(f"Running {mode} pipeline..."):
            start_t = time.monotonic()
            try:
                if mode == "company":
                    results = run_company_system(query)
                elif mode == "4agent":
                    results = run_4agent(query)
                else:
                    results = run_2agent(query)
                elapsed_ms = round((time.monotonic() - start_t) * 1000)
                st.success(f"✅ Workflow completed in **{elapsed_ms} ms**")
                st.session_state["last_results"] = results
                st.session_state["last_mode"] = mode
                st.session_state["last_query"] = query
            except Exception as exc:
                st.error(f"❌ Workflow failed: {exc}")

# ---------------------------------------------------------------------------
# Results display
# ---------------------------------------------------------------------------
if "last_results" in st.session_state:
    results = st.session_state["last_results"]
    mode_used = st.session_state.get("last_mode", "")
    last_query = st.session_state.get("last_query", "")

    st.subheader("📋 Workflow Results")
    st.caption(f"Query: *{last_query}* | Mode: **{mode_used}**")

    # Final Report
    if "final_report" in results:
        report = results["final_report"]
        report_dict = report.model_dump() if hasattr(report, "model_dump") else report

        with st.expander("📄 Final Executive Report", expanded=True):
            st.markdown(f"**Executive Summary**\n\n{report_dict.get('executive_summary', '')}")
            st.markdown("**Key Points**")
            for pt in report_dict.get("key_points", []):
                st.markdown(f"- {pt}")
            st.markdown("**Next Steps**")
            for ns in report_dict.get("next_steps", []):
                st.markdown(f"→ {ns}")

    # Reviewer Output (company mode)
    if "review_output" in results:
        review = results["review_output"]
        review_dict = review.model_dump() if hasattr(review, "model_dump") else review
        approved = review_dict.get("approved", False)
        score = review_dict.get("quality_score", 0)

        with st.expander("🔍 Reviewer / QA Agent Output"):
            col1, col2 = st.columns(2)
            col1.metric("Approved", "✅ Yes" if approved else "❌ No")
            col2.metric("Quality Score", f"{score:.1f} / 5.0")
            st.progress(score / 5.0)
            if review_dict.get("issues_found"):
                st.warning("Issues found:\n" + "\n".join(f"- {i}" for i in review_dict["issues_found"]))
            st.caption(f"Feedback: {review_dict.get('feedback', '')}")

    # Intermediate outputs (collapsible)
    col_a, col_b = st.columns(2)

    if "planner_output" in results or "company_planner_output" in results:
        plan_key = "company_planner_output" if "company_planner_output" in results else "planner_output"
        plan = results[plan_key]
        plan_dict = plan.model_dump() if hasattr(plan, "model_dump") else plan
        with col_a.expander("🗂 Planner Output"):
            st.json(plan_dict)

    if "research_output" in results:
        research = results["research_output"]
        research_dict = research.model_dump() if hasattr(research, "model_dump") else research
        with col_b.expander("🔬 Research Agent Output"):
            st.json(research_dict)

    if "analysis_output" in results:
        analysis = results["analysis_output"]
        analysis_dict = analysis.model_dump() if hasattr(analysis, "model_dump") else analysis
        with col_a.expander("📊 Analyst Agent Output"):
            st.json(analysis_dict)

    if "strategy_output" in results:
        strategy = results["strategy_output"]
        strategy_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else strategy
        with col_b.expander("💡 Strategy Agent Output"):
            st.json(strategy_dict)

st.divider()

# ---------------------------------------------------------------------------
# Monitoring Dashboard
# ---------------------------------------------------------------------------
st.subheader("📡 Monitoring & Observability")

logs = get_logs(limit=100)
stats = get_summary()

# Stats row
if stats.get("total_runs", 0) > 0:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Agent Calls", stats["total_runs"])
    m2.metric("Successful", stats["successful"])
    m3.metric("Failed", stats["failed"])
    m4.metric("Avg Latency", f"{stats['avg_duration_ms']} ms")
    m5.metric("Max Latency", f"{stats['max_duration_ms']} ms")
else:
    st.info("No monitoring data yet. Run a workflow to start collecting metrics.")

# Log table
if logs:
    with st.expander("📋 Agent Execution Logs", expanded=False):
        display_logs = []
        for log in reversed(logs[-20:]):
            display_logs.append({
                "Agent": log.get("agent", ""),
                "Status": "✅" if log.get("status") == "success" else "❌",
                "Duration (ms)": log.get("duration_ms", "—"),
                "Input Chars": log.get("input_chars", "—"),
                "Output Chars": log.get("output_chars", "—"),
                "Time": log.get("start_time", "")[:19].replace("T", " "),
                "Error": log.get("error") or "",
            })
        st.dataframe(display_logs, use_container_width=True)

    with st.expander("🗄 Raw Logs (JSON)", expanded=False):
        st.json(logs[-10:])

st.divider()
st.caption("Synapse AI Multi-Agent System | Built with Streamlit + FastAPI + Gemini/OpenAI")
