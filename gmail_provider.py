"""Gmail API integration."""
import base64
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config
from src.models import EmailMessage, EmailThread

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.compose", "https://www.googleapis.com/auth/gmail.modify"]


def _decode_body(payload: dict) -> tuple[Optional[str], Optional[str]]:
    plain, html = None, None
    if "body" in payload and payload["body"].get("data"):
        data = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        if payload.get("mimeType", "").lower() == "text/html":
            html = data
        else:
            plain = data
    for part in payload.get("parts", []):
        if plain and html:
            break
        mime = part.get("mimeType", "").lower()
        if part.get("body", {}).get("data"):
            data = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            if mime == "text/plain":
                plain = data
            elif mime == "text/html":
                html = data
    return plain or "", html


def _parse_date(header: Optional[str]) -> Optional[datetime]:
    if not header:
        return None
    try:
        return parsedate_to_datetime(header)
    except Exception:
        return None


class GmailProvider:
    """Gmail API provider."""

    def __init__(self, credentials: dict, token_path: Optional[str] = None, credentials_path: Optional[str] = None):
        token_path = token_path or str(config.DATA_DIR / "gmail_token.json")
        credentials_path = credentials_path or str(config.DATA_DIR / "credentials.json")
        self._credentials = credentials
        self._token_path = token_path
        self._credentials_path = credentials_path
        self._service = None
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _get_service(self):
        if self._service is not None:
            return self._service
        creds = None
        try:
            from pathlib import Path
            import json
            p = Path(self._token_path)
            if p.exists():
                creds = Credentials.from_authorized_user_info(json.loads(p.read_text()), SCOPES)
        except Exception as e:
            logger.debug("No token: %s", e)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                from pathlib import Path
                path = Path(self._credentials_path)
                if not path.exists():
                    raise FileNotFoundError(
                        f"OAuth credentials not found at {path}. Download from Google Cloud Console and save as credentials.json in data/."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(path), SCOPES)
                creds = flow.run_local_server(port=0)
            Path(self._token_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self._token_path).write_text(json.dumps({
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
            }))
        self._service = build("gmail", "v1", credentials=creds)
        return self._service

    @property
    def name(self) -> str:
        return "gmail"

    def list_threads(self, max_results: int = 50, query: Optional[str] = None) -> list[dict]:
        service = self._get_service()
        params = {"userId": "me", "maxResults": max_results}
        if query:
            params["q"] = query
        resp = service.users().threads().list(**params).execute()
        threads = resp.get("threads", [])
        return [{"id": t["id"], "provider": "gmail"} for t in threads]

    def get_thread(self, thread_id: str) -> Optional[EmailThread]:
        service = self._get_service()
        try:
            t = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
        except Exception as e:
            logger.exception("get_thread %s: %s", thread_id, e)
            return None
        msgs = []
        subject = ""
        for m in t.get("messages", []):
            payload = m.get("payload", {})
            headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
            plain, html = _decode_body(payload)
            subject = headers.get("subject", "")
            date = _parse_date(headers.get("date"))
            label_ids = m.get("labelIds", [])
            msgs.append(EmailMessage(
                id=m["id"],
                thread_id=thread_id,
                sender=headers.get("from", ""),
                to=[h for k, h in [("to", headers.get("to"))] if h] + (headers.get("to", "").split(",") if headers.get("to") else []),
                subject=subject,
                body_plain=plain or "",
                body_html=html,
                date=date,
                labels=label_ids,
                is_read="UNREAD" not in label_ids,
                has_attachments=any(p.get("filename") for p in payload.get("parts", [])),
                snippet=m.get("snippet"),
            ))
        msgs.sort(key=lambda x: x.date or datetime.min)
        return EmailThread(id=thread_id, messages=msgs, subject=subject, provider="gmail")

    def get_message(self, message_id: str) -> Optional[EmailMessage]:
        service = self._get_service()
        try:
            m = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        except Exception:
            return None
        payload = m.get("payload", {})
        headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
        plain, html = _decode_body(payload)
        return EmailMessage(
            id=m["id"],
            thread_id=m.get("threadId", ""),
            sender=headers.get("from", ""),
            to=(headers.get("to") or "").split(","),
            subject=headers.get("subject", ""),
            body_plain=plain or "",
            body_html=html,
            date=_parse_date(headers.get("date")),
            labels=m.get("labelIds", []),
            is_read="UNREAD" not in m.get("labelIds", []),
            has_attachments=any(p.get("filename") for p in payload.get("parts", [])),
            snippet=m.get("snippet"),
        )

    def create_draft(self, to: list[str], subject: str, body: str, thread_id: Optional[str] = None) -> Optional[str]:
        from email.mime.text import MIMEText
        import base64
        msg = MIMEText(body, "plain", "utf-8")
        msg["to"] = ", ".join(to)
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        draft = {"message": {"raw": raw, "threadId": thread_id} if thread_id else {"raw": raw}}
        try:
            service = self._get_service()
            r = service.users().drafts().create(userId="me", body=draft).execute()
            return r.get("id")
        except Exception as e:
            logger.exception("create_draft: %s", e)
            return None

    def list_labels(self) -> list[dict]:
        try:
            service = self._get_service()
            r = service.users().labels().list(userId="me").execute()
            return [{"id": l["id"], "name": l["name"], "type": l.get("type", "user")} for l in r.get("labels", [])]
        except Exception as e:
            logger.exception("list_labels: %s", e)
            return []

    def apply_label(self, message_id: str, label_id: str) -> bool:
        try:
            service = self._get_service()
            service.users().messages().modify(userId="me", id=message_id, body={"addLabelIds": [label_id]}).execute()
            return True
        except Exception as e:
            logger.exception("apply_label: %s", e)
            return False
