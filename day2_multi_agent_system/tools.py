def search_tool(query: str) -> list:
    """
    A mock search tool that simulates searching internal documentation for AI benefits.
    
    Args:
        query: The search query string.
        
    Returns:
        list: A list of relevant facts and evidence snippets.
    """
    database = {
        "customer support": [
            "AI agents reduce customer support response times by up to 50% through automated FAQ routing.",
            "Always-on 24/7 AI agents prevent SLA breaches during overnight shifts and weekends.",
            "Self-service AI agents successfully resolve up to 70% of common tier-1 repetitive questions, lowering support costs.",
            "Implementing AI-guided agents increases first-contact resolution (FCR) rates by 30%."
        ],
        "sales productivity": [
            "AI agents automate prospect lead qualification in real-time, scoring leads based on initial conversations.",
            "Routine follow-up emails and meeting scheduling automated by AI lead to a 3x increase in prospect engagement.",
            "AI systems automatically sync logs and notes directly to the CRM, improving team coordination and CRM hygiene.",
            "Sales teams utilizing AI productivity tools spend 40% more time on live closing calls."
        ],
        "operations automation": [
            "AI operations agents optimize department workflow orchestration, reducing manual routing errors by 35%.",
            "Automated inventory monitoring agents auto-trigger replenishment orders when safety thresholds are breached.",
            "Data entry workflows integrated with AI parsing models report a 90% reduction in manual processing time.",
            "Operational processing times for back-office documentation drop from 3 days to under 4 hours using AI agents."
        ]
    }
    
    query_lower = query.lower()
    results = []
    
    for key, values in database.items():
        # Match keywords like "customer support", "sales", "operations"
        words = key.split()
        if key in query_lower or any(word in query_lower for word in words):
            results.extend(values)
            
    if results:
        # Return unique items to avoid repeats
        return list(set(results))
        
    return ["No strong database results found for query: " + query]
