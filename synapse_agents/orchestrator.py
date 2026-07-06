"""
orchestrator.py — Unified orchestrator for all three pipelines.

run_2agent(query)          → Day 1 (Research → Summarizer)
run_4agent(query)          → Day 2 (Planner → Research → Analyst → Report)
run_company_system(query)  → Final (6 agents + monitoring + memory + retry)
"""
from __future__ import annotations

import time

from memory import MemoryStore
from monitoring import monitor
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

# ANSI colours
_G = "\033[92m"
_B = "\033[94m"
_Y = "\033[93m"
_C = "\033[96m"
_R = "\033[91m"
_X = "\033[0m"
_W = "\033[1m"

memory = MemoryStore()
_RATE_SLEEP = 5


def _banner(text: str) -> None:
    print(f"\n{_W}{_C}{'='*65}\n {text}\n{'='*65}{_X}")

def _handoff(src: str, dst: str) -> None:
    print(f"{_W}{_C}[Handoff] {src} -> {dst}{_X}")

def _ok(msg: str) -> None:
    print(f"{_G}[OK] {msg}{_X}")

def _info(msg: str) -> None:
    print(f"{_B}[INFO] {msg}{_X}")

def _warn(msg: str) -> None:
    print(f"{_Y}[WARNING] {msg}{_X}")


# ---------------------------------------------------------------------------
# Day 1 — 2-Agent Pipeline
# ---------------------------------------------------------------------------

def run_2agent(query: str) -> dict:
    """2-Agent: User → Research Agent → Summarizer Agent"""
    _banner(f"2-Agent System | {query}")
    memory.save_session("user_query", query)

    _handoff("User", "Research Agent")
    findings = research_agent_d1(query)
    if not findings.key_findings:
        raise ValueError("[Guardrail] Research Agent: 'key_findings' is empty.")
    _ok(f"Research Agent: {len(findings.key_findings)} findings.")
    memory.save_session("research_findings", findings)
    time.sleep(_RATE_SLEEP)

    _handoff("Research Agent", "Summarizer Agent")
    summary = summarizer_agent(findings)
    if not summary.final_summary:
        raise ValueError("[Guardrail] Summarizer Agent: 'final_summary' is empty.")
    _ok("Summarizer Agent: report compiled.")
    memory.save_session("summary", summary)

    return {"research": findings, "summary": summary}


# ---------------------------------------------------------------------------
# Day 2 — 4-Agent Pipeline
# ---------------------------------------------------------------------------

def run_4agent(query: str) -> dict:
    """4-Agent: Planner → Research → Analyst (+ recall) → Report Generator"""
    _banner(f"4-Agent System | {query}")
    memory.save_session("user_query", query)

    past = memory.recall(query)
    recalled_ctx = None
    if past:
        _ok("Memory recall: injecting past context into Analyst.")
        recalled_ctx = (
            f"Past Summary: {past.get('executive_summary', '')}\n"
            f"Past Key Points: {', '.join(past.get('key_points', []))}"
        )
    else:
        _info("No recalled context found.")
    time.sleep(2)

    _handoff("User", "Planner Agent")
    plan = planner_agent(query)
    if not plan.objective or not plan.subtasks:
        raise ValueError("[Guardrail] Planner: 'objective' or 'subtasks' missing.")
    _ok(f"Planner: {len(plan.subtasks)} subtasks.")
    memory.save_session("planner_output", plan)
    time.sleep(_RATE_SLEEP)

    _handoff("Planner", "Research Agent")
    research = research_agent_d2(plan)
    if not research.key_findings:
        raise ValueError("[Guardrail] Research Agent: 'key_findings' empty.")
    _ok(f"Research Agent: {len(research.key_findings)} findings.")
    memory.save_session("research_output", research)
    time.sleep(_RATE_SLEEP)

    _handoff("Research Agent", "Analyst Agent")
    analysis = analyst_agent(research, recalled_context=recalled_ctx)
    if not analysis.insights or not analysis.risks:
        raise ValueError("[Guardrail] Analyst: 'insights' or 'risks' missing.")
    _ok(f"Analyst: {len(analysis.insights)} insights, {len(analysis.risks)} risks.")
    memory.save_session("analysis_output", analysis)
    time.sleep(_RATE_SLEEP)

    _handoff("Analyst", "Report Generator")
    report = report_generator_agent(plan, research, analysis)
    if not report.executive_summary:
        raise ValueError("[Guardrail] Report Generator: 'executive_summary' missing.")
    _ok("Report Generator: report compiled.")
    memory.save_session("final_report", report)
    memory.save_report(query, report.model_dump())
    _info("Saved to long-term memory.")

    return {
        "planner_output": plan,
        "research_output": research,
        "analysis_output": analysis,
        "final_report": report,
    }


# ---------------------------------------------------------------------------
# Final Project — 6-Agent Company System (with monitoring + retry)
# ---------------------------------------------------------------------------

