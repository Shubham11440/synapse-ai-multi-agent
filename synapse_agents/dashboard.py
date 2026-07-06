"""
dashboard.py — Streamlit monitoring dashboard for the Synapse AI Company System.
Provides a visual interface to launch agent workflows and inspect telemetry logs.
"""
from __future__ import annotations

import sys
import os
import time
from typing import Any

# Ensure the package is importable from any cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

import config
from memory import MemoryStore
from monitoring import get_logs, get_summary, monitor
from schemas import PlannerOutput
from orchestrator import run_2agent, run_4agent, run_company_system
from agents import (
    # Day 1
    research_agent_d1,
    summarizer_agent,
    # Day 2
    planner_agent,
    research_agent_d2,
    analyst_agent,
    report_generator_agent,
    # Final
    company_planner_agent,
    research_agent_company,
    analyst_agent_company,
    strategy_agent,
    reviewer_agent,
)

# ---------------------------------------------------------------------------
# Page configuration & custom CSS
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Synapse AI — Monitoring Dashboard",
    page_icon="🤖",
    layout="wide",
)

# Custom Typography & Spacing CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Outfit', sans-serif;
    }
    .metric-card {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #334155;
    }
    .stProgress > div > div > div > div {
        background-color: #3b82f6;
    }
    </style>
    """,
    unsafe_allow_html=True,
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
    
    # Replace deprecated use_container_width=True with width="stretch"
    run_btn = st.button("🚀 Run Workflow", width="stretch", type="primary")
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
# Interactive Step-by-Step Executions (with live progress tracking)
# ---------------------------------------------------------------------------
if run_btn:
    if not query.strip():
        st.error("Please enter a business query.")
    else:
        # Create execution progress widgets
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner(f"Initiating {mode} workflow..."):
            start_t = time.monotonic()
            results: dict[str, Any] = {}
            try:
                if mode == "company":
                    # Step 0: Memory recall
                    status_text.markdown("🔍 **[Memory]** Recalling past context...")
                    progress_bar.progress(5)
                    memory = MemoryStore()
                    past = memory.recall(query)
                    recalled_ctx = None
                    if past:
                        recalled_ctx = (
                            f"Past Summary: {past.get('executive_summary', '')}\n"
                            f"Past Key Points: {', '.join(past.get('key_points', []))}"
                        )
                    time.sleep(1)

                    # Step 1: Planner
                    status_text.markdown("📋 **[Planner]** Executing Company Planner Agent...")
                    progress_bar.progress(15)
                    with monitor("company_planner_agent", query) as log:
                        plan = company_planner_agent(query)
                        log["output_chars"] = len(plan.model_dump_json())
                    results["planner_output"] = plan
                    time.sleep(1)

                    # Step 2: Research
                    status_text.markdown("🔬 **[Research]** Executing Research Agent...")
                    progress_bar.progress(30)
                    with monitor("research_agent_company", plan.objective) as log:
                        research = research_agent_company(plan)
                        log["output_chars"] = len(research.model_dump_json())
                    results["research_output"] = research
                    time.sleep(1)

                    # Step 3: Analyst
                    status_text.markdown("📊 **[Analyst]** Executing Analyst Agent...")
                    progress_bar.progress(45)
                    with monitor("analyst_agent_company", research.model_dump_json()) as log:
                        analysis = analyst_agent_company(research, recalled_context=recalled_ctx)
                        log["output_chars"] = len(analysis.model_dump_json())
                    results["analysis_output"] = analysis
                    time.sleep(1)

                    # Step 4: Strategy
                    status_text.markdown("💡 **[Strategy]** Executing Strategy Agent...")
                    progress_bar.progress(60)
                    with monitor("strategy_agent", analysis.model_dump_json()) as log:
                        strategy = strategy_agent(analysis)
                        log["output_chars"] = len(strategy.model_dump_json())
                    results["strategy_output"] = strategy
                    time.sleep(1)

                    # Step 5: Report Generator
                    status_text.markdown("📄 **[Report]** Executing Report Generator Agent...")
                    progress_bar.progress(75)
                    synthetic_plan = PlannerOutput(
                        user_query=query,
                        objective=plan.objective,
                        subtasks=plan.subtasks,
                        required_tools=["search_tool", "market_search_tool"],
                        handoff_to="report_generator_agent",
                    )
                    with monitor("report_generator_agent", strategy.model_dump_json()) as log:
                        report = report_generator_agent(synthetic_plan, research, analysis)
                        log["output_chars"] = len(report.model_dump_json())
                    results["final_report"] = report
                    time.sleep(1)

                    # Step 6: Reviewer
                    status_text.markdown("🔍 **[Reviewer]** Executing Reviewer QA Agent...")
                    progress_bar.progress(90)
                    with monitor("reviewer_agent", report.model_dump_json()) as log:
                        review = reviewer_agent(report)
                        log["output_chars"] = len(review.model_dump_json())

                    # Retry flow if rejected
                    if not review.approved:
                        status_text.markdown("⚠ **[Reviewer]** Report rejected. Initiating report revision...")
                        time.sleep(1)
                        with monitor("report_generator_agent_retry", strategy.model_dump_json(), retry_count=1) as log:
                            report = report_generator_agent(synthetic_plan, research, analysis)
                            log["output_chars"] = len(report.model_dump_json())
                        status_text.markdown("🔍 **[Reviewer]** Re-evaluating revised report...")
                        time.sleep(1)
                        with monitor("reviewer_agent_retry", report.model_dump_json(), retry_count=1) as log:
                            review = reviewer_agent(report)
                            log["output_chars"] = len(review.model_dump_json())
                        results["retry_occurred"] = True
                    else:
                        results["retry_occurred"] = False

                    progress_bar.progress(100)
                    status_text.markdown("✅ **[Success]** Workflow completed successfully.")
                    results["final_report"] = report
                    results["review_output"] = review
                    memory.save_session("final_report", report)
                    memory.save_session("review_output", review)
                    memory.save_report(query, report.model_dump())

                elif mode == "4agent":
                    status_text.markdown("📋 **[Planner]** Decomposing subtasks...")
                    progress_bar.progress(25)
                    results = run_4agent(query)
                    progress_bar.progress(100)
                    status_text.markdown("✅ **[Success]** 4-Agent pipeline finished.")

                else:
                    status_text.markdown("🔬 **[Research]** Scanning databases...")
                    progress_bar.progress(50)
                    results = run_2agent(query)
                    progress_bar.progress(100)
                    status_text.markdown("✅ **[Success]** 2-Agent pipeline finished.")

                elapsed_ms = round((time.monotonic() - start_t) * 1000)
                st.success(f"✅ Workflow completed in **{elapsed_ms} ms**")
                
                # Store telemetry
                results["elapsed_ms"] = elapsed_ms
                results["provider"] = config.DEFAULT_PROVIDER
                results["model"] = config.DEFAULT_MODEL
                
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
    
    # Telemetry metadata row
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    col_t1.metric("Provider", results.get("provider", config.DEFAULT_PROVIDER))
    col_t2.metric("Model", results.get("model", config.DEFAULT_MODEL))
    col_t3.metric("Execution Time", f"{results.get('elapsed_ms', 0) / 1000:.2f} s")
    col_t4.metric("Review Retries", "1" if results.get("retry_occurred") else "0")

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
                st.markdown(f"-> {ns}")

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
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Agent Calls", stats["total_runs"])
    m2.metric("Successful", stats["successful"])
    m3.metric("Failed", stats["failed"])
    m4.metric("Avg Latency", f"{stats['avg_duration_ms']} ms")
    m5.metric("Max Latency", f"{stats['max_duration_ms']} ms")
    m6.metric("Total Retries", stats["retry_count"])
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
                "Provider": log.get("provider", "—"),
                "Model": log.get("model", "—"),
                "Retry Count": log.get("retry_count", 0),
                "Time": log.get("start_time", "")[:19].replace("T", " "),
                "Error": log.get("error") or "",
            })
            
        # Replace deprecated use_container_width=True with width="stretch"
        st.dataframe(display_logs, width="stretch")

    with st.expander("🗄 Raw Logs (JSON)", expanded=False):
        st.json(logs[-10:])

st.divider()
st.caption("Synapse AI Multi-Agent System | Built with Streamlit + FastAPI + Gemini/OpenAI")
