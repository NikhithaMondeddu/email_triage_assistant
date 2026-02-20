"""Microsoft Graph / Outlook API integration."""
import logging
from datetime import datetime
from typing import Optional

import requests

from src.models import EmailMessage, EmailThread

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class OutlookProvider:
    """Outlook via Microsoft Graph."""

    def __init__(self, credentials: dict):
        self._client_id = credentials.get("client_id") or credentials.get("AZURE_CLIENT_ID")
        self._client_secret = credentials.get("client_secret") or credentials.get("AZURE_CLIENT_SECRET")
        self._tenant_id = credentials.get("tenant_id") or credentials.get("AZURE_TENANT_ID")
        self._access_token = credentials.get("access_token")
        self._refresh_token = credentials.get("refresh_token")

    def _get_token(self) -> Optional[str]:
        if self._access_token:
            return self._access_token
        if not all([self._client_id, self._client_secret, self._tenant_id]):
            logger.warning("Outlook: missing client_id/client_secret/tenant_id")
            return None
        url = f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
        if self._refresh_token:
            data["grant_type"] = "refresh_token"
            data["refresh_token"] = self._refresh_token
        try:
            r = requests.post(url, data=data, timeout=10)
            r.raise_for_status()
            j = r.json()
            self._access_token = j.get("access_token")
            self._refresh_token = j.get("refresh_token") or self._refresh_token
            return self._access_token
        except Exception as e:
            logger.exception("Outlook token: %s", e)
            return None

    def _headers(self) -> dict:
        token = self._get_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if token else {}

    @property
    def name(self) -> str:
        return "outlook"

    def list_threads(self, max_results: int = 50, query: Optional[str] = None) -> list[dict]:
        # Graph uses conversations; we map each message's conversationId to a "thread"
        url = f"{GRAPH_BASE}/me/mailFolders/inbox/messages?$top={max_results}&$orderby=receivedDateTime desc"
        if query:
            escaped = query.replace("'", "''")
            url += f"&$filter=contains(subject,'{escaped}')"
        try:
            r = requests.get(url, headers=self._headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
            seen = set()
            threads = []
            for m in data.get("value", []):
                cid = m.get("conversationId") or m.get("id")
                if cid not in seen:
                    seen.add(cid)
                    threads.append({"id": cid, "provider": "outlook"})
            return threads[:max_results]
        except Exception as e:
            logger.exception("list_threads: %s", e)
            return []

    def get_thread(self, thread_id: str) -> Optional[EmailThread]:
        # Fetch messages in conversation
        url = f"{GRAPH_BASE}/me/messages?$filter=conversationId eq '{thread_id}'&$orderby=receivedDateTime asc"
        try:
            r = requests.get(url, headers=self._headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.exception("get_thread %s: %s", thread_id, e)
            return None
        msgs = []
        subject = ""
        for m in data.get("value", []):
            body = m.get("body", {})
            content = (body.get("content") or "") if body.get("contentType") == "text" else ""
            if body.get("contentType") == "html":
                content = (body.get("content") or "").replace("<br>", "\n")  # crude plain fallback
            sender = (m.get("from", {}).get("emailAddress", {}) or {})
            sender_str = sender.get("address", "")
            to_recips = [e.get("emailAddress", {}).get("address") for e in m.get("toRecipients", [])]
            to_list = [a for a in to_recips if a]
            received = m.get("receivedDateTime")
            try:
                date = datetime.fromisoformat(received.replace("Z", "+00:00")) if received else None
            except Exception:
                date = None
            subject = m.get("subject", "")
            msgs.append(EmailMessage(
                id=m["id"],
                thread_id=thread_id,
                sender=sender_str,
                to=to_list,
                subject=subject,
                body_plain=content[:50000],
                body_html=body.get("content") if body.get("contentType") == "html" else None,
                date=date,
                labels=[],  # Graph uses categories; could map
                is_read=m.get("isRead", False),
                has_attachments=m.get("hasAttachments", False),
                snippet=m.get("bodyPreview", ""),
            ))
        return EmailThread(id=thread_id, messages=msgs, subject=subject, provider="outlook")

    def get_message(self, message_id: str) -> Optional[EmailMessage]:
        url = f"{GRAPH_BASE}/me/messages/{message_id}"
        try:
            r = requests.get(url, headers=self._headers(), timeout=15)
            r.raise_for_status()
            m = r.json()
        except Exception:
            return None
        body = m.get("body", {})
        content = body.get("content") or ""
        sender = (m.get("from", {}).get("emailAddress", {}) or {}).get("address", "")
        to_list = [e.get("emailAddress", {}).get("address") for e in m.get("toRecipients", []) if e.get("emailAddress", {}).get("address")]
        received = m.get("receivedDateTime")
        try:
            date = datetime.fromisoformat(received.replace("Z", "+00:00")) if received else None
        except Exception:
            date = None
        return EmailMessage(
            id=m["id"],
            thread_id=m.get("conversationId", ""),
            sender=sender,
            to=to_list,
            subject=m.get("subject", ""),
            body_plain=content[:50000],
            body_html=content if (body.get("contentType") == "html") else None,
            date=date,
            labels=[],
            is_read=m.get("isRead", False),
            has_attachments=m.get("hasAttachments", False),
            snippet=m.get("bodyPreview", ""),
        )

    def create_draft(self, to: list[str], subject: str, body: str, thread_id: Optional[str] = None) -> Optional[str]:
        payload = {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": a}} for a in to],
        }
        if thread_id:
            payload["conversationId"] = thread_id
        try:
            r = requests.post(f"{GRAPH_BASE}/me/messages", headers=self._headers(), json=payload, timeout=15)
            r.raise_for_status()
            return r.json().get("id")
        except Exception as e:
            logger.exception("create_draft: %s", e)
            return None

    def list_labels(self) -> list[dict]:
        try:
            r = requests.get(f"{GRAPH_BASE}/me/mailFolders", headers=self._headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
            return [{"id": f["id"], "name": f["displayName"], "type": "folder"} for f in data.get("value", [])]
        except Exception as e:
            logger.exception("list_labels: %s", e)
            return []

    def apply_label(self, message_id: str, label_id: str) -> bool:
        # Graph: move to folder
        try:
            r = requests.post(
                f"{GRAPH_BASE}/me/messages/{message_id}/move",
                headers=self._headers(),
                json={"destinationId": label_id},
                timeout=15,
            )
            r.raise_for_status()
            return True
        except Exception as e:
            logger.exception("apply_label: %s", e)
            return False
