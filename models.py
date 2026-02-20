"""Data models for emails, threads, and agent outputs."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Category(str, Enum):
    URGENT = "urgent"
    FOLLOW_UP = "follow_up"
    MEETING = "meeting"
    NEWSLETTER = "newsletter"
    PROMOTION = "promotion"
    OTHER = "other"


@dataclass
class EmailMessage:
    """Single email message."""
    id: str
    thread_id: str
    sender: str
    to: list[str]
    subject: str
    body_plain: str
    body_html: Optional[str] = None
    date: Optional[datetime] = None
    labels: list[str] = field(default_factory=list)
    is_read: bool = False
    has_attachments: bool = False
    snippet: Optional[str] = None


@dataclass
class EmailThread:
    """Thread of messages (can be 50+). Use ScaleDown for long threads."""
    id: str
    messages: list[EmailMessage]
    subject: str
    provider: str  # "gmail" | "outlook"

    @property
    def message_count(self) -> int:
        return len(self.messages)

    def to_context_string(self, max_messages: Optional[int] = None) -> str:
        """Serialize thread for compression or LLM context."""
        msgs = self.messages[:max_messages] if max_messages else self.messages
        parts = []
        for m in msgs:
            parts.append(
                f"From: {m.sender}\nDate: {m.date}\nSubject: {m.subject}\n\n{m.body_plain or m.snippet or ''}"
            )
        return "\n---\n".join(parts)


@dataclass
class TriageResult:
    """Output of triage agent."""
    category: Category
    priority_score: int  # 0-100
    is_urgent: bool
    suggested_folder: str
    summary: Optional[str] = None
    compressed_context: Optional[str] = None  # after ScaleDown


@dataclass
class MeetingInfo:
    """Extracted meeting details."""
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    location: Optional[str] = None
    title: Optional[str] = None
    raw_dates: list[str] = field(default_factory=list)


@dataclass
class DraftSuggestion:
    """Generated draft."""
    body: str
    subject: Optional[str] = None
    template_id: Optional[str] = None


@dataclass
class UnsubscribeSuggestion:
    """Suggestion to unsubscribe."""
    reason: str
    confidence: float
    link_candidates: list[str] = field(default_factory=list)
