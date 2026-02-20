"""Follow-up tracker: track threads that need a reply and remind."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import config
from src.models import EmailThread, TriageResult

logger = logging.getLogger(__name__)

FOLLOW_UPS_FILE = config.DATA_DIR / "follow_ups.json"


class FollowUpTracker:
    """Track threads needing reply; persist and query."""

    def __init__(self, store_path: Optional[Path] = None):
        self._path = store_path or FOLLOW_UPS_FILE
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._store: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._store = json.loads(self._path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("follow_up load: %s", e)
                self._store = []

    def _save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._store, indent=2), encoding="utf-8")
        except Exception as e:
            logger.exception("follow_up save: %s", e)

    def add(self, thread: EmailThread, triage_result: Optional[TriageResult] = None) -> None:
        """Mark thread as needing follow-up."""
        entry = {
            "thread_id": thread.id,
            "provider": thread.provider,
            "subject": thread.subject,
            "last_message_at": thread.messages[-1].date.isoformat() if thread.messages and thread.messages[-1].date else None,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "priority": triage_result.priority_score if triage_result else 50,
        }
        # Dedupe by thread_id
        self._store = [e for e in self._store if e.get("thread_id") != thread.id]
        self._store.append(entry)
        self._save()

    def remove(self, thread_id: str) -> bool:
        """Remove thread from follow-ups (e.g. after reply)."""
        before = len(self._store)
        self._store = [e for e in self._store if e.get("thread_id") != thread_id]
        if len(self._store) < before:
            self._save()
            return True
        return False

    def list_pending(self, min_priority: int = 0) -> list[dict]:
        """Return pending follow-ups, optionally above min_priority."""
        return [e for e in self._store if e.get("priority", 0) >= min_priority]

    def is_follow_up(self, thread_id: str) -> bool:
        return any(e.get("thread_id") == thread_id for e in self._store)
