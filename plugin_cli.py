#!/usr/bin/env python3
"""
Email assistant plugin CLI: triage, smart folders, drafts, follow-ups, metrics.
Usage:
  python plugin_cli.py triage --provider gmail
  python plugin_cli.py folders --provider gmail --max 20
  python plugin_cli.py urgent --provider gmail
  python plugin_cli.py draft <thread_id> [--template acknowledge]
  python plugin_cli.py metrics
  python plugin_cli.py survey --rating 5 --comment "Great"
  python plugin_cli.py inbox-zero --unread 0 --inbox 0
"""
import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.assistant import EmailAssistant

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def cmd_triage(args):
    try:
        assistant = EmailAssistant(provider_name=args.provider, use_scaledown=bool(args.scaledown))
    except Exception as e:
        print(f"Provider init failed: {e}", file=sys.stderr)
        return 1
    threads = assistant.provider.list_threads(max_results=args.max)
    for t in threads[: args.max]:
        thread = assistant.provider.get_thread(t["id"])
        if not thread:
            continue
        triage = assistant.run_triage(thread)
        print(json.dumps({
            "thread_id": thread.id,
            "subject": (thread.subject or "")[:60],
            "category": triage.category.value,
            "priority": triage.priority_score,
            "urgent": triage.is_urgent,
            "folder": triage.suggested_folder,
        }, indent=2))
    return 0


def cmd_folders(args):
    assistant = EmailAssistant(provider_name=args.provider, use_scaledown=bool(args.scaledown))
    view = assistant.get_smart_folders_view(max_threads=args.max)
    out = {k: [{"id": th.id, "subject": th.subject[:50]} for th in v] for k, v in view.items()}
    print(json.dumps(out, indent=2))
    return 0


def cmd_urgent(args):
    assistant = EmailAssistant(provider_name=args.provider)
    items = assistant.get_urgent(max_threads=args.max)
    print(json.dumps(items, indent=2))
    return 0


def cmd_draft(args):
    assistant = EmailAssistant(provider_name=args.provider)
    provider = assistant.provider
    thread = provider.get_thread(args.thread_id)
    if not thread:
        print("Thread not found.", file=sys.stderr)
        return 1
    draft = assistant.suggest_draft(thread, template_id=args.template or None)
    print(draft.body)
    if args.create:
        to = [m.sender for m in thread.messages if m.sender][:1] or ["unknown@example.com"]
        did = assistant.create_draft(to=to, subject=f"Re: {thread.subject}", body=draft.body, thread_id=thread.id)
        print(f"Draft created: {did}", file=sys.stderr)
    return 0


def cmd_metrics(args):
    assistant = EmailAssistant(provider_name=args.provider or "gmail")
    print(json.dumps(assistant.get_metrics(), indent=2))
    return 0


def cmd_survey(args):
    assistant = EmailAssistant(provider_name=args.provider or "gmail")
    assistant.submit_survey(rating=args.rating, comment=args.comment, feature_used=args.feature)
    print("Survey submitted.")
    return 0


def cmd_inbox_zero(args):
    assistant = EmailAssistant(provider_name=args.provider or "gmail")
    assistant.record_inbox_check(unread_count=args.unread, inbox_count=args.inbox)
    rate = assistant.inbox_zero.achievement_rate()
    print(json.dumps({"inbox_zero_recorded": True, "achievement_rate_30d": rate}))
    return 0


def get_provider(name: str, creds: dict):
    from src.providers import get_provider as _gp
    return _gp(name, creds)


def _add_common_args(parser):
    """Add --provider, --max, --scaledown so they work after the subcommand."""
    parser.add_argument("--provider", default="gmail", choices=["gmail", "outlook"])
    parser.add_argument("--max", type=int, default=20)
    parser.add_argument("--scaledown", type=int, default=1, help="1=use ScaleDown for long threads")


def main():
    p = argparse.ArgumentParser(description="Email assistant plugin CLI")
    _add_common_args(p)  # so "plugin_cli.py --provider gmail --max 20 triage" works
    sub = p.add_subparsers(dest="command", required=True)

    t = sub.add_parser("triage")
    _add_common_args(t)
    t.set_defaults(func=cmd_triage)

    f = sub.add_parser("folders")
    _add_common_args(f)
    f.set_defaults(func=cmd_folders)

    u = sub.add_parser("urgent")
    _add_common_args(u)
    u.set_defaults(func=cmd_urgent)

    d = sub.add_parser("draft")
    d.add_argument("thread_id")
    d.add_argument("--template", default=None)
    d.add_argument("--create", action="store_true", help="Create draft in mailbox")
    _add_common_args(d)
    d.set_defaults(func=cmd_draft)

    m = sub.add_parser("metrics")
    _add_common_args(m)
    m.set_defaults(func=cmd_metrics)

    s = sub.add_parser("survey")
    s.add_argument("--rating", type=int, required=True)
    s.add_argument("--comment", default=None)
    s.add_argument("--feature", default=None)
    _add_common_args(s)
    s.set_defaults(func=cmd_survey)

    iz = sub.add_parser("inbox-zero")
    iz.add_argument("--unread", type=int, required=True)
    iz.add_argument("--inbox", type=int, required=True)
    _add_common_args(iz)
    iz.set_defaults(func=cmd_inbox_zero)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
