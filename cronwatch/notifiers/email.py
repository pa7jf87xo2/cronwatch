"""Email alert notifier for cronwatch."""

from __future__ import annotations

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from typing import List

from cronwatch.alerting import Alert, AlertHandler

logger = logging.getLogger(__name__)


@dataclass
class EmailAlertHandler(AlertHandler):
    """Sends alerts via SMTP email."""

    smtp_host: str
    smtp_port: int
    sender: str
    recipients: List[str]
    subject_prefix: str = "[cronwatch]"
    username: str = ""
    password: str = ""
    use_tls: bool = True
    _extra_fields: dict = field(default_factory=dict, init=False, repr=False)

    def send(self, alert: Alert) -> None:
        """Format and dispatch an email for the given alert."""
        subject = f"{self.subject_prefix} {alert.level.name}: {alert.job_name}"
        body = str(alert)

        msg = MIMEMultipart()
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.sender, self.recipients, msg.as_string())
            logger.info(
                "Email alert sent for job '%s' to %s",
                alert.job_name,
                self.recipients,
            )
        except smtplib.SMTPException as exc:
            logger.error("Failed to send email alert: %s", exc)
            raise
