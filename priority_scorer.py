"""Priority scorer: 0-100 score for inbox ordering and triage."""
from typing import Optional

from src.models import Category, EmailThread, TriageResult


class PriorityScorer:
    """Score threads by urgency, category, and engagement signals."""

    def score(
        self,
        thread: EmailThread,
        category: Optional[Category] = None,
        is_urgent: Optional[bool] = None,
        triage_result: Optional[TriageResult] = None,
    ) -> int:
        """Return 0-100; higher = more important."""
        if triage_result:
            category = triage_result.category
            is_urgent = triage_result.is_urgent
        base = 50
        # Urgent boost
        if is_urgent:
            base += 35
        elif category == Category.FOLLOW_UP:
            base += 25
        elif category == Category.MEETING:
            base += 15
        elif category in (Category.NEWSLETTER, Category.PROMOTION):
            base -= 30
        # Recency: newer = slight boost (by last message)
        if thread.messages:
            from datetime import datetime, timezone
            last = thread.messages[-1]
            if last.date:
                then = last.date if last.date.tzinfo else last.date.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                age_hours = (now - then).total_seconds() / 3600
                if age_hours < 1:
                    base += 10
                elif age_hours < 24:
                    base += 5
        return max(0, min(100, base))
