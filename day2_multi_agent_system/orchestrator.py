import time
from memory import MemoryStore
from schemas import PlannerAgentOutput, ResearchAgentOutput, AnalystAgentOutput, ReportGeneratorOutput
from agents import planner_agent, research_agent, analyst_agent, report_generator_agent

# ANSI terminal colors for formatting
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Initialize shared memory store
memory = MemoryStore()

def run_workflow(user_query: str) -> dict:
    """
    4-Agent Orchestrator Loop:
    1. Loads past reports for continuity recall.
    2. Invokes Planner Agent -> Validates -> Saves.
    3. Invokes Research Agent -> Validates -> Saves.
    4. Invokes Analyst Agent (with recalled context) -> Validates -> Saves.
    5. Invokes Report Generator Agent -> Validates -> Saves & serializes to long-term memory.
    """
    print(f"\n{BOLD}{CYAN}=== Starting 4-Agent Orchestration for query: '{user_query}' ==={RESET}")
    
    # Save original query to session
    memory.save_session("user_query", user_query)
    
    # Step 0: Check memory recall
    print(f"{YELLOW}[Orchestrator] Checking long-term memory for past context...{RESET}")
    recalled_report = memory.recall_memory(user_query)
    recalled_context = None
    if recalled_report:
        print(f"{GREEN}[Memory Recall Alert] Found matching past report in memory! Injecting for continuity.{RESET}")
        recalled_context = (
            f"Past Summary: {recalled_report.get('executive_summary', '')}\n"
            f"Past Key Points: {', '.join(recalled_report.get('key_points', []))}"
        )
    else:
        print(f"{BLUE}[Orchestrator] No matching past report found in long-term memory.{RESET}")
        
    # Rate limit sleep to prevent burst issues
    time.sleep(2)

    # Step 1: Planner Agent
    print(f"\n{BOLD}{CYAN}[Orchestrator Handoff: User Query → Planner Agent]{RESET}")
    planner_output = planner_agent(user_query)
    
    # Validation
    if not planner_output.objective:
        raise ValueError("[Guardrail Alert] Planner output validation failed: 'objective' is empty.")
    if not planner_output.subtasks:
        raise ValueError("[Guardrail Alert] Planner output validation failed: 'subtasks' is empty.")
        
    print(f"{GREEN}[Planner Output] Objective: {planner_output.objective}{RESET}")
    print(f"{GREEN}[Planner Output] Subtasks: {', '.join(planner_output.subtasks)}{RESET}")
    memory.save_session("planner_output", planner_output)
    
    # Rate limit sleep
    time.sleep(5)

    # Step 2: Research Agent
    print(f"\n{BOLD}{CYAN}[Orchestrator Handoff: Planner Agent → Research Agent]{RESET}")
    research_output = research_agent(planner_output)
    
    # Validation
    if not research_output.key_findings:
        raise ValueError("[Guardrail Alert] Research Agent output validation failed: 'key_findings' is empty.")
        
    print(f"{GREEN}[Research Output] Key Findings: {len(research_output.key_findings)} items collected.{RESET}")
    print(f"{GREEN}[Research Output] Evidence: {research_output.evidence}{RESET}")
    memory.save_session("research_output", research_output)
    
    # Rate limit sleep
    time.sleep(5)

    # Step 3: Analyst Agent
    print(f"\n{BOLD}{CYAN}[Orchestrator Handoff: Research Agent → Analyst Agent]{RESET}")
    analyst_output = analyst_agent(research_output, recalled_context=recalled_context)
    
    # Validation
    if not analyst_output.insights:
        raise ValueError("[Guardrail Alert] Analyst Agent output validation failed: 'insights' is empty.")
    if not analyst_output.risks:
        raise ValueError("[Guardrail Alert] Analyst Agent output validation failed: 'risks' is empty.")
        
    print(f"{GREEN}[Analyst Output] Insights: {len(analyst_output.insights)} observations generated.{RESET}")
    print(f"{GREEN}[Analyst Output] Risks Identified: {len(analyst_output.risks)} threats found.{RESET}")
    memory.save_session("analysis_output", analyst_output)
    
    # Rate limit sleep
    time.sleep(5)

    # Step 4: Report Generator Agent
    print(f"\n{BOLD}{CYAN}[Orchestrator Handoff: Analyst Agent → Report Generator Agent]{RESET}")
    final_report = report_generator_agent(planner_output, research_output, analyst_output)
    
    # Validation
    if not final_report.executive_summary:
        raise ValueError("[Guardrail Alert] Report Generator output validation failed: 'executive_summary' is empty.")
        
    print(f"{GREEN}[Report Generator Output] Executive report compiled.{RESET}")
    memory.save_session("final_report", final_report)
    
    # Save to long term memory on disk
    memory.save_to_long_term(user_query, final_report.model_dump())
    print(f"{BLUE}[Orchestrator] Saved final report to long-term memory store.{RESET}")
    
    return {
        "planner_output": planner_output,
        "research_output": research_output,
        "analysis_output": analyst_output,
        "final_report": final_report
    }
