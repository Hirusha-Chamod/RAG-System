"""
StateGraph wiring and compilation for the 3-way decision RAG chat workflow.
"""

from langgraph.graph import StateGraph, END
from app.core.state import GraphState
from app.core.nodes import (
    manage_history_node,
    retrieve_node,
    decide_node,
    synthesize_node,
    clarify_node,
    fallback_node,
)
from app.memory.short_term import get_checkpointer
from app.utils.logging import get_logger

logger = get_logger(__name__)


def build_graph():
    """Build and compile the 3-way decision RAG workflow StateGraph."""
    g = StateGraph(GraphState)

    # 1. Register all 6 nodes
    g.add_node("manage_history", manage_history_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("decide", decide_node)
    g.add_node("synthesize", synthesize_node)
    g.add_node("clarify", clarify_node)
    g.add_node("fallback", fallback_node)

    # 2. Wire static edges
    g.set_entry_point("manage_history")
    g.add_edge("manage_history", "retrieve")
    g.add_edge("retrieve", "decide")

    # 3. Wire 3-way conditional edge (Decision Gate)
    g.add_conditional_edges(
        "decide",
        lambda s: s.get("relevance_action", "fallback"),
        {
            "synthesize": "synthesize",
            "clarify": "clarify",
            "fallback": "fallback",
        },
    )

    # 4. Terminal edges
    g.add_edge("synthesize", END)
    g.add_edge("clarify", END)
    g.add_edge("fallback", END)

    # 5. Compile with session checkpointer
    compiled_graph = g.compile(checkpointer=get_checkpointer())
    logger.info("3-Way RAG StateGraph compiled successfully")
    return compiled_graph
