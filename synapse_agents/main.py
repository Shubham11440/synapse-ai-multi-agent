"""
main.py — Unified CLI entrypoint for Synapse AI.
Provides runner scripts, baseline comparative metrics, and execution triggers.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Any

import config
from orchestrator import run_2agent, run_4agent, run_company_system
from agents import single_agent

# Initialize CLI Logger
logger = logging.getLogger("SynapseAI")

# Test queries per mode
QUERIES_2AGENT: list[str] = [
    "How can AI agents improve customer support?",
    "How can AI agents help sales teams?",
    "What are the benefits of AI automation in operations?",
    "What is the weather in San Francisco?",       # triggers guardrail fallback
]

QUERIES_4AGENT: list[str] = [
    "Analyze the benefits of AI agents for customer support teams.",
    "Research how AI can improve sales productivity.",
    "Create a business analysis on AI automation in operations.",
]

QUERIES_COMPANY: list[str] = [
    "Create a go-to-market strategy for an AI customer support product.",
    "Analyze the opportunity for AI in customer success operations.",
    "Prepare a business case for AI-powered support automation.",
]

_SLEEP: int = config.RATE_LIMIT_SLEEP_SECONDS


def _section(title: str) -> None:
    """Logs a section banner block."""
    border = "#" * 70
    logger.info(f"\n{border}\n {title}\n{border}")


def _print_report(report: Any) -> None:
    """Logs a formatted executive report summary."""
    d = report.model_dump() if hasattr(report, "model_dump") else report
    msg = (
        f"\nExecutive Summary:\n{d.get('executive_summary', '')}\n\n"
        "Key Points:\n"
    )
    for pt in d.get("key_points", []):
        msg += f"  - {pt}\n"
    msg += "\nNext Steps:\n"
    for ns in d.get("next_steps", []):
        msg += f"  -> {ns}\n"
    logger.info(msg)


def _comparison_table(mode: str) -> None:
    """Logs a comparative table showing multi-agent vs single-agent features."""
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
    border = "=" * 72
    table_msg = (
        f"\n{border}\n"
        f" Comparison: {col_label} System vs Single-Agent Baseline\n"
        f"{border}\n"
        f"| {'Metric':<28} | {col_label+' System':<26} | {'Single-Agent':<14} |\n"
        f"|{'-'*30}|{'-'*28}|{'-'*16}|\n"
    )
    for metric, multi, single in rows[mode]:
        table_msg += f"| {metric:<28} | {multi:<26} | {single:<14} |\n"
    table_msg += f"{border}\n"
    logger.info(table_msg)


# ---------------------------------------------------------------------------
# Mode runners
# ---------------------------------------------------------------------------

def run_mode_2agent() -> None:
    """
    Run scenarios in 2-agent mode.

    Purpose:
        Iterate through test queries and print comparative summaries.
    """
    _section("MODE: 2-AGENT PIPELINE (Day 1)")
    for i, query in enumerate(QUERIES_2AGENT):
        if i > 0:
            logger.warning(f"[Rate Limiter] Sleeping {_SLEEP}s...")
            time.sleep(_SLEEP)
        logger.info(f"\n>>> Scenario {i+1}/{len(QUERIES_2AGENT)}: {query}")
        try:
            result = run_2agent(query)
            logger.info(f"\nSummary:\n{result['summary'].final_summary}")
            time.sleep(5)
            baseline = single_agent(query)
            logger.info(f"\nSingle-Agent Summary:\n{baseline.executive_summary}")
        except Exception as exc:
            logger.error(f"[ERROR] {exc}", exc_info=True)
    _comparison_table("2agent")


def run_mode_4agent() -> None:
    """
    Run scenarios in 4-agent mode.

    Purpose:
        Iterate through test queries and print comparative reports.
    """
    _section("MODE: 4-AGENT PIPELINE (Day 2)")
    for i, query in enumerate(QUERIES_4AGENT):
        if i > 0:
            logger.warning(f"[Rate Limiter] Sleeping {_SLEEP}s...")
            time.sleep(_SLEEP)
        logger.info(f"\n>>> Scenario {i+1}/{len(QUERIES_4AGENT)}: {query}")
        try:
            result = run_4agent(query)
            _print_report(result["final_report"])
            time.sleep(5)
            baseline = single_agent(query)
            logger.info(f"\nSingle-Agent Summary:\n{baseline.executive_summary}")
        except Exception as exc:
            logger.error(f"[ERROR] {exc}", exc_info=True)
    _comparison_table("4agent")


def run_mode_company() -> None:
    """
    Run scenarios in 6-agent company mode.

    Purpose:
        Iterate through test queries and print full business strategies with review checks.
    """
    _section("MODE: 6-AGENT COMPANY SYSTEM (Final Project)")
    for i, query in enumerate(QUERIES_COMPANY):
        if i > 0:
            logger.warning(f"[Rate Limiter] Sleeping {_SLEEP}s...")
            time.sleep(_SLEEP)
        logger.info(f"\n>>> Scenario {i+1}/{len(QUERIES_COMPANY)}: {query}")
        try:
            result = run_company_system(query)
            _print_report(result["final_report"])
            review = result.get("review_output")
            if review:
                rd = review.model_dump() if hasattr(review, "model_dump") else review
                logger.info(f"\nReviewer: approved={rd['approved']} score={rd['quality_score']}")
            time.sleep(5)
            baseline = single_agent(query)
            logger.info(f"\nSingle-Agent Summary:\n{baseline.executive_summary}")
        except Exception as exc:
            logger.error(f"[ERROR] {exc}", exc_info=True)
    _comparison_table("company")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """
    CLI Entrypoint.

    Purpose:
        Parse command-line flags and dispatch execution tasks.
    """
    parser = argparse.ArgumentParser(description="Synapse AI — unified multi-agent CLI")
    parser.add_argument(
        "--mode",
        choices=["2agent", "4agent", "company", "all"],
        default="company",
        help="Pipeline to run (default: company)",
    )
    args = parser.parse_args()

    # Configure stdout logging handler dynamically for the CLI runner
    logger.setLevel(logging.INFO)

    if args.mode in ("2agent", "all"):
        run_mode_2agent()

    if args.mode in ("4agent", "all"):
        if args.mode == "all":
            logger.warning(f"\n[Main] Sleeping {_SLEEP}s before 4-agent run...")
            time.sleep(_SLEEP)
        run_mode_4agent()

    if args.mode in ("company", "all"):
        if args.mode == "all":
            logger.warning(f"\n[Main] Sleeping {_SLEEP}s before company system run...")
            time.sleep(_SLEEP)
        run_mode_company()


if __name__ == "__main__":
    main()
