import os
import json
from dotenv import load_dotenv

from schemas import PlannerAgentOutput, ResearchAgentOutput, AnalystAgentOutput, ReportGeneratorOutput
from tools import search_tool
from prompts import (
    PLANNER_AGENT_SYSTEM_PROMPT,
    RESEARCH_AGENT_SYSTEM_PROMPT,
    ANALYST_AGENT_SYSTEM_PROMPT,
    REPORT_GENERATOR_SYSTEM_PROMPT
)

# Load environment variables
load_dotenv()
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env')
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

# Check which API key is available
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

use_openai = False
if OPENAI_API_KEY and not GEMINI_API_KEY:
    use_openai = True
elif not GEMINI_API_KEY and not OPENAI_API_KEY:
    raise ValueError(
        "Neither GEMINI_API_KEY nor OPENAI_API_KEY is set. "
        "Please configure at least one API key in a .env file or environment variables."
    )

if use_openai:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    MODEL_NAME = "gpt-4o-mini"
    print(f"[Initialization] Using OpenAI Engine: {MODEL_NAME}")
else:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL_NAME = "gemini-2.5-flash"
    print(f"[Initialization] Using Gemini Engine: {MODEL_NAME}")

def planner_agent(user_query: str) -> PlannerAgentOutput:
    """
    Planner Agent: Analyzes the query and generates a list of subtasks.
    """
    context = f"Business Query: {user_query}"
    
    if use_openai:
        response = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": PLANNER_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            response_format=PlannerAgentOutput,
            temperature=0.1
        )
        return response.choices[0].message.parsed
    else:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=PLANNER_AGENT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=PlannerAgentOutput,
                temperature=0.1,
            )
        )
        return PlannerAgentOutput.model_validate_json(response.text)

def research_agent(planner_output: PlannerAgentOutput) -> ResearchAgentOutput:
    """
    Research Agent: Gathers facts using search_tool based on subtasks.
    """
    search_query = planner_output.objective
    search_results = search_tool(search_query)
    results_str = "\n".join([f"- {r}" for r in search_results])
    
    context = f"""Planner Objective: {planner_output.objective}
Planner Subtasks:
{json.dumps(planner_output.subtasks, indent=2)}

Retrieved Internal Database Snippets:
{results_str}
"""
    if use_openai:
        response = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": RESEARCH_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            response_format=ResearchAgentOutput,
            temperature=0.1
        )
        return response.choices[0].message.parsed
    else:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=RESEARCH_AGENT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ResearchAgentOutput,
                temperature=0.1,
            )
        )
        return ResearchAgentOutput.model_validate_json(response.text)

def analyst_agent(research_output: ResearchAgentOutput, recalled_context: str = None) -> AnalystAgentOutput:
    """
    Analyst Agent: Evaluates research output to generate insights, risks, and recommendations.
    Injects past context if memory recall has matched a historical report.
    """
    context = f"""Research Findings:
{research_output.model_dump_json(indent=2)}
"""
    if recalled_context:
        context += f"\n\nHistorical Memory (Recalled past report context for continuity):\n{recalled_context}\n"

    if use_openai:
        response = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": ANALYST_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            response_format=AnalystAgentOutput,
            temperature=0.3
        )
        return response.choices[0].message.parsed
    else:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=ANALYST_AGENT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=AnalystAgentOutput,
                temperature=0.3,
            )
        )
        return AnalystAgentOutput.model_validate_json(response.text)

def report_generator_agent(
    planner_output: PlannerAgentOutput,
    research_output: ResearchAgentOutput,
    analyst_output: AnalystAgentOutput
) -> ReportGeneratorOutput:
    """
    Report Generator Agent: Compiles intermediate planning, research, and analysis into the final report.
    """
    context = f"""Objective: {planner_output.objective}

Research Key Findings:
{json.dumps(research_output.key_findings, indent=2)}

Analysis Insights:
{json.dumps(analyst_output.insights, indent=2)}

Analysis Risks:
{json.dumps(analyst_output.risks, indent=2)}

Analysis Recommendations:
{json.dumps(analyst_output.recommendations, indent=2)}
"""
    if use_openai:
        response = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": REPORT_GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            response_format=ReportGeneratorOutput,
            temperature=0.3
        )
        return response.choices[0].message.parsed
    else:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=REPORT_GENERATOR_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ReportGeneratorOutput,
                temperature=0.3,
            )
        )
        return ReportGeneratorOutput.model_validate_json(response.text)
