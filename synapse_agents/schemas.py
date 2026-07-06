"""
schemas.py — Unified Pydantic schemas for all agents.

Day 1 (2-Agent System):
  - ResearchFindingsOutput   ← Research Agent
  - SummarizerOutput         ← Summarizer Agent

Day 2 (4-Agent System):
  - PlannerOutput            ← Planner Agent
  - ResearchOutput           ← Research Agent (richer: evidence + handoff)
  - AnalystOutput            ← Analyst Agent
  - ReportOutput             ← Report Generator Agent

Final Project (6-Agent Company System):
  - CompanyPlannerOutput     ← Planner Agent (adds complexity + assigned_agents)
  - StrategyOutput           ← Strategy Agent
  - ReviewerOutput           ← Reviewer / QA Agent
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Literal

# ---------------------------------------------------------------------------
# Day 1
# ---------------------------------------------------------------------------

class ResearchFindingsOutput(BaseModel):
    """Research Agent output for the 2-agent pipeline."""
    query: str = Field(description="The original user query.")
    key_findings: List[str] = Field(description="Key facts extracted from the knowledge base.")
    sources: List[str] = Field(description="Source titles or document references.")
    notes: str = Field(description="Research context, caveats, or limitations.")


class SummarizerOutput(BaseModel):
    """Summarizer Agent output for the 2-agent pipeline."""
    final_summary: str = Field(description="Concise executive paragraph for the user.")
    bullet_points: List[str] = Field(description="Clean bullet list of core facts.")
    recommended_next_step: str = Field(description="One actionable recommendation.")


# ---------------------------------------------------------------------------
# Day 2
# ---------------------------------------------------------------------------

class PlannerOutput(BaseModel):
    """Planner Agent output — task decomposition (Day 2)."""
    user_query: str = Field(description="Original business query.")
    objective: str = Field(description="Main business analysis objective.")
    subtasks: List[str] = Field(description="Sequential subtasks to solve the objective.")
    required_tools: List[str] = Field(description="Tools needed (e.g. 'search_tool').")
    handoff_to: str = Field(description="Always 'research_agent'.")


class ResearchOutput(BaseModel):
    """Research Agent output — evidence-backed findings."""
    research_topic: str = Field(description="Core topic researched.")
    key_findings: List[str] = Field(description="Facts extracted from retrieved data.")
    evidence: List[str] = Field(description="Source snippets supporting findings.")
    notes: str = Field(description="Research context or limitations.")
    handoff_to: str = Field(description="Always 'analyst_agent'.")


class AnalystOutput(BaseModel):
    """Analyst Agent output — strategic interpretation."""
    insights: List[str] = Field(description="Deep analytical observations.")
    risks: List[str] = Field(description="Business risks or technology limitations.")
    recommendations: List[str] = Field(description="Practical business recommendations.")
    handoff_to: str = Field(description="Always 'report_generator_agent'.")


class ReportOutput(BaseModel):
    """Report Generator Agent output — final user-facing report."""
    executive_summary: str = Field(description="Concise executive summary paragraph.")
    key_points: List[str] = Field(description="High-level bullet points of main findings.")
    next_steps: List[str] = Field(description="Immediate actionable next steps.")


# ---------------------------------------------------------------------------
# Final Project (6-Agent Company System)
# ---------------------------------------------------------------------------

class CompanyPlannerOutput(BaseModel):
    """Planner Agent output for the 6-agent company system."""
    objective: str = Field(description="Main business objective derived from the request.")
    subtasks: List[str] = Field(
        description="3–5 sequential subtasks covering research, analysis, strategy, and reporting."
    )
    assigned_agents: List[str] = Field(
        description="Ordered list of agent names that will execute each subtask."
    )
    estimated_complexity: Literal["low", "medium", "high"] = Field(
        description="Estimated complexity of the business request."
    )


class StrategyOutput(BaseModel):
    """Strategy Agent output — business recommendations."""
    recommendations: List[str] = Field(
        description="Prioritized business recommendations derived from analysis."
    )
    priorities: List[str] = Field(
        description="Top immediate priorities the business should act on."
    )
    target_segment: str = Field(
        description="Primary customer or market segment to target."
    )
    positioning_statement: str = Field(
        description="A one-sentence competitive positioning statement."
    )


class ReviewerOutput(BaseModel):
    """Reviewer / QA Agent output — quality validation."""
    approved: bool = Field(
        description="True if the report meets quality standards, False otherwise."
    )
    issues_found: List[str] = Field(
        description="List of quality issues, gaps, or improvement areas. Empty if approved."
    )
    quality_score: float = Field(
        description="Quality score from 0.0 (poor) to 5.0 (excellent).",
        ge=0.0,
        le=5.0,
    )
    feedback: str = Field(
        description="Brief narrative feedback summarising the review decision."
    )
