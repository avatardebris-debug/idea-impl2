"""Ticket ingestion layer — normalizes tickets from multiple input formats."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from email import message_from_string
from email.header import decode_header
from typing import Any, Dict, Optional, Union

from supportagent.models import Ticket, TicketSource


class IngestorError(Exception):
    """Raised when ingestion fails."""


class Ingestor:
    """Normalizes incoming tickets from ≥3 formats into a unified Ticket."""

    # ---------- JSON ----------

    @staticmethod
    def from_json(
        payload: Union[str, Dict[str, Any]],
        ticket_id: Optional[str] = None,
    ) -> Ticket:
        """Parse a raw JSON payload (string or dict) into a Ticket.

        Expected JSON keys (all optional except ticket_id):
            ticket_id, subject, body, sender, sender_email, customer_name,
            channel, priority, custom_field_*, etc.
        """
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload

        # Extract common fields with flexible key names
        subject = (
            data.get("subject")
            or data.get("Subject")
            or data.get("title")
            or data.get("subject_line")
            or ""
        )
        body = (
            data.get("body")
            or data.get("message")
            or data.get("description")
            or data.get("text")
            or ""
        )
        sender = data.get("sender") or data.get("sender_email") or data.get("from") or ""
        customer_name = data.get("customer_name") or data.get("name") or ""

        metadata: Dict[str, Any] = {}
        for k, v in data.items():
            if k not in ("ticket_id", "subject", "body", "sender", "sender_email",
                         "from", "customer_name", "name", "channel", "priority"):
                metadata[k] = v
        if sender:
            metadata["sender"] = sender
        if customer_name:
            metadata["customer_name"] = customer_name

        tid = ticket_id or data.get("ticket_id") or str(uuid.uuid4())

        return Ticket(
            ticket_id=tid,
            source=TicketSource.JSON,
            subject=str(subject),
            body=str(body),
            metadata=metadata,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    # ---------- MIME / Email ----------

    @staticmethod
    def from_mime(
        mime_string: str,
        ticket_id: Optional[str] = None,
    ) -> Ticket:
        """Parse an email MIME string into a Ticket.

        Extracts Subject, From, Date, and body (text/plain preferred).
        """
        msg = message_from_string(mime_string)

        # Subject
        raw_subject = msg.get("Subject", "")
        subject = ""
        if raw_subject:
            parts = decode_header(raw_subject)
            decoded_parts = []
            for part, charset in parts:
                if isinstance(part, bytes):
                    decoded_parts.append(part.decode(charset or "utf-8", errors="replace"))
                else:
                    decoded_parts.append(part)
            subject = " ".join(decoded_parts)

        # From / sender
        from_header = msg.get("From", "")
        sender = from_header

        # Body — prefer text/plain
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode(charset, errors="replace")
                        break
        else:
            charset = msg.get_content_charset() or "utf-8"
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(charset, errors="replace")

        # Date
        date_str = msg.get("Date", "")

        metadata: Dict[str, Any] = {}
        if from_header:
            metadata["sender"] = from_header
        if date_str:
            metadata["date"] = date_str
        # Preserve all headers as metadata
        for h in ["To", "Cc", "Reply-To", "Message-ID", "X-Priority"]:
            val = msg.get(h)
            if val:
                metadata[h] = val

        tid = ticket_id or str(uuid.uuid4())

        return Ticket(
            ticket_id=tid,
            source=TicketSource.EMAIL,
            subject=subject or "(no subject)",
            body=body or "(no body)",
            metadata=metadata,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    # ---------- Web form (URL-encoded) ----------

    @staticmethod
    def from_webform(
        payload: Union[str, Dict[str, str]],
        ticket_id: Optional[str] = None,
    ) -> Ticket:
        """Parse a web form URL-encoded payload into a Ticket.

        Expected form fields: ticket_id, subject, body, name, email, phone, etc.
        Accepts either a URL-encoded string or a dict.
        """
        if isinstance(payload, str):
            # URL-decode
            data: Dict[str, str] = {}
            for part in payload.split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    from urllib.parse import unquote_plus
                    data[unquote_plus(k)] = unquote_plus(v)
        else:
            data = dict(payload)

        subject = data.get("subject") or data.get("Subject") or data.get("title") or ""
        body = data.get("body") or data.get("body_text") or data.get("description") or ""
        customer_name = data.get("name") or data.get("customer_name") or ""
        sender_email = data.get("email") or data.get("email_address") or ""

        metadata: Dict[str, Any] = {}
        for k, v in data.items():
            if k not in ("ticket_id", "subject", "body", "name", "customer_name", "email", "email_address"):
                metadata[k] = v
        if customer_name:
            metadata["customer_name"] = customer_name
        if sender_email:
            metadata["sender_email"] = sender_email

        tid = ticket_id or data.get("ticket_id") or str(uuid.uuid4())

        return Ticket(
            ticket_id=tid,
            source=TicketSource.WEB,
            subject=subject or "(no subject)",
            body=body or "(no body)",
            metadata=metadata,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
