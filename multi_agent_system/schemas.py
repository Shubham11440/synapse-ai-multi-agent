from pydantic import BaseModel, Field
from typing import List

class PlannerAgentOutput(BaseModel):
    """Output schema for the Planner Agent."""
    user_query: str = Field(
        description="The original business query provided by the user."
    )
    objective: str = Field(
        description="The main business analysis objective derived from the query."
    )
    subtasks: List[str] = Field(
        description="A sequential list of subtasks required to solve the objective."
    )
    required_tools: List[str] = Field(
        description="List of tools needed to perform the subtasks (e.g. search_tool)."
    )
    handoff_to: str = Field(
        description="The next agent to handoff to. Always 'research_agent'."
    )

class ResearchAgentOutput(BaseModel):
    """Output schema for the Research Agent."""
    research_topic: str = Field(
        description="The core topic or query researched."
    )
    key_findings: List[str] = Field(
        description="Facts and insights extracted from research data."
    )
    evidence: List[str] = Field(
        description="Evidence snippets or sources cited to support the findings."
    )
    notes: str = Field(
        description="Additional research context or limitations."
    )
    handoff_to: str = Field(
        description="The next agent to handoff to. Always 'analyst_agent'."
    )

class AnalystAgentOutput(BaseModel):
    """Output schema for the Analyst Agent."""
    insights: List[str] = Field(
        description="In-depth analytical observations derived from research findings."
    )
    risks: List[str] = Field(
        description="Potential business risks, bottlenecks, or limitations of the proposed solution."
    )
    recommendations: List[str] = Field(
        description="Practical business recommendations or actions."
    )
    handoff_to: str = Field(
        description="The next agent to handoff to. Always 'report_generator_agent'."
    )

class ReportGeneratorOutput(BaseModel):
    """Output schema for the Report Generator Agent."""
    executive_summary: str = Field(
        description="A concise executive summary paragraph synthesising the entire analysis."
    )
    key_points: List[str] = Field(
        description="High-level bullet points detailing the main observations and findings."
    )
    next_steps: List[str] = Field(
        description="Actionable immediate next steps for business stakeholders."
    )
