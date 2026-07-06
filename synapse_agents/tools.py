"""
tools.py — Unified mock knowledge-base and market research tools.
Supports keyword matching across customer support, sales, operations, and GTM.
"""
from __future__ import annotations

import logging
from exceptions import SearchToolError

logger = logging.getLogger("SynapseAI")

# ---------------------------------------------------------------------------
# Core knowledge base (Day 1 & Day 2)
# ---------------------------------------------------------------------------
_CORE_DB: dict[str, dict[str, list[str]]] = {
    "customer support": {
        "results": [
            "AI agents reduce customer support response times by up to 50% through automated FAQ routing.",
            "Always-on 24/7 AI agents prevent SLA breaches during overnight shifts and weekends.",
            "Self-service AI agents resolve up to 70% of tier-1 repetitive tickets, lowering costs.",
            "AI-guided agents increase first-contact resolution (FCR) rates by 30%.",
        ],
        "sources": ["Support Automation Guide", "Customer Support Metrics Report 2025"],
    },
    "sales": {
        "results": [
            "AI agents automate lead qualification in real-time using conversation scoring.",
            "Routine follow-up automation drives a 3× increase in prospect engagement.",
            "AI auto-syncs CRM logs, improving data hygiene and team coordination.",
            "Sales reps using AI tools spend 40% more time on live closing calls.",
        ],
        "sources": ["Sales Enablement Strategies", "CRM Integration Whitepaper v2"],
    },
    "operations": {
        "results": [
            "AI workflow agents reduce manual routing errors by 35%.",
            "Automated inventory agents trigger replenishment orders at safety thresholds.",
            "AI parsing models cut back-office document processing time by 90%.",
            "Processing times drop from 3 days to under 4 hours with AI automation.",
        ],
        "sources": ["Operations Optimization Guide", "Industry Automation Benchmark Survey"],
    },
}

_CORE_ALIASES: dict[str, str] = {
    "support": "customer support",
    "customer": "customer support",
    "productivity": "sales",
    "operation": "operations",
    "automation": "operations",
}

# ---------------------------------------------------------------------------
# Market intelligence database (Final Project)
# ---------------------------------------------------------------------------
_MARKET_DB: dict[str, dict[str, list[str]]] = {
    "ai support": {
        "results": [
            "The AI customer service market is projected to reach $11.5B by 2026 (CAGR 23%).",
            "72% of enterprise buyers cite 'speed of resolution' as the top support KPI.",
            "Conversational AI reduces average handle time (AHT) by 40% in contact centres.",
            "Mid-market SaaS companies are the fastest adopters of AI support tooling.",
            "Human escalation is required in only 18% of AI-handled support interactions.",
        ],
        "sources": ["Gartner AI CX Report 2025", "Forrester Contact Centre AI Study"],
    },
    "go to market": {
        "results": [
            "Effective GTM strategies start with a tightly defined ICP (Ideal Customer Profile).",
            "Pilot programs with 30-day free trials increase SMB adoption rates by 60%.",
            "Case-study-led content marketing drives 3× faster enterprise pipeline.",
            "Positioning around ROI (cost savings + speed) outperforms feature-led messaging.",
            "Channel partnerships with CRM vendors (HubSpot, Salesforce) accelerate reach.",
        ],
        "sources": ["OpenView GTM Benchmark 2025", "SaaStr Playbook for B2B AI Products"],
    },
    "market opportunity": {
        "results": [
            "AI adoption in business operations has grown 270% over the past 4 years.",
            "Companies that deploy AI report an average 32% reduction in operational costs.",
            "Only 14% of SMBs have deployed AI beyond basic automation — large whitespace remains.",
            "AI-first vendors are capturing 2× the net revenue retention of traditional tools.",
        ],
        "sources": ["McKinsey Global AI Survey 2025", "CB Insights AI Market Map"],
    },
}

_MARKET_ALIASES: dict[str, str] = {
    "support": "ai support",
    "customer support": "ai support",
    "gtm": "go to market",
    "launch": "go to market",
    "strategy": "go to market",
    "opportunity": "market opportunity",
    "market": "market opportunity",
}


def _lookup(query: str, db: dict[str, dict[str, list[str]]], aliases: dict[str, str]) -> dict[str, list[str]]:
    """
    Look up key findings and sources from the database based on query.

    Purpose:
        Perform simple keyword matching to mock search operations.

    Arguments:
        query: The search term or prompt query.
        db: The database dictionary to search against.
        aliases: Alias mappings for fallback key lookups.

    Returns:
        A dictionary with "results" and "sources" lists.

    Raises:
        SearchToolError: If query parameter is empty.
    """
    if not query:
        raise SearchToolError("Query query string cannot be empty.")

    q = query.lower()
    for key, data in db.items():
        if key in q:
            return data
    for alias, key in aliases.items():
        if alias in q:
            return db.get(key, {})
    return {
        "results": [f"No knowledge-base entry found for: '{query}'."],
        "sources": ["Default Knowledge Index"],
    }


def search_tool(query: str) -> dict[str, list[str]]:
    """
    Search the core business database for facts.

    Purpose:
        Expose internal database findings for client workflow agents (Day 1 / Day 2).

    Arguments:
        query: Search query or business topic.

    Returns:
        A dictionary with results and sources list.

    Raises:
        SearchToolError: If search lookup fails.
    """
    try:
        return _lookup(query, _CORE_DB, _CORE_ALIASES)
    except Exception as exc:
        logger.error(f"Search tool lookup failed: {exc}")
        raise SearchToolError(f"Core search tool encountered an error: {exc}", exc)


def market_search_tool(query: str) -> dict[str, list[str]]:
    """
    Search the market intelligence database.

    Purpose:
        Provide market trends, CAGR, and sizing stats for the Final Project research agent.

    Arguments:
        query: Search query or business topic.

    Returns:
        A dictionary with results and sources list.

    Raises:
        SearchToolError: If market search lookup fails.
    """
    try:
        return _lookup(query, _MARKET_DB, _MARKET_ALIASES)
    except Exception as exc:
        logger.error(f"Market search tool lookup failed: {exc}")
        raise SearchToolError(f"Market search tool encountered an error: {exc}", exc)


def go_to_market_tool(query: str) -> dict[str, list[str]]:
    """
    Merges both core and market databases to answer GTM requests.

    Purpose:
        Provide combined answers for enterprise launch strategies.

    Arguments:
        query: GTM topic or query.

    Returns:
        A dictionary with merged results and unique sources list.

    Raises:
        SearchToolError: If merged lookup fails.
    """
    try:
        core = search_tool(query)
        market = market_search_tool(query)
        return {
            "results": list(set(core["results"] + market["results"])),
            "sources": list(set(core["sources"] + market["sources"])),
        }
    except Exception as exc:
        logger.error(f"Go to market tool lookup failed: {exc}")
        raise SearchToolError(f"GTM tool merged search encountered an error: {exc}", exc)
