"""
agents.py — All agent functions for the Synapse multi-agent system.

All agents call the shared llm_call() factory from client.py.
No provider-specific logic lives here.

Day 1:  research_agent_d1, summarizer_agent
Day 2:  planner_agent, research_agent_d2, analyst_agent, report_generator_agent
Final:  company_planner_agent, research_agent_company, analyst_agent_company,
        strategy_agent, report_generator_agent (reused), reviewer_agent
Shared: single_agent
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
    CompanyPlannerOutput,
    StrategyOutput,
    ReviewerOutput,
)
from tools import search_tool, go_to_market_tool
from prompts import (
    RESEARCH_PROMPT,
    SUMMARIZER_PROMPT,
    PLANNER_PROMPT,
    RESEARCH_PROMPT_D2,
    ANALYST_PROMPT,
    ANALYST_PROMPT_COMPANY,
    REPORT_PROMPT,
    COMPANY_PLANNER_PROMPT,
    COMPANY_RESEARCH_PROMPT,
    STRATEGY_PROMPT,
    REVIEWER_PROMPT,
    SINGLE_AGENT_PROMPT,
)

# ---------------------------------------------------------------------------
# Day 1 — 2-Agent Pipeline
# ---------------------------------------------------------------------------

def research_agent_d1(user_query: str) -> ResearchFindingsOutput:
    """Research Agent (Day 1): fetches KB snippets and extracts facts."""
    data = search_tool(user_query)
    results_str = "\n".join(f"- {r}" for r in data["results"])
    context = (
        f"User Query: {user_query}\n\n"
        f"Retrieved Snippets:\n{results_str}\n\n"
        f"Sources: {', '.join(data['sources'])}"
    )
    return llm_call(RESEARCH_PROMPT, context, ResearchFindingsOutput, temperature=0.1)


def summarizer_agent(findings: ResearchFindingsOutput) -> SummarizerOutput:
    """Summarizer Agent (Day 1): synthesizes findings into a user report."""
    context = f"Research Findings:\n{findings.model_dump_json(indent=2)}"
    return llm_call(SUMMARIZER_PROMPT, context, SummarizerOutput, temperature=0.3)


# ---------------------------------------------------------------------------
# Day 2 — 4-Agent Pipeline
# ---------------------------------------------------------------------------

def planner_agent(user_query: str) -> PlannerOutput:
    """Planner Agent (Day 2): decomposes the business query into subtasks."""
    return llm_call(PLANNER_PROMPT, f"Business Query: {user_query}", PlannerOutput, temperature=0.1)


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


def analyst_agent(research: ResearchOutput, recalled_context: str | None = None) -> AnalystOutput:
    """Analyst Agent (Day 2): derives insights, risks, and recommendations."""
    context = f"Research Findings:\n{research.model_dump_json(indent=2)}"
    if recalled_context:
        context += f"\n\nHistorical Context (recalled memory):\n{recalled_context}"
    return llm_call(ANALYST_PROMPT, context, AnalystOutput, temperature=0.3)


def report_generator_agent(
    planner: PlannerOutput,
    research: ResearchOutput,
    analyst: AnalystOutput,
) -> ReportOutput:
    """Report Generator (Day 2 & Final): compiles everything into the final report."""
    context = (
        f"Objective: {planner.objective}\n\n"
        f"Key Findings:\n{json.dumps(research.key_findings, indent=2)}\n\n"
        f"Insights:\n{json.dumps(analyst.insights, indent=2)}\n\n"
        f"Risks:\n{json.dumps(analyst.risks, indent=2)}\n\n"
        f"Recommendations:\n{json.dumps(analyst.recommendations, indent=2)}"
    )
    return llm_call(REPORT_PROMPT, context, ReportOutput, temperature=0.3)


# ---------------------------------------------------------------------------
# Final Project — 6-Agent Company System
# ---------------------------------------------------------------------------

def company_planner_agent(user_query: str) -> CompanyPlannerOutput:
    """Planner Agent (Final): estimates complexity and assigns the full agent team."""
    return llm_call(
        COMPANY_PLANNER_PROMPT,
        f"Business Request: {user_query}",
        CompanyPlannerOutput,
        temperature=0.1,
    )


def research_agent_company(plan: CompanyPlannerOutput) -> ResearchOutput:
    """Research Agent (Final): multi-tool evidence gathering for GTM queries."""
    # Use go_to_market_tool for richer combined market + core data
    data = go_to_market_tool(plan.objective)
    results_str = "\n".join(f"- {r}" for r in data["results"])
    context = (
        f"Business Objective: {plan.objective}\n\n"
        f"Subtasks:\n{json.dumps(plan.subtasks, indent=2)}\n\n"
        f"Market Intelligence Snippets:\n{results_str}\n\n"
        f"Sources: {', '.join(data['sources'])}"
    )
    return llm_call(COMPANY_RESEARCH_PROMPT, context, ResearchOutput, temperature=0.1)


def analyst_agent_company(
    research: ResearchOutput,
    recalled_context: str | None = None,
) -> AnalystOutput:
    """Analyst Agent (Final): strategic pattern recognition with memory recall."""
    context = f"Research Findings:\n{research.model_dump_json(indent=2)}"
    if recalled_context:
        context += f"\n\nHistorical Context (recalled memory):\n{recalled_context}"
    return llm_call(ANALYST_PROMPT_COMPANY, context, AnalystOutput, temperature=0.3)


def strategy_agent(analysis: AnalystOutput) -> StrategyOutput:
    """Strategy Agent (Final): converts insights into prioritized business recommendations."""
    context = (
        f"Insights:\n{json.dumps(analysis.insights, indent=2)}\n\n"
        f"Risks:\n{json.dumps(analysis.risks, indent=2)}\n\n"
        f"Analyst Recommendations:\n{json.dumps(analysis.recommendations, indent=2)}"
    )
    return llm_call(STRATEGY_PROMPT, context, StrategyOutput, temperature=0.3)


def reviewer_agent(report: ReportOutput) -> ReviewerOutput:
    """Reviewer / QA Agent (Final): validates report quality; may trigger regeneration."""
    context = f"Report to Review:\n{report.model_dump_json(indent=2)}"
    return llm_call(REVIEWER_PROMPT, context, ReviewerOutput, temperature=0.1)


# ---------------------------------------------------------------------------
# Shared — Single-Agent Baseline
# ---------------------------------------------------------------------------

def single_agent(user_query: str) -> ReportOutput:
    """Single-agent baseline: one-shot prompt returning ReportOutput."""
    data = search_tool(user_query)
    results_str = "\n".join(f"- {r}" for r in data["results"])
    context = f"User Query: {user_query}\n\nSearch Results:\n{results_str}"
    return llm_call(SINGLE_AGENT_PROMPT, context, ReportOutput, temperature=0.3)
