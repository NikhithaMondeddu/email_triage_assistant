"""Triage agent: categorize threads with optional ScaleDown for long threads."""
import logging
import re
from typing import Optional

import config
from src.models import Category, EmailThread, TriageResult
from src.scaledown_client import compress_thread_if_long

logger = logging.getLogger(__name__)

# Patterns for categorization
NEWSLETTER_PATTERNS = [
    r"unsubscribe",
    r"view in browser",
    r"newsletter",
    r"you're receiving this because",
    r"manage preferences",
    r"mailchimp|sendgrid|constant contact",
]
PROMO_PATTERNS = [
    r"\d+% off",
    r"limited time",
    r"buy now",
    r"shop now",
    r"discount code",
    r"promo",
]
MEETING_PATTERNS = [
    r"meeting (invite|request|scheduled)",
    r"invitation:",
    r"when:.*\d{1,2}[\/\-]\d{1,2}",
    r"calendar",
    r"zoom\.us|teams\.microsoft|meet\.google",
    r"accept\.ics|invite\.ics",
]


class TriageAgent:
    """Categorize email threads; use ScaleDown for long threads."""

    def __init__(self, use_scaledown: bool = True):
        self.use_scaledown = use_scaledown and bool(config.SCALEDOWN_API_KEY)

    def triage(self, thread: EmailThread, priority_score: Optional[int] = None) -> TriageResult:
        """Run triage: optionally compress long thread, then categorize and suggest folder."""
        context = thread.to_context_string()
        compressed_context = None
        if self.use_scaledown and thread.message_count >= config.THREAD_SCALEDOWN_THRESHOLD:
            context_to_use, compressed_context = compress_thread_if_long(context, thread.message_count)
            if compressed_context:
                context = context_to_use
        category = self._categorize(context, thread)
        is_urgent = self._is_urgent(context, thread)
        if priority_score is None:
            from .priority_scorer import PriorityScorer
            priority_score = PriorityScorer().score(thread, category=category, is_urgent=is_urgent)
        folder = self._folder_for(category, is_urgent)
        summary = compressed_context[:500] if compressed_context else None
        return TriageResult(
            category=category,
            priority_score=priority_score,
            is_urgent=is_urgent,
            suggested_folder=folder,
            summary=summary,
            compressed_context=compressed_context,
        )

    def _categorize(self, text: str, thread: EmailThread) -> Category:
        combined = (text + " " + (thread.subject or "")).lower()
        for pat in MEETING_PATTERNS:
            if re.search(pat, combined, re.I):
                return Category.MEETING
        for pat in NEWSLETTER_PATTERNS:
            if re.search(pat, combined, re.I):
                return Category.NEWSLETTER
        for pat in PROMO_PATTERNS:
            if re.search(pat, combined, re.I):
                return Category.PROMOTION
        # Follow-up: thread has multiple messages, last from other
        if thread.message_count >= 2 and thread.messages:
            last = thread.messages[-1]
            # Heuristic: if last message has question-like content
            if "?" in (last.body_plain or "") or "?" in (last.snippet or ""):
                return Category.FOLLOW_UP
        return Category.OTHER

    def _is_urgent(self, text: str, thread: EmailThread) -> bool:
        combined = (text + " " + (thread.subject or "")).lower()
        for kw in config.URGENT_KEYWORDS:
            if kw in combined:
                return True
        for domain in config.URGENT_SENDER_DOMAINS:
            for m in thread.messages:
                if domain in (m.sender or "").lower():
                    return True
        return False

    def _folder_for(self, category: Category, is_urgent: bool) -> str:
        if is_urgent:
            return config.FOLDER_URGENT
        return {
            Category.URGENT: config.FOLDER_URGENT,
            Category.FOLLOW_UP: config.FOLDER_FOLLOW_UP,
            Category.MEETING: config.FOLDER_MEETINGS,
            Category.NEWSLETTER: config.FOLDER_NEWSLETTER,
            Category.PROMOTION: config.FOLDER_PROMO,
            Category.OTHER: config.FOLDER_OTHER,
        }.get(category, config.FOLDER_OTHER)
