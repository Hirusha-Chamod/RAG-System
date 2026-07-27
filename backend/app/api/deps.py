"""
Shared FastAPI dependencies injected via Depends().

Usage in route handlers:
    @router.post("/chat")
    async def chat(graph = Depends(get_graph)):
        result = await graph.ainvoke(...)
"""

from fastapi import Request


def get_graph(request: Request):
    """Returns the compiled LangGraph workflow stored on app.state.
    
    Set during the lifespan startup in main.py.
    Available after Phase 3 when the graph is built.
    """
    return request.app.state.graph
