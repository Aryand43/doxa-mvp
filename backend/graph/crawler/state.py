"""
Data crawler agent state.
"""

from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class Finding(TypedDict):
    """A single anomaly or noteworthy finding."""

    source: str
    description: str
    severity: str  # "low" | "medium" | "high"


class CrawlerState(TypedDict):
    """State for the data crawler / anomaly detection graph."""

    # Conversation / instruction messages sent to the LLM.
    messages: Annotated[list, add_messages]

    # The data source or URL to analyze.
    source: str

    # Structured list of anomalies / findings.
    findings: list[Finding]
