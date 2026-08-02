"""
Async LangChain ChatOpenAI client pointing to OpenRouter for RAG synthesis,
history summarization, memory fact extraction, and real-time token streaming.
Automatically traced in LangSmith with full fallback roster for 429/503 rate limits.
"""

from typing import AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
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

# Lightweight roster for auxiliary tasks (summary, memory extraction) to save rate limits
UTILITY_FALLBACK_ROSTER = [
    "inclusionai/ling-3.0-flash:free",
    "google/gemma-4-26b-a4b-it:free",
]


def _build_lc_messages(query: str, context: str, history: list) -> list:
    """Format history, system prompt, context, long-term memory, and query into LangChain Message objects."""
    system_text = SYSTEM_PROMPT

    memory_notes = []
    for msg in history:
        if hasattr(msg, "content") and getattr(msg, "type", "") == "system":
            memory_notes.append(msg.content)

    if memory_notes:
        system_text += "\n\n" + "\n".join(memory_notes) + "\n- Respect and apply all user personal preferences, tone instructions, and context."

    lc_messages = [SystemMessage(content=system_text)]

    for msg in history:
        if hasattr(msg, "content"):
            mtype = getattr(msg, "type", "")
            if mtype == "system":
                continue
            if mtype in ("ai", "assistant"):
                lc_messages.append(AIMessage(content=msg.content))
            else:
                lc_messages.append(HumanMessage(content=msg.content))

    user_prompt = f"Context Documents:\n{context}\n\nQuestion: {query}" if context else query
    lc_messages.append(HumanMessage(content=user_prompt))

    return lc_messages


def _get_chat_model(model_name: str) -> ChatOpenAI:
    """Construct LangChain ChatOpenAI instance pointing to OpenRouter API endpoint."""
    api_key = settings.OPENROUTER_API_KEY.strip()
    return ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.2,
        max_retries=1,
    )


async def call_openrouter(query: str, context: str, history: list, model: str | None = None) -> str:
    """Async single-turn completion using LangChain ChatOpenAI with automatic 429 failover."""
    api_key = settings.OPENROUTER_API_KEY.strip()
    if not api_key:
        logger.warning("OPENROUTER_API_KEY is missing or empty in .env")
        return (
            "⚠️ OPENROUTER_API_KEY is not configured. "
            "Please add your OpenRouter API key to backend/.env (OPENROUTER_API_KEY=sk-or-v1-...) to enable LLM generation."
        )

    target_model = model or settings.DEFAULT_MODEL
    lc_messages = _build_lc_messages(query, context, history)
    models_to_try = [target_model] + [m for m in FALLBACK_ROSTER if m != target_model]

    for current_model in models_to_try:
        try:
            llm = _get_chat_model(current_model)
            response = await llm.ainvoke(lc_messages)
            answer = response.content
            logger.info(f"LangChain ChatOpenAI [{current_model}] generated response: {answer[:80]}...")
            return answer
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "503" in err_str or "Rate limit" in err_str:
                logger.warning(f"LangChain model '{current_model}' rate limited. Trying next fallback model...")
                continue
            logger.error(f"LangChain call error ({current_model}): {e}")
            return f"I encountered an issue calling OpenRouter ({current_model}): {str(e)}"

    return "⚠️ All free OpenRouter models are currently rate limited. Please wait 30 seconds and try again."


async def stream_openrouter(query: str, context: str, history: list, model: str | None = None) -> AsyncGenerator[str, None]:
    """Async token-by-token generator using LangChain ChatOpenAI .astream()."""
    api_key = settings.OPENROUTER_API_KEY.strip()
    if not api_key:
        yield "⚠️ OPENROUTER_API_KEY is not configured in backend/.env"
        return

    target_model = model or settings.DEFAULT_MODEL
    lc_messages = _build_lc_messages(query, context, history)
    models_to_try = [target_model] + [m for m in FALLBACK_ROSTER if m != target_model]

    for current_model in models_to_try:
        try:
            llm = _get_chat_model(current_model)
            has_yielded = False
            async for chunk in llm.astream(lc_messages):
                if chunk.content:
                    has_yielded = True
                    yield chunk.content
            if has_yielded:
                return
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "503" in err_str or "Rate limit" in err_str:
                logger.warning(f"LangChain streaming model '{current_model}' rate limited. Trying fallback...")
                continue
            logger.error(f"LangChain streaming error ({current_model}): {e}")
            yield f"Error calling model ({current_model}): {str(e)}"
            return

    yield "⚠️ All free OpenRouter models are currently rate limited."


async def call_openrouter_summary(messages: list) -> str:
    """Summarize older conversation turns using LangChain ChatOpenAI."""
    api_key = settings.OPENROUTER_API_KEY.strip()
    if not api_key:
        return "Conversation history summary unavailable (missing API key)."

    conversation_text = "\n".join(
        f"{'User' if getattr(m, 'type', '') == 'human' else 'Assistant'}: {m.content}"
        for m in messages if hasattr(m, "content")
    )

    for model_name in [settings.SUMMARY_MODEL] + UTILITY_FALLBACK_ROSTER:
        try:
            llm = _get_chat_model(model_name)
            lc_messages = [
                SystemMessage(content=SUMMARY_SYSTEM_PROMPT),
                HumanMessage(content=conversation_text),
            ]
            response = await llm.ainvoke(lc_messages)
            return str(response.content)
        except Exception:
            continue

    return "Conversation history summary unavailable."


async def call_openrouter_extract_memory(messages: list) -> str | None:
    """Extract a durable long-term fact from conversation snippet using LangChain ChatOpenAI."""
    api_key = settings.OPENROUTER_API_KEY.strip()
    if not api_key:
        return None

    conversation_text = "\n".join(
        f"{'User' if getattr(m, 'type', '') == 'human' else 'Assistant'}: {m.content}"
        for m in messages if hasattr(m, "content")
    )

    for model_name in [settings.SUMMARY_MODEL] + UTILITY_FALLBACK_ROSTER:
        try:
            llm = _get_chat_model(model_name)
            lc_messages = [
                SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
                HumanMessage(content=conversation_text),
            ]
            response = await llm.ainvoke(lc_messages)
            extracted = str(response.content).strip()
            if extracted and extracted != "NOTHING_WORTH_REMEMBERING":
                logger.info(f"Extracted durable memory fact: {extracted}")
                return extracted
            return None
        except Exception:
            continue

    return None
