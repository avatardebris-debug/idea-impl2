"""Email tool for AutomatedClientOps Manager.

Handles composing and sending emails for client communication,
file delivery, and invoice notifications.
"""

from __future__ import annotations

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class EmailMessage:
    """Represents an email to be sent.

    Attributes:
        to: Recipient email address(es).
        subject: Email subject line.
        body: Plain-text body of the email.
        html_body: Optional HTML body.
        attachments: List of file paths to attach.
        cc: CC email address(es).
        bcc: BCC email address(es).
    """

    to: str
    subject: str
    body: str
    html_body: Optional[str] = None
    attachments: list[str] = field(default_factory=list)
    cc: Optional[str] = None
    bcc: Optional[str] = None

    def build_mime(self) -> MIMEMultipart:
        """Build a MIMEMultipart message from this EmailMessage."""
        msg = MIMEMultipart("mixed")
        msg["From"] = ""  # Set by sender
        msg["To"] = self.to
        msg["Subject"] = self.subject
        if self.cc:
            msg["Cc"] = self.cc
        if self.bcc:
            msg["Bcc"] = self.bcc

        # Attach body
        if self.html_body:
            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(self.body, "plain"))
            alt.attach(MIMEText(self.html_body, "html"))
            msg.attach(alt)
        else:
            msg.attach(MIMEText(self.body, "plain"))

        # Attach files
        for filepath in self.attachments:
            with open(filepath, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)  # mutates part in place
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filepath.split('/')[-1]}",
            )
            msg.attach(part)

        return msg


class EmailSender:
    """Handles sending emails via SMTP.

    Attributes:
        smtp_server: SMTP server hostname.
        smtp_port: SMTP server port.
        sender_email: The sender's email address.
        sender_password: The sender's email password/app password.
        use_tls: Whether to use TLS.
    """

    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: str = "",
        sender_password: str = "",
        use_tls: bool = True,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls

    def send(self, message: EmailMessage) -> bool:
        """Send an email message.

        Args:
            message: The EmailMessage to send.

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.sender_email or not self.sender_password:
            raise ValueError("sender_email and sender_password must be set")

        msg = message.build_mime()
        msg["From"] = self.sender_email

        recipients = [message.to]
        if message.cc:
            recipients.append(message.cc)
        if message.bcc:
            recipients.append(message.bcc)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                if self.use_tls:
                    server.starttls(context=context)
                    server.ehlo()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, msg.as_string())
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to send email: {e}")

    def compose_invoice_email(
        self,
        client_email: str,
        invoice_id: str,
        total: float,
        attachments: Optional[list[str]] = None,
    ) -> EmailMessage:
        """Compose an invoice notification email.

        Args:
            client_email: Client's email address.
            invoice_id: Invoice identifier.
            total: Invoice total amount.
            attachments: Optional list of file paths to attach.

        Returns:
            A composed EmailMessage.
        """
        attachments = attachments or []
        body = (
            f"Dear Client,\n\n"
            f"Your invoice #{invoice_id} is ready for review.\n\n"
            f"Total Amount: ${total:.2f}\n\n"
            f"Please find the invoice attached. If you have any questions,\n"
            f"feel free to reach out.\n\n"
            f"Best regards,\n"
            f"AutomatedClientOps Manager"
        )
        return EmailMessage(
            to=client_email,
            subject=f"Invoice #{invoice_id} — ${total:.2f}",
            body=body,
            attachments=attachments,
        )

    def compose_file_delivery_email(
        self,
        client_email: str,
        project_name: str,
        attachments: list[str],
    ) -> EmailMessage:
        """Compose a file delivery email.

        Args:
            client_email: Client's email address.
            project_name: Name of the project/deliverable.
            attachments: List of file paths to attach.

        Returns:
            A composed EmailMessage.
        """
        file_names = [a.split("/")[-1] for a in attachments]
        body = (
            f"Dear Client,\n\n"
            f"Your deliverable for '{project_name}' is ready!\n\n"
            f"Attached files:\n" + "\n".join(f"  - {fn}" for fn in file_names) + "\n\n"
            f"Please review and let us know if you need any revisions.\n\n"
            f"Best regards,\n"
            f"AutomatedClientOps Manager"
        )
        return EmailMessage(
            to=client_email,
            subject=f"Deliverable Ready: {project_name}",
            body=body,
            attachments=attachments,
        )
