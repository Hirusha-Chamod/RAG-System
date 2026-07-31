"""
Async OpenRouter client for RAG synthesis, history summarization, and memory fact extraction.
Includes automatic model failover / retry strategy for 429 Rate Limits and 503 Service Unavailable errors.
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

# Active free fallback models when 429 Rate Limit occurs
FALLBACK_ROSTER = [
    "inclusionai/ling-3.0-flash:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]


def _build_messages(query: str, context: str, history: list) -> list[dict]:
    """Format history, system prompt, context, long-term memory, and query for OpenRouter API."""
    system_text = SYSTEM_PROMPT

    # Extract long-term user memories from system messages in history
    memory_notes = []
    for msg in history:
        if hasattr(msg, "content") and getattr(msg, "type", "") == "system":
            memory_notes.append(msg.content)

    if memory_notes:
        system_text += "\n\n" + "\n".join(memory_notes) + "\n- Respect and apply all user personal preferences, tone instructions, and context."

    messages = [{"role": "system", "content": system_text}]

    for msg in history:
        if hasattr(msg, "content"):
            if getattr(msg, "type", "") == "system":
                continue
            role = "assistant" if getattr(msg, "type", "") in ("ai", "assistant") else "user"
            messages.append({"role": role, "content": msg.content})

    user_prompt = f"Context Documents:\n{context}\n\nQuestion: {query}" if context else query
    messages.append({"role": "user", "content": user_prompt})

    return messages


async def call_openrouter(query: str, context: str, history: list, model: str | None = None) -> str:
    """Async single-turn completion request to OpenRouter with automatic 429 failover."""
    api_key = settings.OPENROUTER_API_KEY.strip()
    if not api_key:
        logger.warning("OPENROUTER_API_KEY is missing or empty in .env")
        return (
            "⚠️ OPENROUTER_API_KEY is not configured. "
            "Please add your OpenRouter API key to backend/.env (OPENROUTER_API_KEY=sk-or-v1-...) to enable LLM generation."
        )

    target_model = model or settings.DEFAULT_MODEL
    messages = _build_messages(query, context, history)

    headers = {"Authorization": f"Bearer {api_key}"}
    if settings.APP_URL:
        headers["HTTP-Referer"] = settings.APP_URL

    models_to_try = [target_model] + [m for m in FALLBACK_ROSTER if m != target_model]

    async with httpx.AsyncClient() as client:
        for current_model in models_to_try:
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={
                        "model": current_model,
                        "messages": messages,
                    },
                    timeout=60.0,
                )
                if resp.status_code in (429, 503):
                    logger.warning(f"OpenRouter model '{current_model}' returned HTTP {resp.status_code} (Rate Limit). Trying fallback model...")
                    continue

                resp.raise_for_status()
                answer = resp.json()["choices"][0]["message"]["content"]
                logger.info(f"OpenRouter [{current_model}] generated response: {answer[:80]}...")
                return answer
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503):
                    logger.warning(f"OpenRouter model '{current_model}' rate limited ({e.response.status_code}). Trying next fallback model...")
                    continue
                logger.error(f"OpenRouter call error ({current_model}): {e}")
                return f"I encountered an issue calling OpenRouter ({current_model}): {str(e)}"
            except Exception as e:
                logger.error(f"OpenRouter call failed ({current_model}): {e}")
                return f"I encountered an issue calling OpenRouter ({current_model}): {str(e)}"

    return "⚠️ All free OpenRouter models are currently rate limited. Please wait 30 seconds and try again."


async def call_openrouter_summary(messages: list) -> str:
    """Summarize older conversation turns using the fast summary model."""
    api_key = settings.OPENROUTER_API_KEY.strip()
    if not api_key:
        return "Conversation history summary unavailable (missing API key)."

    conversation_text = "\n".join(
        f"{'User' if getattr(m, 'type', '') == 'human' else 'Assistant'}: {m.content}"
        for m in messages if hasattr(m, "content")
    )

    async with httpx.AsyncClient() as client:
        for model_name in [settings.SUMMARY_MODEL] + FALLBACK_ROSTER:
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                            {"role": "user", "content": conversation_text},
                        ],
                    },
                    timeout=30.0,
                )
                if resp.status_code in (429, 503):
                    continue
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception:
                continue

    return "Conversation history summary unavailable."


async def call_openrouter_extract_memory(messages: list) -> str | None:
    """Extract a durable long-term fact from conversation snippet using summary model."""
    api_key = settings.OPENROUTER_API_KEY.strip()
    if not api_key:
        return None

    conversation_text = "\n".join(
        f"{'User' if getattr(m, 'type', '') == 'human' else 'Assistant'}: {m.content}"
        for m in messages if hasattr(m, "content")
    )

    async with httpx.AsyncClient() as client:
        for model_name in [settings.SUMMARY_MODEL] + FALLBACK_ROSTER:
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                            {"role": "user", "content": conversation_text},
                        ],
                    },
                    timeout=30.0,
                )
                if resp.status_code in (429, 503):
                    continue
                resp.raise_for_status()
                extracted = resp.json()["choices"][0]["message"]["content"].strip()
                if extracted and extracted != "NOTHING_WORTH_REMEMBERING":
                    logger.info(f"Extracted durable memory fact: {extracted}")
                    return extracted
                return None
            except Exception:
                continue

    return None
