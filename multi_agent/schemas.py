from pydantic import BaseModel, Field
from typing import List

class ResearchAgentOutput(BaseModel):
    """Structured response schema for the Research Agent."""
    query: str = Field(
        description="The original user query."
    )
    key_findings: List[str] = Field(
        description="List of key facts, statistics, or findings extracted from the search results."
    )
    sources: List[str] = Field(
        description="List of mock source titles or document references used in the findings."
    )
    notes: str = Field(
        description="Additional research context, limitations, or meta-commentary on the research."
    )

class SummarizerAgentOutput(BaseModel):
    """Structured response schema for the Summarizer Agent."""
    final_summary: str = Field(
        description="A concise, high-level summary paragraph representing the final answer for the user."
    )
    bullet_points: List[str] = Field(
        description="A clean list of bullet points detailing the key details of the summary."
    )
    recommended_next_step: str = Field(
        description="A practical, actionable recommendation or next step for the user."
    )
