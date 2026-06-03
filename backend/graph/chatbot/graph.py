"""
Compile the chatbot LangGraph agent.

Graph topology:
    START ──▶ chatbot ──▶ END
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.graph.chatbot.nodes import chatbot_node
from backend.graph.chatbot.state import ChatState

builder = StateGraph(ChatState)
builder.add_node("chatbot", chatbot_node)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
