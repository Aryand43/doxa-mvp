"""
Report generator agent state.
"""

from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ReportState(TypedDict):
    """State for the report generation graph."""

    # Conversation / instruction messages sent to the LLM.
    messages: Annotated[list, add_messages]

    # The final generated report text.
    report: str
