import os
import sys
import json
from dotenv import load_dotenv

# Ensure the script directory is in the path for clean imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schemas import ResearchAgentOutput, SummarizerAgentOutput
from agents import research_agent, summarizer_agent, client, MODEL_NAME, use_openai
from tools import mock_search
from prompts import SINGLE_AGENT_SYSTEM_PROMPT

# ANSI terminal colors for formatting
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

import time

def run_system(user_query: str) -> dict:
    """
    Orchestration Loop:
    1. Pass user query to Research Agent.
    2. Validate Research Agent output.
    3. Pass Research Agent output to Summarizer Agent.
    4. Validate Summarizer Agent output.
    """
    print(f"\n{BOLD}{CYAN}>>> Executing Multi-Agent System for query: '{user_query}'{RESET}")
    
    # 1. Run Research Agent
    print(f"{YELLOW}[Orchestrator] Dispatching query to Research Agent...{RESET}")
    research_output = research_agent(user_query)
    
    # Basic Validation: Research Agent Guardrails
    if not research_output.key_findings:
        raise ValueError("[Guardrail Alert] Research Agent output validation failed: 'key_findings' is empty.")
    if not research_output.query:
        raise ValueError("[Guardrail Alert] Research Agent output validation failed: 'query' is missing.")
        
    # Introduce small delay to prevent API request bursts
    time.sleep(5)

    # 2. Run Summarizer Agent
    print(f"{YELLOW}[Orchestrator] Passing findings to Summarizer Agent...{RESET}")
    summary_output = summarizer_agent(research_output)
    
    # Basic Validation: Summarizer Agent Guardrails
    if not summary_output.final_summary:
        raise ValueError("[Guardrail Alert] Summarizer Agent output validation failed: 'final_summary' is empty.")
    if not summary_output.bullet_points:
        raise ValueError("[Guardrail Alert] Summarizer Agent output validation failed: 'bullet_points' is empty.")
        
    return {
        "research": research_output,
        "summary": summary_output
    }

def run_single_agent(user_query: str) -> SummarizerAgentOutput:
    """
    Single-Agent Baseline:
    Retrieves mock search results and passes them directly to the LLM
    requesting the summary schema in a single prompt step.
    """
    search_data = mock_search(user_query)
    results_str = "\n".join([f"- {r}" for r in search_data["results"]])
    
    context = f"""User Query: {user_query}

Retrieved Search Results:
{results_str}
"""
    if use_openai:
        response = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SINGLE_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            response_format=SummarizerAgentOutput,
            temperature=0.3
        )
        return response.choices[0].message.parsed
    else:
        from google.genai import types
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=context,
            config=types.GenerateContentConfig(
                system_instruction=SINGLE_AGENT_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=SummarizerAgentOutput,
                temperature=0.3
            )
        )
        return SummarizerAgentOutput.model_validate_json(response.text)

def display_results(user_query: str, multi_agent_results: dict, single_agent_result: SummarizerAgentOutput):
    """Prints intermediate stages, final results, and baseline comparisons."""
    research = multi_agent_results["research"]
    summary = multi_agent_results["summary"]
    
    print("\n" + "="*60)
    print(f"{BOLD}{BLUE}=== Intermediate Stage: Research Agent Output ==={RESET}")
    print(json.dumps(research.model_dump(), indent=2))
    
    print("\n" + "="*60)
    print(f"{BOLD}{GREEN}=== Final Stage: Summarizer Agent Output ==={RESET}")
    print(json.dumps(summary.model_dump(), indent=2))
    
    print("\n" + "="*60)
    print(f"{BOLD}{YELLOW}=== Single-Agent Baseline Output ==={RESET}")
    print(json.dumps(single_agent_result.model_dump(), indent=2))
    
    print("\n" + "="*60)
    print(f"{BOLD}{CYAN}=== Side-by-Side Comparison & Architecture Metrics ==={RESET}")
    print(f"| Metric                   | 2-Agent System                      | Single-Agent System         |")
    print(f"|--------------------------|-------------------------------------|-----------------------------|")
    print(f"| Separation of Concerns   | HIGH (Specialized Research + Synthesis) | LOW (Done in single step)   |")
    print(f"| Output Validation        | Yes (Validation on research/summary)| Yes (Final summary only)    |")
    print(f"| Findings Extracted Count | {len(research.key_findings):<35} | {len(single_agent_result.bullet_points):<27} |")
    print(f"| Debuggability            | Easy (Inspect intermediate state)   | Hard (Black box generation) |")
    print("="*60 + "\n")

def main():
    # Load environment variables
    load_dotenv()
    
    # 3-5 Representative test queries mapping to Support, Sales, Operations, and Fallback
    test_queries = [
        "How can AI agents improve customer support?",
        "How can AI agents help sales teams?",
        "What are the benefits of AI automation in operations?",
        "What is the weather today in San Francisco?"  # Trigger fallback search results
    ]
    
    for i, query in enumerate(test_queries):
        if i > 0:
            print(f"{YELLOW}[Rate Limiter] Sleeping 15 seconds to avoid API quota limits...{RESET}")
            time.sleep(15)
        try:
            # Run multi-agent orchestrator
            multi_agent_res = run_system(query)
            
            # Delay to avoid rate limiting before the baseline call
            time.sleep(5)
            
            # Run single-agent baseline
            single_agent_res = run_single_agent(query)
            
            # Output and Compare
            display_results(query, multi_agent_res, single_agent_res)
            
        except Exception as e:
            print(f"{RED}{BOLD}Error processing query '{query}': {e}{RESET}", file=sys.stderr)

if __name__ == "__main__":
    main()

