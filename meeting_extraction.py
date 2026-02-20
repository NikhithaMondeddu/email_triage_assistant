"""Meeting extraction: parse dates, times, locations from threads."""
import re
from datetime import datetime
from typing import Optional

from src.models import EmailMessage, EmailThread, MeetingInfo


class MeetingExtractor:
    """Extract meeting details from email content."""

    # Common patterns
    WHEN_PATTERN = re.compile(
        r"(?:when|time|date|at)\s*:?\s*([^\n]+?(?:\d{1,2}[\/\-]\d{1,2}[\/\-]?\d{2,4}|\d{1,2}:\d{2}\s*(?:am|pm)?))",
        re.I,
    )
    LOCATION_PATTERN = re.compile(
        r"(?:where|location|place|room)\s*:?\s*([^\n]+)",
        re.I,
    )
    ZOOM_TEAMS = re.compile(
        r"(https?://(?:zoom\.us|teams\.microsoft\.com|meet\.google\.com)[^\s]+)",
        re.I,
    )
    DATE_LIKE = re.compile(
        r"(\d{1,2})[\/\-](\d{1,2})[\/\-]?(\d{2,4})?",
    )
    TIME_LIKE = re.compile(
        r"(\d{1,2}):(\d{2})\s*(am|pm)?",
        re.I,
    )

    def extract(self, thread: EmailThread) -> MeetingInfo:
        """Extract meeting info from thread (prefer last message)."""
        info = MeetingInfo()
        text = (thread.subject or "") + "\n"
        for m in thread.messages:
            text += (m.body_plain or "") + "\n" + (m.snippet or "") + "\n"
        # Links
        links = self.ZOOM_TEAMS.findall(text)
        if links:
            info.location = links[0]
        # Location line
        loc = self.LOCATION_PATTERN.search(text)
        if loc and not info.location:
            info.location = loc.group(1).strip()[:200]
        # Raw date-like strings
        raw = self.DATE_LIKE.findall(text)
        info.raw_dates = [f"{m}/{d}/{y or ''}" for m, d, y in raw[:5]]
        info.title = thread.subject
        return info
