"""
main.py — Unified CLI entrypoint for the Synapse multi-agent system.

Usage:
    python synapse_agents/main.py --mode 2agent    # Day 1
    python synapse_agents/main.py --mode 4agent    # Day 2
    python synapse_agents/main.py --mode company   # Final: 6-agent system
    python synapse_agents/main.py --mode all       # Run all three in sequence
    python synapse_agents/main.py                  # Defaults to 'company'
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import run_2agent, run_4agent, run_company_system
from orchestrator import _G, _B, _Y, _C, _R, _X, _W
from agents import single_agent

# ---------------------------------------------------------------------------
# Test queries per mode
# ---------------------------------------------------------------------------
QUERIES_2AGENT = [
    "How can AI agents improve customer support?",
    "How can AI agents help sales teams?",
    "What are the benefits of AI automation in operations?",
    "What is the weather in San Francisco?",       # triggers guardrail fallback
]

QUERIES_4AGENT = [
    "Analyze the benefits of AI agents for customer support teams.",
    "Research how AI can improve sales productivity.",
    "Create a business analysis on AI automation in operations.",
]

QUERIES_COMPANY = [
    "Create a go-to-market strategy for an AI customer support product.",
    "Analyze the opportunity for AI in customer success operations.",
    "Prepare a business case for AI-powered support automation.",
]

_SLEEP = 15   # seconds between query blocks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _section(title: str) -> None:
    print(f"\n{_W}{_Y}{'#'*70}\n {title}\n{'#'*70}{_X}")


def _print_report(report) -> None:
    d = report.model_dump() if hasattr(report, "model_dump") else report
    print(f"\n{_W}{_G}Executive Summary:{_X}\n{d.get('executive_summary', '')}")
    print(f"\n{_W}{_G}Key Points:{_X}")
    for pt in d.get("key_points", []):
        print(f"  - {pt}")
    print(f"\n{_W}{_G}Next Steps:{_X}")
    for ns in d.get("next_steps", []):
        print(f"  -> {ns}")


def _comparison_table(mode: str) -> None:
    rows = {
        "2agent": [
            ("Agents Used",           "2 (Research + Summarizer)",         "1"),
            ("Task Decomposition",    "None",                               "None"),
            ("Intermediate State",    "Research findings",                  "None"),
            ("Guardrails",            "2 checks",                           "0"),
            ("Monitoring",            "None",                               "None"),
            ("Memory",                "Session only",                       "None"),
        ],
        "4agent": [
            ("Agents Used",           "4",                                  "1"),
            ("Task Decomposition",    "Planner subtasks",                   "None"),
            ("Intermediate State",    "Plan + Research + Analysis",         "None"),
            ("Guardrails",            "4 checks",                           "0"),
            ("Monitoring",            "None",                               "None"),
            ("Memory",                "Session + JSON disk",                "None"),
        ],
        "company": [
            ("Agents Used",           "6",                                  "1"),
            ("Task Decomposition",    "Company Planner (complexity est.)",  "None"),
            ("Intermediate State",    "Plan/Research/Analysis/Strategy",    "None"),
            ("Guardrails",            "6 checks + Reviewer retry",          "0"),
            ("Monitoring",            "Per-agent latency + logs.json",      "None"),
            ("Memory",                "Session + JSON disk + recall",       "None"),
            ("API",                   "FastAPI /run /logs /health",         "None"),
            ("Dashboard",             "Streamlit real-time",                "None"),
        ],
    }
    col_label = {"2agent": "2-Agent", "4agent": "4-Agent", "company": "6-Agent Company"}[mode]
    print(f"\n{_W}{_C}{'='*72}")
    print(f" Comparison: {col_label} System vs Single-Agent Baseline")
    print(f"{'='*72}{_X}")
    print(f"| {'Metric':<28} | {col_label+' System':<26} | {'Single-Agent':<14} |")
    print(f"|{'-'*30}|{'-'*28}|{'-'*16}|")
    for metric, multi, single in rows[mode]:
        print(f"| {metric:<28} | {multi:<26} | {single:<14} |")
    print(f"{_W}{_C}{'='*72}{_X}\n")


# ---------------------------------------------------------------------------
# Mode runners
# ---------------------------------------------------------------------------

def run_mode_2agent() -> None:
    _section("MODE: 2-AGENT PIPELINE (Day 1)")
    for i, query in enumerate(QUERIES_2AGENT):
        if i > 0:
            print(f"{_Y}[Rate Limiter] Sleeping {_SLEEP}s...{_X}")
            time.sleep(_SLEEP)
        print(f"\n{_W}{_C}>>> Scenario {i+1}/{len(QUERIES_2AGENT)}: {query}{_X}")
        try:
            result = run_2agent(query)
            print(f"\n{_W}{_G}Summary:{_X}\n{result['summary'].final_summary}")
            time.sleep(5)
            baseline = single_agent(query)
            print(f"\n{_W}{_B}Single-Agent Summary:{_X}\n{baseline.executive_summary}")
        except Exception as exc:
            print(f"{_R}{_W}[ERROR] {exc}{_X}", file=sys.stderr)
    _comparison_table("2agent")


def run_mode_4agent() -> None:
    _section("MODE: 4-AGENT PIPELINE (Day 2)")
    for i, query in enumerate(QUERIES_4AGENT):
        if i > 0:
            print(f"{_Y}[Rate Limiter] Sleeping {_SLEEP}s...{_X}")
            time.sleep(_SLEEP)
        print(f"\n{_W}{_C}>>> Scenario {i+1}/{len(QUERIES_4AGENT)}: {query}{_X}")
        try:
            result = run_4agent(query)
            _print_report(result["final_report"])
            time.sleep(5)
            baseline = single_agent(query)
            print(f"\n{_W}{_B}Single-Agent Summary:{_X}\n{baseline.executive_summary}")
        except Exception as exc:
            print(f"{_R}{_W}[ERROR] {exc}{_X}", file=sys.stderr)
    _comparison_table("4agent")


def run_mode_company() -> None:
    _section("MODE: 6-AGENT COMPANY SYSTEM (Final Project)")
    for i, query in enumerate(QUERIES_COMPANY):
        if i > 0:
            print(f"{_Y}[Rate Limiter] Sleeping {_SLEEP}s...{_X}")
            time.sleep(_SLEEP)
        print(f"\n{_W}{_C}>>> Scenario {i+1}/{len(QUERIES_COMPANY)}: {query}{_X}")
        try:
            result = run_company_system(query)
            _print_report(result["final_report"])
            review = result.get("review_output")
            if review:
                rd = review.model_dump() if hasattr(review, "model_dump") else review
                print(f"\n{_W}{_G}Reviewer: approved={rd['approved']} score={rd['quality_score']}{_X}")
            time.sleep(5)
            baseline = single_agent(query)
            print(f"\n{_W}{_B}Single-Agent Summary:{_X}\n{baseline.executive_summary}")
        except Exception as exc:
            print(f"{_R}{_W}[ERROR] {exc}{_X}", file=sys.stderr)
    _comparison_table("company")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Synapse AI — unified multi-agent CLI")
    parser.add_argument(
        "--mode",
        choices=["2agent", "4agent", "company", "all"],
        default="company",
        help="Pipeline to run (default: company)",
    )
    args = parser.parse_args()

    if args.mode in ("2agent", "all"):
        run_mode_2agent()

    if args.mode in ("4agent", "all"):
        if args.mode == "all":
            print(f"\n{_Y}[Main] Sleeping {_SLEEP}s before 4-agent run...{_X}")
            time.sleep(_SLEEP)
        run_mode_4agent()

    if args.mode in ("company", "all"):
        if args.mode == "all":
            print(f"\n{_Y}[Main] Sleeping {_SLEEP}s before company system run...{_X}")
            time.sleep(_SLEEP)
        run_mode_company()


if __name__ == "__main__":
    main()
