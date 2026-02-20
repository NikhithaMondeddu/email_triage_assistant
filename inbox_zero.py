"""Inbox zero achievement rate: track when inbox reaches zero."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import config

logger = logging.getLogger(__name__)


class InboxZeroTracker:
    """Track inbox zero events and compute achievement rate."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or config.INBOX_ZERO_FILE
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict = {"events": [], "checks": []}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("inbox_zero load: %s", e)

    def _save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.exception("inbox_zero save: %s", e)

    def record_check(self, unread_count: int, inbox_count: int) -> None:
        """Record an inbox check (unread and total in inbox)."""
        self._data.setdefault("checks", []).append({
            "at": datetime.now(timezone.utc).isoformat(),
            "unread_count": unread_count,
            "inbox_count": inbox_count,
            "inbox_zero": inbox_count == 0,
        })
        if inbox_count == 0:
            self._data.setdefault("events", []).append({
                "at": datetime.now(timezone.utc).isoformat(),
                "inbox_zero": True,
            })
        self._save()

    def achievement_rate(self, last_n_days: Optional[int] = 30) -> Optional[float]:
        """
        Fraction of check days where inbox zero was achieved at least once.
        If last_n_days given, only consider checks in that window.
        """
        checks = self._data.get("checks", [])
        if not checks:
            return None
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=last_n_days)).isoformat()
        day_hits = set()
        for c in checks:
            at = c.get("at", "")
            if at < cutoff:
                continue
            day = at[:10]
            if c.get("inbox_zero"):
                day_hits.add(day)
        days_checked = set(c.get("at", "")[:10] for c in checks if c.get("at", "") >= cutoff)
        if not days_checked:
            return None
        return len(day_hits) / len(days_checked) if days_checked else 0.0

    def total_inbox_zero_events(self) -> int:
        return len(self._data.get("events", []))
