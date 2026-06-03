"""
Chatbot agent state.

Uses LangGraph's `add_messages` annotation so that each node's returned
messages are *appended* to the list rather than replacing it.
"""

from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ChatState(TypedDict):
    """Shared state that flows through every node in the chatbot graph."""

    # The full conversation history.  `add_messages` merges new messages
    # into the existing list (and handles de-duplication by message ID).
    messages: Annotated[list, add_messages]
