import logging
from typing import List

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, smtp_server: str = "smtp.example.com", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
    def send_digest(self, to_email: str, subject: str, html_content: str):
        """Sends an email digest. Mocks the actual SMTP sending for now."""
        logger.info(f"Sending email digest to {to_email}")
        logger.debug(f"Subject: {subject}")
        logger.debug(f"Content length: {len(html_content)}")
        
        # In a real app, this would use smtplib or an API like SendGrid
        # import smtplib
        # from email.mime.text import MIMEText
        # msg = MIMEText(html_content, "html")
        # msg["Subject"] = subject
        # msg["To"] = to_email
        # with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
        #     server.send_message(msg)
        
        return True

email_sender = EmailSender()
