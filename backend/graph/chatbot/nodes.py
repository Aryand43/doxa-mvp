"""
Chatbot node functions.
"""

from backend.graph.chatbot.state import ChatState
from backend.llm import get_llm


async def chatbot_node(state: ChatState) -> dict:
    """Call the LLM with the full conversation history and return its reply."""
    llm = get_llm()
    response = await llm.ainvoke(state["messages"])
    return {"messages": [response]}
