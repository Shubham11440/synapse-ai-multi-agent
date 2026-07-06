def mock_search(query: str) -> dict:
    """
    A mock search function that simulates scanning an internal knowledge base.
    
    Args:
        query: The search query string.
        
    Returns:
        dict: A dictionary containing a list of 'results' and a list of 'sources'.
    """
    # Expanded database to cover all recommended test scenarios
    database = {
        "customer support": {
            "results": [
                "AI agents can reduce customer support response times by up to 50% through instant automated replies.",
                "AI agents provide consistent 24/7 support coverage, mitigating overnight SLA breaches.",
                "AI agents lower customer service costs by successfully resolving up to 70% of common tier-1 FAQs."
            ],
            "sources": [
                "Mock Knowledge Base: Support Automation Guide",
                "Customer Support Metrics Report 2025"
            ]
        },
        "sales": {
            "results": [
                "AI agents can qualify inbound leads in real-time, scoring them based on conversation history.",
                "AI agents automate routine follow-up emails, leading to a 3x increase in prospect engagement.",
                "AI agents automatically sync conversation logs to the CRM, improving team coordination and productivity."
            ],
            "sources": [
                "Mock Knowledge Base: Sales Enablement Strategies",
                "CRM Integration Whitepaper v2"
            ]
        },
        "operations": {
            "results": [
                "AI automation optimizes workflow orchestration by automatically routing tasks between departments.",
                "AI agents monitor inventory levels and automatically generate replenishment requests when thresholds are breached.",
                "Operational systems integrated with AI agents report a 35% reduction in manual data entry errors."
            ],
            "sources": [
                "Mock Knowledge Base: Operations Optimization Guide",
                "Industry Automation Benchmark Survey"
            ]
        }
    }

    query_lower = query.lower()
    for key, data in database.items():
        if key in query_lower:
            return data

    # Default fallback if no keywords match
    return {
        "results": [
            f"No specific internal knowledge base entry found for topic in: '{query}'."
        ],
        "sources": [
            "Default Knowledge Index"
        ]
    }
