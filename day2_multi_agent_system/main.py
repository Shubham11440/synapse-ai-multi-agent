import os
import sys
import time

# Ensure the script directory is in the path for clean imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator import run_workflow, GREEN, BLUE, YELLOW, CYAN, RED, RESET, BOLD
from agents import client, MODEL_NAME, use_openai
from prompts import SINGLE_AGENT_SYSTEM_PROMPT
from tools import search_tool
from schemas import ReportGeneratorOutput

def run_single_agent(user_query: str) -> ReportGeneratorOutput:
    """
    Single-Agent Baseline:
    Retrieves mock search results and passes them directly to the LLM
    requesting the ReportGeneratorOutput schema in a single prompt step.
    """
    search_results = search_tool(user_query)
    results_str = "\n".join([f"- {r}" for r in search_results])
    
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
            response_format=ReportGeneratorOutput,
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
                response_schema=ReportGeneratorOutput,
                temperature=0.3
            )
        )
        return ReportGeneratorOutput.model_validate_json(response.text)

def display_comparison_dashboard():
    print(f"\n{BOLD}{CYAN}=== Architecture & Quality Comparison: 4-Agent vs Single-Agent ==={RESET}")
    print(f"| {'Metric':<28} | {'4-Agent Orchestrator':<38} | {'Single-Agent Baseline':<32} |")
    print(f"|{'-'*30}|{'-'*40}|{'-'*34}|")
    print(f"| {'Task Decomposition':<28} | {'Yes (Planner splits into subtasks)':<38} | {'No (All-in-one generation)':<32} |")
    print(f"| {'Evidence Gathering':<28} | {'Structured (Research Agent findings)':<38} | {'Direct context feeding':<32} |")
    print(f"| {'Context Expansion':<28} | {'Deep (Analyst + Memory Recall)':<38} | {'Superficial summary':<32} |")
    print(f"| {'Shared Memory Layer':<28} | {'Yes (Session & JSON disk recall)':<38} | {'None (No state persistence)':<32} |")
    print(f"| {'Intermediate Guardrails':<28} | {'Active (Step-by-step validations)':<38} | {'None (Final validation only)':<32} |")
    print(f"| {'Visibility & Debuggability':<28} | {'Excellent (Full visibility per stage)':<38} | {'Poor (Black box output)':<32} |")
    print()

def main():
    queries = [
        "Analyze the benefits of AI agents for customer support teams.",
        "Research how AI can improve sales productivity.",
        "Create a business analysis on AI automation in operations.",
        "What is the weather today in San Francisco?", # Expecting validation failure
        "Analyze the benefits of AI agents for customer support teams." # Expecting memory recall
    ]

    for index, query in enumerate(queries):
        print(f"\n{BOLD}{YELLOW}========================================================================")
        print(f" RUNNING SCENARIO {index + 1}: '{query}'")
        print(f"========================================================================{RESET}")
        
        try:
            # 1. Run the Multi-Agent System
            multi_agent_results = run_workflow(query)
            
            # Print Final Report from Multi-Agent system
            report = multi_agent_results["final_report"]
            print(f"\n{BOLD}{GREEN}>>> Final Report (4-Agent System) <<<{RESET}")
            print(f"{BOLD}Executive Summary:{RESET}\n{report.executive_summary}\n")
            print(f"{BOLD}Key Points:{RESET}")
            for p in report.key_points:
                print(f" - {p}")
            print(f"\n{BOLD}Recommended Next Steps:{RESET}")
            for s in report.next_steps:
                print(f" - {s}")
            print()
            
            # Introduce small sleep to prevent API burst limits
            print(f"{YELLOW}[Main] Sleeping 15 seconds to avoid API quota limits...{RESET}")
            time.sleep(15)

            # 2. Run the Single-Agent baseline (only for successful queries)
            print(f"\n{BOLD}{BLUE}>>> Running Single-Agent Baseline for query...<<<{RESET}")
            single_report = run_single_agent(query)
            print(f"{BOLD}Single-Agent Summary:{RESET}\n{single_report.executive_summary}\n")
            print(f"{BOLD}Single-Agent Next Steps:{RESET}")
            for s in single_report.next_steps:
                print(f" - {s}")
            
        except Exception as e:
            print(f"\n{RED}{BOLD}Error processing query '{query}': {e}{RESET}", file=sys.stderr)
            
        # Introduce sleep between scenario blocks to prevent rate limit hits
        print(f"{YELLOW}[Main] Scenario finished. Sleeping 15 seconds before next scenario...{RESET}")
        time.sleep(15)

    # Output Comparative metrics dashboard
    display_comparison_dashboard()

if __name__ == "__main__":
    main()
