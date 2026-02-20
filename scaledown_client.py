"""
ScaleDown client: compress long email threads by ~85% for full inbox context.
https://docs.scaledown.ai/quickstart
"""
import json
import logging
from typing import Optional

import requests

import config

logger = logging.getLogger(__name__)


def compress_thread(context: str, prompt: str = "Summarize and preserve key facts, decisions, and action items.") -> Optional[str]:
    """
    Compress a long thread via ScaleDown API. Use for threads with 10+ messages.
    Returns compressed text or None if API unavailable.
    """
    if not config.SCALEDOWN_API_KEY:
        logger.warning("SCALEDOWN_API_KEY not set; skipping compression.")
        return None

    payload = {
        "context": context,
        "prompt": prompt,
        "scaledown": {"rate": config.SCALEDOWN_RATE},
    }
    headers = {
        "x-api-key": config.SCALEDOWN_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(
            config.SCALEDOWN_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("successful") and data.get("compressed_prompt"):
            logger.info(
                "ScaleDown: %s -> %s tokens",
                data.get("original_prompt_tokens"),
                data.get("compressed_prompt_tokens"),
            )
            return data["compressed_prompt"]
        return None
    except Exception as e:
        logger.exception("ScaleDown request failed: %s", e)
        return None


def compress_thread_if_long(thread_context: str, message_count: int) -> tuple[str, Optional[str]]:
    """
    If thread is long (>= THREAD_SCALEDOWN_THRESHOLD), compress it.
    Returns (context_to_use, compressed_version_or_None).
    """
    if message_count >= config.THREAD_SCALEDOWN_THRESHOLD:
        compressed = compress_thread(
            context=thread_context,
            prompt="Preserve: senders, key decisions, action items, deadlines, and main question. Remove greetings and redundancy.",
        )
        if compressed:
            return compressed, compressed
    return thread_context, None
