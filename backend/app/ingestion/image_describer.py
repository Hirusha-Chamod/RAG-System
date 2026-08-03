"""
Vision LLM image description generator with SHA256 caching, size filtering, and 429 rate limit fallbacks.

- Filters out images smaller than 3KB (logos, bullet points, UI icons) to save rate limits.
- Checks SHA256 image_cache before issuing API calls to OpenRouter.
- Uses LangChain ChatOpenAI with automatic 429 failover roster and LangSmith tracing.
"""

import base64
import hashlib
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.config import settings
from app.ingestion.image_cache import get_cached_description, cache_description
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Skip images smaller than 3KB (bullet points, small icons, tiny header logos)
MIN_IMAGE_BYTES = 3000

IMAGE_PROMPT = (
    "Describe this image factually in 1-3 sentences, focusing on any text, "
    "charts, diagrams, tables, or key data it contains for a search index."
)

VISION_FALLBACK_ROSTER = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "inclusionai/ling-3.0-flash:free",
]


async def describe_image(image_bytes: bytes) -> str | None:
    """Send raw image bytes to Vision LLM using LangChain ChatOpenAI. Returns description string or None."""
    if len(image_bytes) < MIN_IMAGE_BYTES:
        logger.debug(f"Skipping tiny image ({len(image_bytes)} bytes < {MIN_IMAGE_BYTES} threshold)")
        return None

    # Check SHA256 hash cache
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    if (cached := get_cached_description(image_hash)) is not None:
        return cached

    api_key = settings.OPENROUTER_API_KEY.strip()
    if not api_key:
        logger.warning("OPENROUTER_API_KEY missing for image description")
        return None

    # Prepare base64 image string
    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    models_to_try = [settings.VISION_LLM_MODEL] + [m for m in VISION_FALLBACK_ROSTER if m != settings.VISION_LLM_MODEL]

    for current_model in models_to_try:
        try:
            llm = ChatOpenAI(
                model=current_model,
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.2,
                max_retries=1,
            )

            msg = HumanMessage(
                content=[
                    {"type": "text", "text": IMAGE_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_data}"},
                    },
                ]
            )

            response = await llm.ainvoke([msg])
            description = str(response.content).strip()

            logger.info(f"Generated Vision description via LangChain [{current_model}] ({len(description)} chars): {description[:60]}...")
            # Save to SQLite hash cache
            cache_description(image_hash, description)
            return description

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "503" in err_str or "Rate limit" in err_str:
                logger.warning(f"Vision model '{current_model}' rate limited. Trying next fallback model...")
                continue
            logger.error(f"Vision description call failed ({current_model}): {e}")
            return None

    return None
