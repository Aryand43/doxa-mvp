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
    severity: str


class CrawlerState(TypedDict):
    """State for the data crawler / anomaly detection graph."""

    messages: Annotated[list, add_messages]

    source: str

    findings: list[Finding]
