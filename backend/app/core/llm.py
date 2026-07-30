"""
Async OpenRouter client for RAG synthesis, history summarization, and memory fact extraction.
"""

import httpx
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "You are AI Nexus, an intelligent RAG assistant. Answer the user's question "
    "strictly using the provided context documents.\n"
    "Rules:\n"
    "- Base your answer ONLY on the provided context documents.\n"
    "- If the context does not contain enough information, state that clearly.\n"
    "- Cite the source document names when referencing information.\n"
    "- Be concise, accurate, and structured."
)

SUMMARY_SYSTEM_PROMPT = (
    "Summarize the following conversation history into 3-4 concise bullet points. "
    "Focus on key topics discussed, facts stated, and questions asked. "
    "Be brief and objective."
)

EXTRACTION_SYSTEM_PROMPT = (
    "Inspect the conversation snippet below. If the user explicitly mentions a durable, "
    "long-term personal fact, background, or preference (e.g. 'I am a lawyer', 'I prefer Python', "
    "'I work on Project X'), extract it as a single concise fact sentence.\n"
    "If there is NO durable fact worth remembering long-term, output EXACTLY: NOTHING_WORTH_REMEMBERING"
)


def _build_messages(query: str, context: str, history: list) -> list[dict]:
    """Format history, system prompt, context, and query for OpenRouter API."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in history:
        if hasattr(msg, "content"):
            role = "assistant" if getattr(msg, "type", "") in ("ai", "assistant") else "user"
            if getattr(msg, "type", "") == "system":
                continue
            messages.append({"role": role, "content": msg.content})

    user_prompt = f"Context Documents:\n{context}\n\nQuestion: {query}" if context else query
    messages.append({"role": "user", "content": user_prompt})

    return messages


async def call_openrouter(query: str, context: str, history: list, model: str | None = None) -> str:
    """Async single-turn completion request to OpenRouter."""
    target_model = model or settings.DEFAULT_MODEL
    messages = _build_messages(query, context, history)

    headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
    if settings.APP_URL:
        headers["HTTP-Referer"] = settings.APP_URL

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": target_model,
                    "messages": messages,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            answer = resp.json()["choices"][0]["message"]["content"]

        logger.info(f"OpenRouter [{target_model}] generated response: {answer[:80]}...")
        return answer
    except Exception as e:
        logger.error(f"OpenRouter synthesis call failed ({target_model}): {e}")
        return f"I encountered an issue generating a response: {str(e)}"


async def call_openrouter_summary(messages: list) -> str:
    """Summarize older conversation turns using the fast summary model."""
    conversation_text = "\n".join(
        f"{'User' if getattr(m, 'type', '') == 'human' else 'Assistant'}: {m.content}"
        for m in messages if hasattr(m, "content")
    )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
                json={
                    "model": settings.SUMMARY_MODEL,
                    "messages": [
                        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                        {"role": "user", "content": conversation_text},
                    ],
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return "Conversation history summary unavailable."


async def call_openrouter_extract_memory(messages: list) -> str | None:
    """Extract a durable long-term fact from conversation snippet using summary model."""
    conversation_text = "\n".join(
        f"{'User' if getattr(m, 'type', '') == 'human' else 'Assistant'}: {m.content}"
        for m in messages if hasattr(m, "content")
    )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
                json={
                    "model": settings.SUMMARY_MODEL,
                    "messages": [
                        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                        {"role": "user", "content": conversation_text},
                    ],
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            extracted = resp.json()["choices"][0]["message"]["content"].strip()
            if extracted and extracted != "NOTHING_WORTH_REMEMBERING":
                logger.info(f"Extracted durable memory fact: {extracted}")
                return extracted
            return None
    except Exception as e:
        logger.error(f"Fact extraction call failed: {e}")
        return None
