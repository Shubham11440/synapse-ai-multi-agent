"""
tools.py — Unified mock knowledge-base and market research tools.

search_tool(query)         → dict {results, sources}  — used by Day 1, Day 2
market_search_tool(query)  → dict {results, sources}  — used by Final Project
go_to_market_tool(query)   → dict {results, sources}  — GTM-specific data

All tools share the same return signature so agents handle them identically.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Core knowledge base (Day 1 & Day 2)
# ---------------------------------------------------------------------------
_CORE_DB: dict[str, dict] = {
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
_MARKET_DB: dict[str, dict] = {
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


def _lookup(query: str, db: dict, aliases: dict) -> dict:
    """Generic keyword lookup against a database with alias fallback."""
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


def search_tool(query: str) -> dict:
    """Core knowledge-base search — used by Day 1 and Day 2 agents."""
    return _lookup(query, _CORE_DB, _CORE_ALIASES)


def market_search_tool(query: str) -> dict:
    """Market intelligence search — used by Final Project research agent."""
    return _lookup(query, _MARKET_DB, _MARKET_ALIASES)


def go_to_market_tool(query: str) -> dict:
    """
    Aggregates both core and market results for GTM-type queries.
    Returns a merged dict with combined results and sources.
    """
    core = search_tool(query)
    market = market_search_tool(query)
    return {
        "results": list(set(core["results"] + market["results"])),
        "sources": list(set(core["sources"] + market["sources"])),
    }
