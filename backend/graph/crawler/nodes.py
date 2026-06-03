"""
Data crawler / anomaly detection node functions.
"""

import json

from backend.graph.crawler.state import CrawlerState
from backend.llm import get_llm

_SYSTEM_PROMPT = (
    "You are a data-crawling AI agent for a financial intelligence platform. "
    "Given a data source description, analyze it for anomalies, irregularities, "
    "or noteworthy patterns. Return your findings as a JSON array where each "
    "element has keys: source (str), description (str), severity ('low'|'medium'|'high'). "
    "Return ONLY the JSON array, no other text."
)


async def analyze_node(state: CrawlerState) -> dict:
    """Analyze a data source for anomalies and return structured findings."""
    llm = get_llm()

    messages = [
        ("system", _SYSTEM_PROMPT),
        ("user", f"Data source to analyze: {state['source']}"),
    ] + list(state["messages"])

    response = await llm.ainvoke(messages)

    # Attempt to parse the LLM output as structured JSON.
    try:
        findings = json.loads(response.content)
    except (json.JSONDecodeError, TypeError):
        findings = [
            {
                "source": state["source"],
                "description": response.content,
                "severity": "medium",
            }
        ]

    return {
        "messages": [response],
        "findings": findings,
    }
