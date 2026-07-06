"""
schemas.py — Unified Pydantic schemas for all agents across Day 1 and Day 2.

Day 1 (2-Agent System):
  - ResearchFindingsOutput   ← Research Agent
  - SummarizerOutput         ← Summarizer Agent

Day 2 (4-Agent System):
  - PlannerOutput            ← Planner Agent
  - ResearchOutput           ← Research Agent (richer, with evidence + handoff)
  - AnalystOutput            ← Analyst Agent
  - ReportOutput             ← Report Generator Agent

The Day 2 ResearchOutput is a superset of Day 1 ResearchFindingsOutput.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List

# ---------------------------------------------------------------------------
# Day 1 Schemas
# ---------------------------------------------------------------------------

class ResearchFindingsOutput(BaseModel):
    """Research Agent output for the 2-agent pipeline."""
    query: str = Field(description="The original user query.")
    key_findings: List[str] = Field(
        description="Key facts extracted from the knowledge base."
    )
    sources: List[str] = Field(
        description="Source titles or document references for the findings."
    )
    notes: str = Field(
        description="Research context, caveats, or limitations."
    )

class SummarizerOutput(BaseModel):
    """Summarizer Agent output for the 2-agent pipeline."""
    final_summary: str = Field(
        description="Concise executive paragraph summarizing findings for the user."
    )
    bullet_points: List[str] = Field(
        description="Clean bullet list of the core facts."
    )
    recommended_next_step: str = Field(
        description="One practical, actionable recommendation for the user."
    )

# ---------------------------------------------------------------------------
# Day 2 Schemas
# ---------------------------------------------------------------------------

class PlannerOutput(BaseModel):
    """Planner Agent output — task decomposition."""
    user_query: str = Field(description="Original business query from the user.")
    objective: str = Field(description="Main business analysis objective.")
    subtasks: List[str] = Field(
        description="Sequential subtasks required to solve the objective."
    )
    required_tools: List[str] = Field(
        description="Tools needed (e.g. 'search_tool')."
    )
    handoff_to: str = Field(description="Always 'research_agent'.")

class ResearchOutput(BaseModel):
    """Research Agent output — evidence-backed findings."""
    research_topic: str = Field(description="Core topic researched.")
    key_findings: List[str] = Field(description="Facts extracted from retrieved data.")
    evidence: List[str] = Field(
        description="Source snippets or references supporting the findings."
    )
    notes: str = Field(description="Research context or limitations.")
    handoff_to: str = Field(description="Always 'analyst_agent'.")

class AnalystOutput(BaseModel):
    """Analyst Agent output — strategic interpretation."""
    insights: List[str] = Field(
        description="Deep analytical observations from the research."
    )
    risks: List[str] = Field(
        description="Business risks or technology limitations identified."
    )
    recommendations: List[str] = Field(
        description="Practical business recommendations."
    )
    handoff_to: str = Field(description="Always 'report_generator_agent'.")

class ReportOutput(BaseModel):
    """Report Generator Agent output — final user-facing report."""
    executive_summary: str = Field(
        description="Concise executive summary synthesising the entire analysis."
    )
    key_points: List[str] = Field(
        description="High-level bullet points of main findings."
    )
    next_steps: List[str] = Field(
        description="Immediate actionable next steps for business stakeholders."
    )
