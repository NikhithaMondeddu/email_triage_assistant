"""Base email provider interface."""
from abc import ABC, abstractmethod
from typing import Optional

from src.models import EmailMessage, EmailThread


class EmailProvider(ABC):
    """Abstract provider for Gmail/Outlook."""

    @abstractmethod
    def list_threads(self, max_results: int = 50, query: Optional[str] = None) -> list[dict]:
        """List thread IDs and minimal metadata."""
        pass

    @abstractmethod
    def get_thread(self, thread_id: str) -> Optional[EmailThread]:
        """Fetch full thread with all messages."""
        pass

    @abstractmethod
    def get_message(self, message_id: str) -> Optional[EmailMessage]:
        """Fetch single message."""
        pass

    @abstractmethod
    def create_draft(self, to: list[str], subject: str, body: str, thread_id: Optional[str] = None) -> Optional[str]:
        """Create draft; returns draft ID."""
        pass

    @abstractmethod
    def list_labels(self) -> list[dict]:
        """List folders/labels."""
        pass

    @abstractmethod
    def apply_label(self, message_id: str, label_id: str) -> bool:
        """Apply label to message."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


def get_provider(provider: str, credentials: Optional[dict] = None) -> Optional[EmailProvider]:
    """Return provider instance by name."""
    if provider == "gmail":
        from .gmail_provider import GmailProvider
        return GmailProvider(credentials or {})
    if provider == "outlook":
        from .outlook_provider import OutlookProvider
        return OutlookProvider(credentials or {})
    return None
