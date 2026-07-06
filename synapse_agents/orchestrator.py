"""
orchestrator.py — Unified orchestrator for both pipelines.

run_2agent(query)   → 2-agent orchestration (Day 1)
run_4agent(query)   → 4-agent orchestration with memory recall (Day 2)

Both functions:
  - save outputs to the shared MemoryStore session
  - validate each agent's output before the next handoff
  - return a structured results dict
"""
from __future__ import annotations

import time

from memory import MemoryStore
from agents import (
    research_agent_d1,
    summarizer_agent,
    planner_agent,
    research_agent_d2,
    analyst_agent,
    report_generator_agent,
)

# ANSI colours
_G = "\033[92m"   # green
_B = "\033[94m"   # blue
_Y = "\033[93m"   # yellow
_C = "\033[96m"   # cyan
_R = "\033[91m"   # red
_X = "\033[0m"    # reset
_W = "\033[1m"    # bold

# Shared memory store (one instance, shared by both pipelines)
memory = MemoryStore()

_RATE_SLEEP = 5   # seconds between agent calls to avoid burst limits


def _banner(text: str) -> None:
    print(f"\n{_W}{_C}{'='*60}\n {text}\n{'='*60}{_X}")


def _handoff(src: str, dst: str) -> None:
    print(f"{_W}{_C}[Handoff] {src} → {dst}{_X}")


def _ok(msg: str) -> None:
    print(f"{_G}✔ {msg}{_X}")


def _info(msg: str) -> None:
    print(f"{_B}ℹ {msg}{_X}")


def _warn(msg: str) -> None:
    print(f"{_Y}⚠ {msg}{_X}")


# ---------------------------------------------------------------------------
# Day 1 — 2-Agent Pipeline
# ---------------------------------------------------------------------------

def run_2agent(query: str) -> dict:
    """
    2-Agent orchestration:
      User → Research Agent → Summarizer Agent
    """
    _banner(f"2-Agent System | Query: {query}")
    memory.save_session("user_query", query)

    # Step 1: Research Agent
    _handoff("User", "Research Agent")
    findings = research_agent_d1(query)

    if not findings.key_findings:
        raise ValueError("[Guardrail] Research Agent: 'key_findings' is empty.")
    _ok(f"Research Agent: {len(findings.key_findings)} findings extracted.")
    memory.save_session("research_findings", findings)
    time.sleep(_RATE_SLEEP)

    # Step 2: Summarizer Agent
    _handoff("Research Agent", "Summarizer Agent")
    summary = summarizer_agent(findings)

    if not summary.final_summary:
        raise ValueError("[Guardrail] Summarizer Agent: 'final_summary' is empty.")
    if not summary.bullet_points:
        raise ValueError("[Guardrail] Summarizer Agent: 'bullet_points' is empty.")
    _ok("Summarizer Agent: report compiled.")
    memory.save_session("summary", summary)

    return {"research": findings, "summary": summary}


# ---------------------------------------------------------------------------
# Day 2 — 4-Agent Pipeline
# ---------------------------------------------------------------------------

def run_4agent(query: str) -> dict:
    """
    4-Agent orchestration with memory recall:
      User → Planner → Research → Analyst (+ recalled context) → Report Generator
    """
    _banner(f"4-Agent System | Query: {query}")
    memory.save_session("user_query", query)

    # Memory recall check
    _info("Checking long-term memory for recalled context...")
    past = memory.recall(query)
    recalled_ctx: str | None = None
    if past:
        _ok("Recalled a past report — injecting context into Analyst.")
        recalled_ctx = (
            f"Past Summary: {past.get('executive_summary', '')}\n"
            f"Past Key Points: {', '.join(past.get('key_points', []))}"
        )
    else:
        _info("No matching past report found.")

    time.sleep(2)

    # Step 1: Planner Agent
    _handoff("User", "Planner Agent")
    plan = planner_agent(query)
    if not plan.objective or not plan.subtasks:
        raise ValueError("[Guardrail] Planner Agent: 'objective' or 'subtasks' is empty.")
    _ok(f"Planner Agent: objective set, {len(plan.subtasks)} subtasks defined.")
    memory.save_session("planner_output", plan)
    time.sleep(_RATE_SLEEP)

    # Step 2: Research Agent
    _handoff("Planner Agent", "Research Agent")
    research = research_agent_d2(plan)
    if not research.key_findings:
        raise ValueError("[Guardrail] Research Agent: 'key_findings' is empty.")
    _ok(f"Research Agent: {len(research.key_findings)} findings collected.")
    memory.save_session("research_output", research)
    time.sleep(_RATE_SLEEP)

    # Step 3: Analyst Agent
    _handoff("Research Agent", "Analyst Agent")
    analysis = analyst_agent(research, recalled_context=recalled_ctx)
    if not analysis.insights or not analysis.risks:
        raise ValueError("[Guardrail] Analyst Agent: 'insights' or 'risks' is empty.")
    _ok(f"Analyst Agent: {len(analysis.insights)} insights, {len(analysis.risks)} risks.")
    memory.save_session("analysis_output", analysis)
    time.sleep(_RATE_SLEEP)

    # Step 4: Report Generator Agent
    _handoff("Analyst Agent", "Report Generator Agent")
    report = report_generator_agent(plan, research, analysis)
    if not report.executive_summary:
        raise ValueError("[Guardrail] Report Generator: 'executive_summary' is empty.")
    _ok("Report Generator Agent: final report compiled.")
    memory.save_session("final_report", report)

    # Persist to long-term memory
    memory.save_report(query, report.model_dump())
    _info("Final report saved to long-term memory store.")

    return {
        "planner_output": plan,
        "research_output": research,
        "analysis_output": analysis,
        "final_report": report,
    }
