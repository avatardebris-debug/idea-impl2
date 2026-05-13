"""Alert configuration and dispatching for the monitoring system."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger("forensic.alerts")


@dataclass
class AlertConfig:
    """Configuration for alert dispatching.

    Supports multiple channels (email, slack, webhook, console).
    """

    # Email
    email_enabled: bool = False
    email_to: List[str] = field(default_factory=list)
    email_from: str = "forensic-suite@alerts.local"
    smtp_host: str = "localhost"
    smtp_port: int = 587

    # Slack
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = "#fraud-alerts"

    # Webhook
    webhook_enabled: bool = False
    webhook_url: str = ""
    webhook_headers: dict = field(default_factory=dict)

    # Console (always available for debugging)
    console_enabled: bool = True

    def to_dict(self) -> dict:
        """Return config as a dict (excluding sensitive fields)."""
        return {
            "email_enabled": self.email_enabled,
            "email_to": self.email_to,
            "slack_enabled": self.slack_enabled,
            "slack_channel": self.slack_channel,
            "webhook_enabled": self.webhook_enabled,
            "console_enabled": self.console_enabled,
        }


class AlertDispatcher:
    """Dispatches alerts via configured channels."""

    def __init__(self, config: AlertConfig):
        self.config = config

    def dispatch(
        self,
        ticker: str,
        score: float,
        risk_level: str,
        flags: List[str],
    ) -> None:
        """Dispatch an alert via all enabled channels.

        Args:
            ticker: Company ticker symbol.
            score: Fraud risk score (0-100).
            risk_level: Risk level string (low/medium/high/critical).
            flags: List of red flag descriptions.
        """
        message = self._format_message(ticker, score, risk_level, flags)

        if self.config.console_enabled:
            self._dispatch_console(message)

        if self.config.email_enabled:
            self._dispatch_email(ticker, score, risk_level, flags)

        if self.config.slack_enabled:
            self._dispatch_slack(ticker, score, risk_level, flags)

        if self.config.webhook_enabled:
            self._dispatch_webhook(ticker, score, risk_level, flags)

    def _format_message(
        self, ticker: str, score: float, risk_level: str, flags: List[str]
    ) -> str:
        """Format alert message for display."""
        lines = [
            f"🚨 Forensic Alert: {ticker}",
            f"   Fraud Score: {score:.1f}/100",
            f"   Risk Level: {risk_level.upper()}",
            f"   Red Flags ({len(flags)}):",
        ]
        for flag in flags[:5]:  # Limit to first 5 flags
            lines.append(f"      - {flag}")
        if len(flags) > 5:
            lines.append(f"      ... and {len(flags) - 5} more")
        return "\n".join(lines)

    def _dispatch_console(self, message: str) -> None:
        """Dispatch alert to console."""
        logger.warning("ALERT:\n%s", message)

    def _dispatch_email(
        self, ticker: str, score: float, risk_level: str, flags: List[str]
    ) -> None:
        """Dispatch alert via email."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            subject = f"[Forensic Alert] {ticker} - Score: {score:.1f} ({risk_level.upper()})"

            body = f"""Forensic Alert

Ticker: {ticker}
Fraud Score: {score:.1f}/100
Risk Level: {risk_level.upper()}

Red Flags:
"""
            for flag in flags:
                body += f"  - {flag}\n"

            msg = MIMEMultipart()
            msg["From"] = self.config.email_from
            msg["To"] = ", ".join(self.config.email_to)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                # Note: authentication would go here in production
                server.sendmail(self.config.email_from, self.config.email_to, msg.as_string())

            logger.info("Email alert sent to %s", ", ".join(self.config.email_to))
        except Exception as e:
            logger.error("Failed to send email alert: %s", e)

    def _dispatch_slack(
        self, ticker: str, score: float, risk_level: str, flags: List[str]
    ) -> None:
        """Dispatch alert via Slack webhook."""
        try:
            import requests

            color = {
                "low": "#36a64f",
                "medium": "#ffcc00",
                "high": "#ff6600",
                "critical": "#ff0000",
            }.get(risk_level, "#36a64f")

            payload = {
                "channel": self.config.slack_channel,
                "attachments": [
                    {
                        "color": color,
                        "title": f"Forensic Alert: {ticker}",
                        "fields": [
                            {"title": "Fraud Score", "value": f"{score:.1f}/100", "short": True},
                            {"title": "Risk Level", "value": risk_level.upper(), "short": True},
                        ],
                        "footer": "Forensic Suite",
                    }
                ],
            }

            response = requests.post(
                self.config.slack_webhook_url,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Slack alert sent to %s", self.config.slack_channel)
        except Exception as e:
            logger.error("Failed to send Slack alert: %s", e)

    def _dispatch_webhook(
        self, ticker: str, score: float, risk_level: str, flags: List[str]
    ) -> None:
        """Dispatch alert via generic webhook."""
        try:
            import requests

            payload = {
                "ticker": ticker,
                "score": score,
                "risk_level": risk_level,
                "flags": flags,
            }

            response = requests.post(
                self.config.webhook_url,
                json=payload,
                headers=self.config.webhook_headers,
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Webhook alert sent to %s", self.config.webhook_url)
        except Exception as e:
            logger.error("Failed to send webhook alert: %s", e)
