"""
StateGraph wiring and compilation for the RAG chat workflow.
"""

from langgraph.graph import StateGraph, END
from app.core.state import GraphState
from app.core.nodes import (
    manage_history_node,
    retrieve_node,
    decide_node,
    synthesize_node,
    fallback_node,
)
from app.memory.short_term import get_checkpointer
from app.utils.logging import get_logger

logger = get_logger(__name__)


def build_graph():
    """Build and compile the RAG workflow StateGraph with MemorySaver checkpointer."""
    g = StateGraph(GraphState)

    # 1. Register all 5 nodes
    g.add_node("manage_history", manage_history_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("decide", decide_node)
    g.add_node("synthesize", synthesize_node)
    g.add_node("fallback", fallback_node)

    # 2. Wire static edges
    g.set_entry_point("manage_history")
    g.add_edge("manage_history", "retrieve")
    g.add_edge("retrieve", "decide")

    # 3. Wire conditional edge (Decision Gate)
    g.add_conditional_edges(
        "decide",
        lambda s: "synthesize" if s["relevance_ok"] else "fallback",
        {"synthesize": "synthesize", "fallback": "fallback"},
    )

    # 4. Terminal edges
    g.add_edge("synthesize", END)
    g.add_edge("fallback", END)

    # 5. Compile with session checkpointer
    compiled_graph = g.compile(checkpointer=get_checkpointer())
    logger.info("RAG StateGraph compiled successfully")
    return compiled_graph
