"""
agents.py — All agent functions for the Synapse multi-agent system.

All agents use the shared llm_call() factory from client.py.
No provider-specific logic lives here.

Day 1 agents:
  research_agent_d1(query)           -> ResearchFindingsOutput
  summarizer_agent(findings)         -> SummarizerOutput

Day 2 agents:
  planner_agent(query)               -> PlannerOutput
  research_agent_d2(planner_output)  -> ResearchOutput
  analyst_agent(research, recalled)  -> AnalystOutput
  report_generator_agent(...)        -> ReportOutput

Shared:
  single_agent(query)                -> ReportOutput  (baseline comparison)
"""
from __future__ import annotations

import json

from client import llm_call
from schemas import (
    ResearchFindingsOutput,
    SummarizerOutput,
    PlannerOutput,
    ResearchOutput,
    AnalystOutput,
    ReportOutput,
)
from tools import search_tool
from prompts import (
    RESEARCH_PROMPT,
    SUMMARIZER_PROMPT,
    PLANNER_PROMPT,
    RESEARCH_PROMPT_D2,
    ANALYST_PROMPT,
    REPORT_PROMPT,
    SINGLE_AGENT_PROMPT,
)

# ---------------------------------------------------------------------------
# Day 1 — 2-Agent Pipeline
# ---------------------------------------------------------------------------

def research_agent_d1(user_query: str) -> ResearchFindingsOutput:
    """Research Agent (Day 1): fetches knowledge-base snippets + extracts facts."""
    data = search_tool(user_query)
    results_str = "\n".join(f"- {r}" for r in data["results"])
    sources_str = ", ".join(data["sources"])

    context = (
        f"User Query: {user_query}\n\n"
        f"Retrieved Snippets:\n{results_str}\n\n"
        f"Sources: {sources_str}"
    )
    return llm_call(RESEARCH_PROMPT, context, ResearchFindingsOutput, temperature=0.1)


def summarizer_agent(findings: ResearchFindingsOutput) -> SummarizerOutput:
    """Summarizer Agent (Day 1): synthesizes research findings into a user report."""
    context = f"Research Findings:\n{findings.model_dump_json(indent=2)}"
    return llm_call(SUMMARIZER_PROMPT, context, SummarizerOutput, temperature=0.3)


# ---------------------------------------------------------------------------
# Day 2 — 4-Agent Pipeline
# ---------------------------------------------------------------------------

def planner_agent(user_query: str) -> PlannerOutput:
    """Planner Agent (Day 2): decomposes the business query into subtasks."""
    context = f"Business Query: {user_query}"
    return llm_call(PLANNER_PROMPT, context, PlannerOutput, temperature=0.1)


def research_agent_d2(planner: PlannerOutput) -> ResearchOutput:
    """Research Agent (Day 2): gathers evidence-backed findings per the plan."""
    data = search_tool(planner.objective)
    results_str = "\n".join(f"- {r}" for r in data["results"])

    context = (
        f"Objective: {planner.objective}\n\n"
        f"Subtasks:\n{json.dumps(planner.subtasks, indent=2)}\n\n"
        f"Retrieved Snippets:\n{results_str}"
    )
    return llm_call(RESEARCH_PROMPT_D2, context, ResearchOutput, temperature=0.1)


def analyst_agent(
    research: ResearchOutput,
    recalled_context: str | None = None,
) -> AnalystOutput:
    """Analyst Agent (Day 2): derives insights, risks, and recommendations."""
    context = f"Research Findings:\n{research.model_dump_json(indent=2)}"
    if recalled_context:
        context += f"\n\nHistorical Context (recalled from memory):\n{recalled_context}"
    return llm_call(ANALYST_PROMPT, context, AnalystOutput, temperature=0.3)


def report_generator_agent(
    planner: PlannerOutput,
    research: ResearchOutput,
    analyst: AnalystOutput,
) -> ReportOutput:
    """Report Generator Agent (Day 2): compiles everything into the final report."""
    context = (
        f"Objective: {planner.objective}\n\n"
        f"Key Findings:\n{json.dumps(research.key_findings, indent=2)}\n\n"
        f"Insights:\n{json.dumps(analyst.insights, indent=2)}\n\n"
        f"Risks:\n{json.dumps(analyst.risks, indent=2)}\n\n"
        f"Recommendations:\n{json.dumps(analyst.recommendations, indent=2)}"
    )
    return llm_call(REPORT_PROMPT, context, ReportOutput, temperature=0.3)


# ---------------------------------------------------------------------------
# Shared — Single-Agent Baseline
# ---------------------------------------------------------------------------

def single_agent(user_query: str) -> ReportOutput:
    """Single-agent baseline: one prompt, same ReportOutput schema."""
    data = search_tool(user_query)
    results_str = "\n".join(f"- {r}" for r in data["results"])
    context = (
        f"User Query: {user_query}\n\n"
        f"Retrieved Search Results:\n{results_str}"
    )
    return llm_call(SINGLE_AGENT_PROMPT, context, ReportOutput, temperature=0.3)
