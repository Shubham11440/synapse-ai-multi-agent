"""
main.py — Unified CLI entrypoint for the Synapse multi-agent system.

Usage:
    python synapse_agents/main.py --mode 2agent   # Day 1: 2-agent pipeline
    python synapse_agents/main.py --mode 4agent   # Day 2: 4-agent pipeline
    python synapse_agents/main.py                 # Default: runs both

Each mode runs a battery of test queries and then prints a side-by-side
comparison against the single-agent baseline.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import os

# Ensure this package directory is on the path regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import run_2agent, run_4agent, _G, _B, _Y, _C, _R, _X, _W
from agents import single_agent

# ---------------------------------------------------------------------------
# Test queries
# ---------------------------------------------------------------------------
QUERIES_2AGENT = [
    "How can AI agents improve customer support?",
    "How can AI agents help sales teams?",
    "What are the benefits of AI automation in operations?",
    "What is the weather today in San Francisco?",   # triggers fallback guardrail
]

QUERIES_4AGENT = [
    "Analyze the benefits of AI agents for customer support teams.",
    "Research how AI can improve sales productivity.",
    "Create a business analysis on AI automation in operations.",
    "What is the weather today in San Francisco?",   # triggers guardrail
    "Analyze the benefits of AI agents for customer support teams.",  # triggers recall
]

_SLEEP_BETWEEN = 15  # seconds between query blocks to respect rate limits


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _print_section(title: str, data: dict | str) -> None:
    print(f"\n{_W}{_B}--- {title} ---{_X}")
    if isinstance(data, str):
        print(data)
    else:
        print(json.dumps(data, indent=2))


def _comparison_table(mode: str) -> None:
    rows = {
        "2agent": [
            ("Task Decomposition",    "No (single query in)",              "No"),
            ("Separation of Concerns","High (Research + Summarizer)",       "None"),
            ("Intermediate State",    "Yes (research findings saved)",      "No"),
            ("Guardrails",            "2 validation checks",                "0"),
            ("Memory Layer",          "Session only",                       "None"),
            ("Debuggability",         "Medium (2 visible stages)",          "Low"),
        ],
        "4agent": [
            ("Task Decomposition",    "Yes (Planner → subtasks)",           "No"),
            ("Separation of Concerns","High (4 specialised agents)",        "None"),
            ("Intermediate State",    "Yes (plan + research + analysis)",   "No"),
            ("Guardrails",            "4 validation checks",                "0"),
            ("Memory Layer",          "Session + JSON disk + recall",       "None"),
            ("Debuggability",         "Excellent (every stage visible)",    "Low"),
        ],
    }
    selected = rows.get(mode, rows["4agent"])
    col_label = "2-Agent" if mode == "2agent" else "4-Agent"
    print(f"\n{_W}{_C}{'='*70}")
    print(f" Comparison: {col_label} Orchestrator vs Single-Agent Baseline")
    print(f"{'='*70}{_X}")
    print(f"| {'Metric':<26} | {col_label+' System':<28} | {'Single-Agent':<18} |")
    print(f"|{'-'*28}|{'-'*30}|{'-'*20}|")
    for metric, multi, single in selected:
        print(f"| {metric:<26} | {multi:<28} | {single:<18} |")
    print(f"{_W}{_C}{'='*70}{_X}\n")


# ---------------------------------------------------------------------------
# Mode runners
# ---------------------------------------------------------------------------

def run_mode_2agent() -> None:
    print(f"\n{_W}{_Y}{'#'*70}")
    print(" MODE: 2-AGENT PIPELINE (Day 1)")
    print(f"{'#'*70}{_X}\n")

    for i, query in enumerate(QUERIES_2AGENT):
        if i > 0:
            print(f"{_Y}[Rate Limiter] Sleeping {_SLEEP_BETWEEN}s ...{_X}")
            time.sleep(_SLEEP_BETWEEN)

        print(f"\n{_W}{_C}>>> Scenario {i+1}/{len(QUERIES_2AGENT)}: {query}{_X}")
        try:
            result = run_2agent(query)

            # Multi-agent output
            _print_section("Research Findings", result["research"].model_dump())
            _print_section("Summarizer Output", result["summary"].model_dump())

            # Baseline comparison (delay to avoid rate limits)
            time.sleep(_RATE_SLEEP_INNER := 5)
            baseline = single_agent(query)
            _print_section("Single-Agent Baseline", baseline.model_dump())

        except Exception as exc:
            print(f"{_R}{_W}✖ Error: {exc}{_X}", file=sys.stderr)

    _comparison_table("2agent")


def run_mode_4agent() -> None:
    print(f"\n{_W}{_Y}{'#'*70}")
    print(" MODE: 4-AGENT PIPELINE (Day 2)")
    print(f"{'#'*70}{_X}\n")

    for i, query in enumerate(QUERIES_4AGENT):
        if i > 0:
            print(f"{_Y}[Rate Limiter] Sleeping {_SLEEP_BETWEEN}s ...{_X}")
            time.sleep(_SLEEP_BETWEEN)

        print(f"\n{_W}{_C}>>> Scenario {i+1}/{len(QUERIES_4AGENT)}: {query}{_X}")
        try:
            result = run_4agent(query)

            report = result["final_report"]
            print(f"\n{_W}{_G}Executive Summary:{_X}\n{report.executive_summary}")
            print(f"\n{_W}{_G}Key Points:{_X}")
            for pt in report.key_points:
                print(f"  • {pt}")
            print(f"\n{_W}{_G}Next Steps:{_X}")
            for ns in report.next_steps:
                print(f"  → {ns}")

            # Baseline
            time.sleep(5)
            baseline = single_agent(query)
            _print_section("Single-Agent Baseline", baseline.model_dump())

        except Exception as exc:
            print(f"{_R}{_W}✖ Error: {exc}{_X}", file=sys.stderr)

    _comparison_table("4agent")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synapse Multi-Agent System — unified entrypoint"
    )
    parser.add_argument(
        "--mode",
        choices=["2agent", "4agent", "both"],
        default="both",
        help="Pipeline to run: '2agent' (Day 1), '4agent' (Day 2), or 'both' (default).",
    )
    args = parser.parse_args()

    if args.mode in ("2agent", "both"):
        run_mode_2agent()

    if args.mode in ("4agent", "both"):
        if args.mode == "both":
            print(f"\n{_Y}[Main] Sleeping {_SLEEP_BETWEEN}s before starting 4-agent run...{_X}")
            time.sleep(_SLEEP_BETWEEN)
        run_mode_4agent()


if __name__ == "__main__":
    main()
