"""Urgent detection: keywords, senders, deadlines."""
import re
from typing import Optional

import config
from src.models import EmailMessage, EmailThread


class UrgentDetector:
    """Detect urgent emails for triage and smart folders."""

    def __init__(
        self,
        keywords: Optional[list[str]] = None,
        sender_domains: Optional[list[str]] = None,
    ):
        self.keywords = keywords or config.URGENT_KEYWORDS
        self.sender_domains = sender_domains or config.URGENT_SENDER_DOMAINS

    def is_urgent(self, thread: EmailThread) -> bool:
        text = (thread.subject or "") + " "
        for m in thread.messages:
            text += (m.body_plain or "") + " " + (m.snippet or "")
        text = text.lower()
        for kw in self.keywords:
            if kw in text:
                return True
        for domain in self.sender_domains:
            for m in thread.messages:
                if domain in (m.sender or "").lower():
                    return True
        return False

    def urgency_reason(self, thread: EmailThread) -> Optional[str]:
        """Return short reason if urgent, else None."""
        text = (thread.subject or "").lower()
        for m in thread.messages:
            text += " " + (m.body_plain or "").lower() + " " + (m.snippet or "").lower()
        for kw in self.keywords:
            if kw in text:
                return f"Keyword: {kw}"
        for domain in self.sender_domains:
            for m in thread.messages:
                if domain in (m.sender or "").lower():
                    return f"Sender: {domain}"
        return None