def run_company_system(query: str) -> dict:
    """
    6-Agent company orchestration with per-agent monitoring and reviewer retry.

    Flow:
      User → Company Planner → Research → Analyst → Strategy
           → Report Generator → Reviewer (→ regenerate once if rejected)
    """
    _banner(f"6-Agent Company System | {query}")
    memory.save_session("user_query", query)

    # Memory recall
    past = memory.recall(query)
    recalled_ctx = None
    if past:
        _ok("Memory recall: injecting historical context into Analyst.")
        recalled_ctx = (
            f"Past Summary: {past.get('executive_summary', '')}\n"
            f"Past Key Points: {', '.join(past.get('key_points', []))}"
        )
    else:
        _info("No recalled context found.")

    results: dict = {}

    # Step 1: Company Planner
    _handoff("User", "Company Planner Agent")
    with monitor("company_planner_agent", query) as log:
        plan = company_planner_agent(query)
        log["output_chars"] = len(plan.model_dump_json())
    if not plan.objective or not plan.subtasks:
        raise ValueError("[Guardrail] Company Planner: 'objective' or 'subtasks' missing.")
    _ok(f"Planner: complexity={plan.estimated_complexity}, {len(plan.subtasks)} subtasks.")
    memory.save_session("company_planner_output", plan)
    results["planner_output"] = plan
    time.sleep(_RATE_SLEEP)

    # Step 2: Research Agent
    _handoff("Company Planner", "Research Agent")
    with monitor("research_agent_company", plan.objective) as log:
        research = research_agent_company(plan)
        log["output_chars"] = len(research.model_dump_json())
    if not research.key_findings:
        raise ValueError("[Guardrail] Research Agent: 'key_findings' empty.")
    _ok(f"Research Agent: {len(research.key_findings)} findings, {len(research.evidence)} evidence items.")
    memory.save_session("research_output", research)
    results["research_output"] = research
    time.sleep(_RATE_SLEEP)

    # Step 3: Analyst Agent
    _handoff("Research Agent", "Analyst Agent")
    with monitor("analyst_agent_company", research.model_dump_json()) as log:
        analysis = analyst_agent_company(research, recalled_context=recalled_ctx)
        log["output_chars"] = len(analysis.model_dump_json())
    if not analysis.insights or not analysis.risks:
        raise ValueError("[Guardrail] Analyst: 'insights' or 'risks' missing.")
    _ok(f"Analyst: {len(analysis.insights)} insights, {len(analysis.risks)} risks.")
    memory.save_session("analysis_output", analysis)
    results["analysis_output"] = analysis
    time.sleep(_RATE_SLEEP)

    # Step 4: Strategy Agent
    _handoff("Analyst Agent", "Strategy Agent")
    with monitor("strategy_agent", analysis.model_dump_json()) as log:
        strategy = strategy_agent(analysis)
        log["output_chars"] = len(strategy.model_dump_json())
    if not strategy.recommendations:
        raise ValueError("[Guardrail] Strategy Agent: 'recommendations' missing.")
    _ok(f"Strategy Agent: {len(strategy.recommendations)} recommendations.")
    memory.save_session("strategy_output", strategy)
    results["strategy_output"] = strategy
    time.sleep(_RATE_SLEEP)

    # Step 5: Report Generator — build a synthetic PlannerOutput for the shared function
    _handoff("Strategy Agent", "Report Generator Agent")
    from schemas import PlannerOutput
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
    if not report.executive_summary:
        raise ValueError("[Guardrail] Report Generator: 'executive_summary' missing.")
    _ok("Report Generator: executive report compiled.")
    results["final_report"] = report
    time.sleep(_RATE_SLEEP)

    # Step 6: Reviewer Agent (with one retry on rejection)
    _handoff("Report Generator", "Reviewer / QA Agent")
    with monitor("reviewer_agent", report.model_dump_json()) as log:
        review = reviewer_agent(report)
        log["output_chars"] = len(review.model_dump_json())

    if not review.approved:
        _warn(f"Reviewer rejected report (score={review.quality_score}). Issues: {review.issues_found}")
        _warn("Regenerating report once (retry)...")
        time.sleep(_RATE_SLEEP)
        with monitor("report_generator_agent_retry", strategy.model_dump_json()) as log:
            report = report_generator_agent(synthetic_plan, research, analysis)
            log["output_chars"] = len(report.model_dump_json())
        time.sleep(_RATE_SLEEP)
        with monitor("reviewer_agent_retry", report.model_dump_json()) as log:
            review = reviewer_agent(report)
            log["output_chars"] = len(review.model_dump_json())
        if review.approved:
            _ok(f"Report approved after retry (score={review.quality_score}).")
        else:
            _warn(f"Report still not fully approved after retry (score={review.quality_score}). Proceeding.")
    else:
        _ok(f"Reviewer approved report (score={review.quality_score}).")

    memory.save_session("final_report", report)
    memory.save_session("review_output", review)
    results["final_report"] = report
    results["review_output"] = review

    # Persist to long-term memory
    memory.save_report(query, report.model_dump())
    _info("Final report saved to long-term memory.")

    return results
