"""
Report generator agent state.
"""

from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ReportState(TypedDict):
    """State for the report generation graph."""

    messages: Annotated[list, add_messages]

    report: str
