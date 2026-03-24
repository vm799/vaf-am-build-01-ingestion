"""
VAF AM Build 01 — Gmail Ingester

Connects to Gmail via OAuth 2.0, fetches emails from a designated label/inbox,
extracts email bodies and PDF attachments, and routes them intelligently:

  - Email with PDF attachment   → 2 documents: email_body + email_attachment
  - Email without attachment    → 1 document:  email_body
  - Attachment is not PDF       → skipped (only PDFs are financially relevant)

Signal scoring (drives metadata.importance):
  - HIGH:   FCA/compliance/enforcement keywords, regulatory sender domains
  - HIGH:   Earnings / results / guidance keywords
  - MEDIUM: Market commentary, analyst research, fund updates
  - LOW:    Everything else

Source types produced:
  - "email"             — email body text
  - "email_attachment"  — PDF extracted from attachment
"""
import base64
import io
import re
from datetime import datetime

import pdfplumber
from googleapiclient.discovery import build

from .base import BaseIngester, RawDocument

# Keywords that lift importance to HIGH
HIGH_IMPORTANCE_SUBJECT = [
    "fca", "sec", "enforcement", "compliance", "violation", "alert", "urgent",
    "breach", "penalty", "fine", "regulatory", "notice", "supervisory",
    "earnings", "results", "guidance", "q1", "q2", "q3", "q4",
    "profit", "revenue", "acquisition", "merger", "insider",
]

HIGH_IMPORTANCE_SENDERS = [
    "fca.org.uk", "sec.gov", "bankofengland.co.uk", "esma.europa.eu",
    "pra.bankofengland.co.uk", "fsb.org",
]

MEDIUM_IMPORTANCE_SUBJECT = [
    "market", "fund", "portfolio", "analyst", "research", "briefing",
    "outlook", "forecast", "sector", "equity", "bond", "rate",
]


def _score_importance(subject: str, sender: str) -> str:
    subject_lower = subject.lower()
    sender_lower = sender.lower()

    if any(k in subject_lower for k in HIGH_IMPORTANCE_SUBJECT):
        return "high"
    if any(domain in sender_lower for domain in HIGH_IMPORTANCE_SENDERS):
        return "high"
    if any(k in subject_lower for k in MEDIUM_IMPORTANCE_SUBJECT):
        return "medium"
    return "low"


def _extract_email_body(payload: dict) -> str:
    """Recursively walk MIME parts to extract plain text body."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain" and body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

    # Walk multipart
    for part in payload.get("parts", []):
        result = _extract_email_body(part)
        if result:
            return result

    return ""


def _extract_pdf_attachments(service, message_id: str, payload: dict) -> list[tuple[str, bytes]]:
    """
    Returns list of (filename, pdf_bytes) for all PDF attachments in the message.
    Fetches attachment data from API when stored as attachment reference.
    """
    pdfs = []
    parts = payload.get("parts", [])

    for part in parts:
        filename = part.get("filename", "")
        mime_type = part.get("mimeType", "")

        if mime_type != "application/pdf" and not filename.lower().endswith(".pdf"):
            continue

        body = part.get("body", {})
        attachment_id = body.get("attachmentId")
        inline_data = body.get("data")

        if inline_data:
            pdfs.append((filename, base64.urlsafe_b64decode(inline_data)))
        elif attachment_id:
            attachment = (
                service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message_id, id=attachment_id)
                .execute()
            )
            pdf_bytes = base64.urlsafe_b64decode(attachment["data"])
            pdfs.append((filename, pdf_bytes))

    return pdfs


def _pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages).strip()


def _parse_date(date_str: str) -> datetime:
    """Parse Gmail date header to datetime (UTC). Falls back to now."""
    import email.utils
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.replace(tzinfo=None)  # store as naive UTC
    except Exception:
        return datetime.utcnow()


class GmailIngester(BaseIngester):
    """
    Fetches emails from Gmail and converts them to RawDocuments.

    Args:
        credentials: Authenticated google.oauth2.credentials.Credentials object
        label:       Gmail label to read (default "INBOX"). Use label ID or name.
        max_emails:  Maximum number of emails to fetch per run (default 10)
    """

    def __init__(self, credentials, label: str = "INBOX", max_emails: int = 10):
        self.credentials = credentials
        self.label = label
        self.max_emails = max_emails

    async def ingest(self) -> list[RawDocument]:
        # Note: Gmail API is synchronous, wrapped here for pipeline compatibility
        return self._fetch_emails()

    def _fetch_emails(self) -> list[RawDocument]:
        service = build("gmail", "v1", credentials=self.credentials)
        docs = []

        print(f"[Gmail] Fetching up to {self.max_emails} emails from label: {self.label}")

        results = (
            service.users()
            .messages()
            .list(userId="me", labelIds=[self.label], maxResults=self.max_emails)
            .execute()
        )

        messages = results.get("messages", [])
        if not messages:
            print("[Gmail] No messages found in label.")
            return docs

        for msg_ref in messages:
            try:
                docs.extend(self._process_message(service, msg_ref["id"]))
            except Exception as e:
                print(f"[Gmail WARN] Message {msg_ref['id']}: {e}")

        print(f"[Gmail ✓] Produced {len(docs)} document(s) from {len(messages)} email(s)")
        return docs

    def _process_message(self, service, message_id: str) -> list[RawDocument]:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )

        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

        subject = headers.get("Subject", "(no subject)")
        sender  = headers.get("From", "unknown")
        date_str = headers.get("Date", "")
        thread_id = msg.get("threadId", "")

        ingested_at = _parse_date(date_str)
        importance  = _score_importance(subject, sender)
        gmail_url   = f"https://mail.google.com/mail/u/0/#inbox/{message_id}"

        base_metadata = {
            "message_id": message_id,
            "thread_id":  thread_id,
            "sender":     sender,
            "subject":    subject,
            "date":       date_str,
            "label":      self.label,
            "importance": importance,
            "gmail_url":  gmail_url,
        }

        docs = []

        # --- Email body document ---
        body_text = _extract_email_body(payload).strip()
        if len(body_text) > 50:
            docs.append(RawDocument(
                source_type="email",
                source_url=gmail_url,
                title=subject,
                content=body_text,
                metadata={**base_metadata, "content_type": "email_body"},
                ingested_at=ingested_at,
            ))
            importance_tag = f"[{importance.upper()}]" if importance != "low" else ""
            print(f"[Gmail ✓] {importance_tag} Email body | {subject[:55]}")
        else:
            print(f"[Gmail] Skipping thin body ({len(body_text)} chars) | {subject[:55]}")

        # --- PDF attachments ---
        pdf_attachments = _extract_pdf_attachments(service, message_id, payload)
        for filename, pdf_bytes in pdf_attachments:
            try:
                pdf_text = _pdf_bytes_to_text(pdf_bytes)
                if len(pdf_text) < 20:
                    print(f"[Gmail WARN] Empty PDF: {filename}")
                    continue
                docs.append(RawDocument(
                    source_type="email_attachment",
                    source_url=gmail_url,
                    title=f"{filename} (from: {subject})",
                    content=pdf_text,
                    metadata={
                        **base_metadata,
                        "content_type": "pdf_attachment",
                        "attachment_filename": filename,
                        "attachment_size_bytes": len(pdf_bytes),
                    },
                    ingested_at=ingested_at,
                ))
                print(f"[Gmail ✓] PDF attachment | {filename} ({len(pdf_text)} chars)")
            except Exception as e:
                print(f"[Gmail WARN] PDF extraction failed for {filename}: {e}")

        return docs
