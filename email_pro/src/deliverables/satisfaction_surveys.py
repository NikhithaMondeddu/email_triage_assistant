"""User satisfaction surveys: collect and store feedback."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import config

logger = logging.getLogger(__name__)


class SatisfactionSurveys:
    """Store and aggregate satisfaction survey responses."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or config.SURVEYS_FILE
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._responses: list[dict] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._responses = data.get("responses", [])
            except Exception as e:
                logger.warning("surveys load: %s", e)

    def _save(self) -> None:
        try:
            self._path.write_text(
                json.dumps({"updated": datetime.now(timezone.utc).isoformat(), "responses": self._responses}, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.exception("surveys save: %s", e)

    def submit(
        self,
        rating: int,
        comment: Optional[str] = None,
        feature_used: Optional[str] = None,
    ) -> None:
        """Submit a survey (rating 1-5, optional comment and feature)."""
        entry = {
            "rating": max(1, min(5, rating)),
            "comment": comment,
            "feature_used": feature_used,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self._responses.append(entry)
        self._save()

    def average_rating(self) -> Optional[float]:
        if not self._responses:
            return None
        return sum(r["rating"] for r in self._responses) / len(self._responses)

    def list_recent(self, limit: int = 20) -> list[dict]:
        return list(reversed(self._responses[-limit:]))
