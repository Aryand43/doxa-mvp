"""
Report generator node functions.
"""

from backend.graph.reporter.state import ReportState
from backend.llm import get_llm

_SYSTEM_PROMPT = (
    "You are a professional report generator for a financial intelligence platform. "
    "When given a topic or prompt, produce a clear, well-structured report with "
    "sections, key findings, and actionable insights. Use markdown formatting."
)


async def generate_report_node(state: ReportState) -> dict:
    """Ask the LLM to generate a structured report from the user's prompt."""
    llm = get_llm()

    # Prepend the system instruction to the conversation.
    messages = [("system", _SYSTEM_PROMPT)] + list(state["messages"])
    response = await llm.ainvoke(messages)

    return {
        "messages": [response],
        "report": response.content,
    }
