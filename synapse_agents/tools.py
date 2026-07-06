"""
tools.py — Unified mock knowledge-base search tool.

Returns structured results with sources (for Day 1)
or plain evidence lists (for Day 2), depending on the caller.
A single search function handles both needs.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Shared knowledge base — covers all test scenarios across Day 1 & Day 2
# ---------------------------------------------------------------------------
_DATABASE: dict[str, dict] = {
    "customer support": {
        "results": [
            "AI agents reduce customer support response times by up to 50% through automated FAQ routing.",
            "Always-on 24/7 AI agents prevent SLA breaches during overnight shifts and weekends.",
            "Self-service AI agents resolve up to 70% of tier-1 repetitive tickets, lowering costs.",
            "AI-guided agents increase first-contact resolution (FCR) rates by 30%.",
        ],
        "sources": [
            "Support Automation Guide",
            "Customer Support Metrics Report 2025",
        ],
    },
    "sales": {
        "results": [
            "AI agents automate lead qualification in real-time using conversation scoring.",
            "Routine follow-up automation drives a 3× increase in prospect engagement.",
            "AI auto-syncs CRM logs, improving data hygiene and team coordination.",
            "Sales reps using AI tools spend 40% more time on live closing calls.",
        ],
        "sources": [
            "Sales Enablement Strategies",
            "CRM Integration Whitepaper v2",
        ],
    },
    "operations": {
        "results": [
            "AI workflow agents reduce manual routing errors by 35%.",
            "Automated inventory agents trigger replenishment orders at safety thresholds.",
            "AI parsing models cut back-office document processing time by 90%.",
            "Processing times drop from 3 days to under 4 hours with AI automation.",
        ],
        "sources": [
            "Operations Optimization Guide",
            "Industry Automation Benchmark Survey",
        ],
    },
}

# Alias keywords → database keys
_ALIASES: dict[str, str] = {
    "support": "customer support",
    "customer": "customer support",
    "sales": "sales",
    "productivity": "sales",
    "operation": "operations",
    "automation": "operations",
}


def search_tool(query: str) -> dict:
    """
    Search the mock knowledge base.

    Returns a dict with keys:
      - 'results' : List[str]  — fact snippets
      - 'sources' : List[str]  — source titles

    Works for both Day 1 (uses 'results' + 'sources')
    and Day 2 (callers extract 'results' as evidence list).
    """
    q = query.lower()

    # Direct key match
    for key, data in _DATABASE.items():
        if key in q:
            return data

    # Alias match
    for alias, key in _ALIASES.items():
        if alias in q:
            return _DATABASE[key]

    # Fallback
    return {
        "results": [f"No knowledge-base entry found for: '{query}'."],
        "sources": ["Default Knowledge Index"],
    }
