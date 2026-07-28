"""
Vision LLM image description generator with SHA256 caching and size filtering.

- Filters out images smaller than 3KB (logos, bullet points, UI icons) to save rate limits.
- Checks SHA256 image_cache before issuing API calls to OpenRouter.
- Uses vision-capable LLM (e.g. nvidia/nemotron-nano-12b-v2-vl:free).
"""

import base64
import hashlib
import httpx
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


async def describe_image(image_bytes: bytes) -> str | None:
    """Send raw image bytes to Vision LLM. Returns description string or None."""
    if len(image_bytes) < MIN_IMAGE_BYTES:
        logger.debug(f"Skipping tiny image ({len(image_bytes)} bytes < {MIN_IMAGE_BYTES} threshold)")
        return None

    # Check SHA256 hash cache
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    if (cached := get_cached_description(image_hash)) is not None:
        return cached

    # Prepare base64 image string
    b64_data = base64.b64encode(image_bytes).decode("utf-8")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
                json={
                    "model": settings.VISION_LLM_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": IMAGE_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{b64_data}"},
                                },
                            ],
                        }
                    ],
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            description = resp.json()["choices"][0]["message"]["content"].strip()

        logger.info(f"Generated Vision description ({len(description)} chars): {description[:60]}...")
        # Save to SQLite hash cache
        cache_description(image_hash, description)
        return description

    except Exception as e:
        logger.error(f"Vision description call failed: {e}")
        return None
