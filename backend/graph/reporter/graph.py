"""
Compile the report generator LangGraph agent.

Graph topology:
    START ──▶ generate_report ──▶ END
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.graph.reporter.nodes import generate_report_node
from backend.graph.reporter.state import ReportState

builder = StateGraph(ReportState)
builder.add_node("generate_report", generate_report_node)
builder.add_edge(START, "generate_report")
builder.add_edge("generate_report", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
