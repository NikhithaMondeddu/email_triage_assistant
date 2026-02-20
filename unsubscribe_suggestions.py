"""Unsubscribe suggestions: detect marketing/newsletters and suggest unsubscribing."""
import re
from typing import Optional

from src.models import EmailThread, UnsubscribeSuggestion

# Patterns that indicate bulk/marketing mail
UNSUB_PATTERNS = [
    re.compile(r"unsubscribe\s*(?:here|link|below)?\s*[:\s]*(https?://[^\s<>\"']+)", re.I),
    re.compile(r"href\s*=\s*[\"'](https?://[^\"']*unsubscribe[^\"']*)[\"']", re.I),
    re.compile(r"(https?://[^\s<>\"']*unsubscribe[^\s<>\"']*)", re.I),
]
BULK_INDICATORS = [
    "unsubscribe",
    "manage preferences",
    "email preferences",
    "you're receiving this because",
    "view in browser",
    "mailchimp",
    "sendgrid",
    "constant contact",
    "newsletter",
]


class UnsubscribeSuggestions:
    """Suggest unsubscribing for likely marketing/newsletters."""

    def suggest(self, thread: EmailThread) -> Optional[UnsubscribeSuggestion]:
        """Return suggestion if thread looks like bulk/marketing."""
        text = (thread.subject or "") + "\n"
        for m in thread.messages:
            text += (m.body_plain or "") + "\n" + (m.body_html or "") + "\n"
        confidence = 0.0
        link_candidates = []
        for pat in UNSUB_PATTERNS:
            for m in pat.finditer(text):
                link_candidates.append(m.group(1).strip())
                confidence = min(1.0, confidence + 0.4)
        for ind in BULK_INDICATORS:
            if ind in text.lower():
                confidence = min(1.0, confidence + 0.2)
        link_candidates = list(dict.fromkeys(link_candidates))[:5]
        if confidence < 0.3:
            return None
        return UnsubscribeSuggestion(
            reason="Likely newsletter or marketing; unsubscribe link detected.",
            confidence=confidence,
            link_candidates=link_candidates,
        )
