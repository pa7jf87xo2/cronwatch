"""Tests for the email alert notifier."""

from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.email import EmailAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        job_name="backup",
        level=level,
        message="Job is overdue by 5 minutes",
        checked_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def handler() -> EmailAlertHandler:
    return EmailAlertHandler(
        smtp_host="smtp.example.com",
        smtp_port=587,
        sender="cronwatch@example.com",
        recipients=["ops@example.com", "admin@example.com"],
        username="user",
        password="secret",
    )


class TestEmailAlertHandler:
    def test_send_connects_to_correct_host(self, handler: EmailAlertHandler) -> None:
        alert = _make_alert()
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server
            handler.send(alert)
        mock_smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=10)

    def test_send_uses_tls_by_default(self, handler: EmailAlertHandler) -> None:
        alert = _make_alert()
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server
            handler.send(alert)
        mock_server.starttls.assert_called_once()

    def test_send_skips_tls_when_disabled(self, handler: EmailAlertHandler) -> None:
        handler.use_tls = False
        alert = _make_alert()
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server
            handler.send(alert)
        mock_server.starttls.assert_not_called()

    def test_send_logs_in_with_credentials(self, handler: EmailAlertHandler) -> None:
        alert = _make_alert()
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server
            handler.send(alert)
        mock_server.login.assert_called_once_with("user", "secret")

    def test_send_omits_login_without_credentials(self) -> None:
        handler = EmailAlertHandler(
            smtp_host="smtp.example.com",
            smtp_port=25,
            sender="cronwatch@example.com",
            recipients=["ops@example.com"],
        )
        alert = _make_alert()
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value.__enter__.return_value = mock_server
            handler.send(alert)
        mock_server.login.assert_not_called()

    def test_send_subject_contains_level_and_job(self, handler: EmailAlertHandler) -> None:
        alert = _make_alert(AlertLevel.CRITICAL)
        captured: list[str] = []

        def capture_sendmail(sender, recipients, msg_str):
            captured.append(msg_str)

        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_server.sendmail.side_effect = capture_sendmail
            mock_smtp_cls.return_value.__enter__.return_value = mock_server
            handler.send(alert)

        assert len(captured) == 1
        assert "CRITICAL" in captured[0]
        assert "backup" in captured[0]

    def test_send_raises_on_smtp_error(self, handler: EmailAlertHandler) -> None:
        alert = _make_alert()
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_server.sendmail.side_effect = smtplib.SMTPException("connection refused")
            mock_smtp_cls.return_value.__enter__.return_value = mock_server
            with pytest.raises(smtplib.SMTPException):
                handler.send(alert)
