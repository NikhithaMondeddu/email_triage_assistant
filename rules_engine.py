"""Custom rules engine: match conditions and run actions on threads/messages."""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from src.models import EmailMessage, EmailThread


class RuleCondition(str, Enum):
    FROM = "from"
    TO = "to"
    SUBJECT = "subject"
    BODY_CONTAINS = "body_contains"
    HAS_ATTACHMENT = "has_attachment"
    LABEL = "label"
    THREAD_COUNT = "thread_count"


class RuleAction(str, Enum):
    APPLY_LABEL = "apply_label"
    MARK_READ = "mark_read"
    ADD_FOLLOW_UP = "add_follow_up"
    SET_PRIORITY_BOOST = "set_priority_boost"
    SKIP = "skip"


@dataclass
class Rule:
    """Single rule: conditions (AND) -> action."""
    name: str
    conditions: list[tuple[RuleCondition, str]]  # (condition_type, pattern or value)
    action: RuleAction
    action_param: Optional[str] = None  # e.g. label_id for APPLY_LABEL
    enabled: bool = True


class RulesEngine:
    """Evaluate custom rules against threads/messages."""

    def __init__(self, rules: Optional[list[Rule]] = None):
        self.rules = rules or []

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def evaluate_thread(self, thread: EmailThread) -> list[tuple[Rule, dict]]:
        """Return list of (rule, action_params) that match. First match wins per rule."""
        results = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            params = self._match_rule(rule, thread)
            if params is not None:
                results.append((rule, params))
        return results

    def _match_rule(self, rule: Rule, thread: EmailThread) -> Optional[dict]:
        if not thread.messages:
            return None
        last = thread.messages[-1]
        for cond_type, pattern in rule.conditions:
            if not self._check_condition(cond_type, pattern, thread, last):
                return None
        return {"action_param": rule.action_param}

    def _check_condition(
        self,
        cond_type: RuleCondition,
        pattern: str,
        thread: EmailThread,
        message: EmailMessage,
    ) -> bool:
        if cond_type == RuleCondition.FROM:
            return re.search(pattern, message.sender or "", re.I) is not None
        if cond_type == RuleCondition.TO:
            return any(re.search(pattern, t or "", re.I) for t in message.to)
        if cond_type == RuleCondition.SUBJECT:
            return re.search(pattern, message.subject or "", re.I) is not None
        if cond_type == RuleCondition.BODY_CONTAINS:
            text = (message.body_plain or "") + (message.snippet or "")
            return pattern.lower() in text.lower()
        if cond_type == RuleCondition.HAS_ATTACHMENT:
            return message.has_attachments if pattern.lower() in ("true", "1", "yes") else not message.has_attachments
        if cond_type == RuleCondition.LABEL:
            return pattern in (message.labels or [])
        if cond_type == RuleCondition.THREAD_COUNT:
            try:
                n = int(pattern)
                return thread.message_count >= n
            except ValueError:
                return False
        return False
