"""Productivity metrics: time saved, threads processed, drafts created, etc."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import config

logger = logging.getLogger(__name__)


class ProductivityMetrics:
    """Track and persist productivity metrics for the email assistant."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or config.METRICS_FILE
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = {"daily": {}, "totals": {}}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("metrics load: %s", e)

    def _save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.exception("metrics save: %s", e)

    def _today(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def record_threads_processed(self, count: int = 1) -> None:
        key = "threads_processed"
        self._data.setdefault("totals", {})[key] = self._data["totals"].get(key, 0) + count
        day = self._data.setdefault("daily", {}).setdefault(self._today(), {})
        day[key] = day.get(key, 0) + count
        self._save()

    def record_drafts_created(self, count: int = 1) -> None:
        key = "drafts_created"
        self._data.setdefault("totals", {})[key] = self._data["totals"].get(key, 0) + count
        day = self._data.setdefault("daily", {}).setdefault(self._today(), {})
        day[key] = day.get(key, 0) + count
        self._save()

    def record_scaledown_used(self, original_tokens: int, compressed_tokens: int) -> None:
        self._data.setdefault("totals", {})["scaledown_calls"] = self._data["totals"].get("scaledown_calls", 0) + 1
        self._data.setdefault("totals", {})["tokens_saved"] = self._data["totals"].get("tokens_saved", 0) + max(0, original_tokens - compressed_tokens)
        self._save()

    def record_triage_count(self, count: int = 1) -> None:
        key = "triage_count"
        self._data.setdefault("totals", {})[key] = self._data["totals"].get(key, 0) + count
        self._save()

    def get_totals(self) -> dict[str, Any]:
        return dict(self._data.get("totals", {}))

    def get_daily(self, date: Optional[str] = None) -> dict[str, Any]:
        date = date or self._today()
        return dict(self._data.get("daily", {}).get(date, {}))

    def estimate_time_saved_minutes(self) -> float:
        """Rough estimate: 60% reduction in email time (per spec). Assume 2 min/thread baseline."""
        threads = self._data.get("totals", {}).get("threads_processed", 0)
        baseline_min = threads * 2.0
        return baseline_min * 0.6  # 60% reduction
