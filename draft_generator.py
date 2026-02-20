"""Draft generator: template-based and context-aware reply drafts."""
import re
from typing import Optional

from src.models import DraftSuggestion, EmailThread


class DraftGenerator:
    """Generate reply drafts from templates and thread context."""

    def __init__(self, templates: Optional[dict[str, str]] = None):
        self.templates = templates or self._default_templates()

    def _default_templates(self) -> dict[str, str]:
        return {
            "acknowledge": "Thanks for your message. I'll look into this and get back to you soon.\n\nBest,\n",
            "short_yes": "Yes, that works for me. Thanks!\n\n",
            "short_no": "Unfortunately I won't be able to do that. Let me know if there's an alternative.\n\n",
            "meeting_accept": "I'll be there. Thanks for scheduling.\n\n",
            "meeting_decline": "I can't make that time. Could we find another slot?\n\n",
            "follow_up": "Following up on this. Could you let me know when you have an update?\n\n",
            "out_of_office": "I'm currently out of office with limited access to email. I'll respond when I'm back.\n\n",
        }

    def generate(
        self,
        thread: EmailThread,
        template_id: Optional[str] = None,
        context_summary: Optional[str] = None,
    ) -> DraftSuggestion:
        """Produce a draft; use template_id or pick from context."""
        if not thread.messages:
            return DraftSuggestion(body="", template_id=None)
        last = thread.messages[-1]
        body = ""
        tid = template_id
        if not tid and context_summary:
            tid = self._infer_template(context_summary, last.body_plain or "")
        if tid and tid in self.templates:
            body = self.templates[tid]
        else:
            body = self.templates["acknowledge"]
            tid = "acknowledge"
        # Personalize: add greeting from sender name
        name = self._extract_name(last.sender or "")
        if name:
            body = f"Hi {name},\n\n" + body
        else:
            body = "Hi,\n\n" + body
        return DraftSuggestion(body=body, subject=None, template_id=tid)

    def _extract_name(self, sender: str) -> str:
        # "Name <email>" or "email"
        match = re.match(r"^([^<]+)<", sender)
        if match:
            return match.group(1).strip().strip('"')
        if "@" in sender:
            return sender.split("@")[0].replace(".", " ").title()
        return sender or ""

    def _infer_template(self, summary: str, body: str) -> str:
        text = (summary + " " + body).lower()
        if "meeting" in text or "invite" in text or "schedule" in text:
            return "meeting_accept"
        if "?" in body or "follow up" in text:
            return "follow_up"
        return "acknowledge"

    def add_template(self, template_id: str, body: str) -> None:
        self.templates[template_id] = body
