"""
Short-term session memory checkpointer using LangGraph MemorySaver.

Keyed by `thread_id` (session ID).
"""

from langgraph.checkpoint.memory import MemorySaver

_checkpointer = MemorySaver()


def get_checkpointer():
    """Returns singleton MemorySaver instance for short-term graph checkpointing."""
    return _checkpointer
