"""
Compile the data crawler LangGraph agent.

Graph topology:
    START ──▶ analyze ──▶ END
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.graph.crawler.nodes import analyze_node
from backend.graph.crawler.state import CrawlerState

builder = StateGraph(CrawlerState)
builder.add_node("analyze", analyze_node)
builder.add_edge(START, "analyze")
builder.add_edge("analyze", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
