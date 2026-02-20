"""
Email assistant plugin: single entrypoint for triage, priority, drafts,
follow-up, ScaleDown, rules, smart folders, urgent detection, templates,
meeting extraction, unsubscribe suggestions, metrics, surveys, inbox zero.
"""
import logging
from typing import Any, Optional

from src.agents import DraftGenerator, FollowUpTracker, PriorityScorer, TriageAgent
from src.deliverables import InboxZeroTracker, ProductivityMetrics, SatisfactionSurveys
from src.engines import RulesEngine
from src.features import MeetingExtractor, SmartFolders, UnsubscribeSuggestions, UrgentDetector
from src.models import EmailThread, TriageResult
from src.providers import get_provider

logger = logging.getLogger(__name__)


class EmailAssistant:
    """Main email management agent plugin."""

    def __init__(
        self,
        provider_name: str = "gmail",
        credentials: Optional[dict] = None,
        use_scaledown: bool = True,
    ):
        self.provider = get_provider(provider_name, credentials)
        if not self.provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        self.triage_agent = TriageAgent(use_scaledown=use_scaledown)
        self.priority_scorer = PriorityScorer()
        self.draft_generator = DraftGenerator()
        self.follow_up_tracker = FollowUpTracker()
        self.rules_engine = RulesEngine()
        self.smart_folders = SmartFolders()
        self.urgent_detector = UrgentDetector()
        self.meeting_extractor = MeetingExtractor()
        self.unsubscribe_suggestions = UnsubscribeSuggestions()
        self.metrics = ProductivityMetrics()
        self.surveys = SatisfactionSurveys()
        self.inbox_zero = InboxZeroTracker()

    def run_triage(self, thread: EmailThread) -> TriageResult:
        """Triage a thread (with ScaleDown for long threads); record metrics."""
        result = self.triage_agent.triage(thread)
        self.metrics.record_triage_count(1)
        self.metrics.record_threads_processed(1)
        if result.compressed_context:
            self.metrics.record_scaledown_used(1000, 150)  # placeholder; real from API
        return result

    def get_priority(self, thread: EmailThread, triage_result: Optional[TriageResult] = None) -> int:
        if triage_result is None:
            triage_result = self.run_triage(thread)
        return self.priority_scorer.score(thread, triage_result=triage_result)

    def suggest_draft(self, thread: EmailThread, template_id: Optional[str] = None) -> Any:
        triage = self.run_triage(thread)
        draft = self.draft_generator.generate(
            thread,
            template_id=template_id,
            context_summary=triage.compressed_context or (triage.summary or ""),
        )
        self.metrics.record_drafts_created(1)
        return draft

    def add_follow_up(self, thread: EmailThread) -> None:
        triage = self.run_triage(thread)
        self.follow_up_tracker.add(thread, triage)

    def get_smart_folders_view(self, max_threads: int = 50) -> dict[str, list[dict]]:
        """Fetch inbox threads, triage each, return grouped by smart folder."""
        threads_list = self.provider.list_threads(max_results=max_threads)
        threads_with_triage = []
        for t in threads_list:
            thread = self.provider.get_thread(t["id"])
            if thread:
                triage = self.run_triage(thread)
                threads_with_triage.append((thread, triage))
        return self.smart_folders.filter_into_folders(threads_with_triage)

    def get_urgent(self, max_threads: int = 50) -> list[dict]:
        """Return threads detected as urgent."""
        threads_list = self.provider.list_threads(max_results=max_threads)
        out = []
        for t in threads_list:
            thread = self.provider.get_thread(t["id"])
            if thread and self.urgent_detector.is_urgent(thread):
                reason = self.urgent_detector.urgency_reason(thread)
                out.append({"thread_id": thread.id, "subject": thread.subject, "reason": reason})
        return out

    def extract_meeting(self, thread: EmailThread) -> Any:
        return self.meeting_extractor.extract(thread)

    def suggest_unsubscribe(self, thread: EmailThread) -> Optional[Any]:
        return self.unsubscribe_suggestions.suggest(thread)

    def apply_rules(self, thread: EmailThread) -> list[tuple[Any, dict]]:
        return self.rules_engine.evaluate_thread(thread)

    def create_draft(self, to: list[str], subject: str, body: str, thread_id: Optional[str] = None) -> Optional[str]:
        return self.provider.create_draft(to=to, subject=subject, body=body, thread_id=thread_id)

    def record_inbox_check(self, unread_count: int, inbox_count: int) -> None:
        self.inbox_zero.record_check(unread_count, inbox_count)

    def submit_survey(self, rating: int, comment: Optional[str] = None, feature_used: Optional[str] = None) -> None:
        self.surveys.submit(rating=rating, comment=comment, feature_used=feature_used)

    def get_metrics(self) -> dict:
        return {
            "productivity": self.metrics.get_totals(),
            "time_saved_estimate_min": self.metrics.estimate_time_saved_minutes(),
            "satisfaction_avg": self.surveys.average_rating(),
            "inbox_zero_rate": self.inbox_zero.achievement_rate(),
            "inbox_zero_events": self.inbox_zero.total_inbox_zero_events(),
        }
