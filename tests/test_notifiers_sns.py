"""Tests for the AWS SNS alert handler."""

from __future__ import annotations

import io
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.sns import SNSAlertHandler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_alert(
    level: AlertLevel = AlertLevel.WARNING,
    job_name: str = "backup",
    message: str = "Job is overdue",
) -> Alert:
    return Alert(
        level=level,
        job_name=job_name,
        message=message,
        timestamp=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def handler() -> SNSAlertHandler:
    return SNSAlertHandler(
        topic_arn="arn:aws:sns:us-east-1:123456789012:cronwatch",
        region="us-east-1",
        aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
        aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    )


@contextmanager
def mock_urlopen(status: int = 200):
    fake_resp = MagicMock()
    fake_resp.status = status
    fake_resp.read.return_value = b"<PublishResponse/>"
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.sns.urllib.request.urlopen", return_value=fake_resp) as m:
        yield m


# ---------------------------------------------------------------------------
# Construction validation
# ---------------------------------------------------------------------------


class TestSNSAlertHandler:
    def test_empty_topic_arn_raises(self):
        with pytest.raises(ValueError, match="topic_arn"):
            SNSAlertHandler(
                topic_arn="",
                region="us-east-1",
                aws_access_key_id="KEY",
                aws_secret_access_key="SECRET",
            )

    def test_empty_region_raises(self):
        with pytest.raises(ValueError, match="region"):
            SNSAlertHandler(
                topic_arn="arn:aws:sns:us-east-1:123:topic",
                region="",
                aws_access_key_id="KEY",
                aws_secret_access_key="SECRET",
            )

    def test_empty_access_key_raises(self):
        with pytest.raises(ValueError, match="aws_access_key_id"):
            SNSAlertHandler(
                topic_arn="arn:aws:sns:us-east-1:123:topic",
                region="us-east-1",
                aws_access_key_id="",
                aws_secret_access_key="SECRET",
            )

    def test_empty_secret_key_raises(self):
        with pytest.raises(ValueError, match="aws_secret_access_key"):
            SNSAlertHandler(
                topic_arn="arn:aws:sns:us-east-1:123:topic",
                region="us-east-1",
                aws_access_key_id="KEY",
                aws_secret_access_key="",
            )

    # -----------------------------------------------------------------------
    # send() behaviour
    # -----------------------------------------------------------------------

    def test_posts_to_correct_region_url(self, handler):
        with mock_urlopen() as m:
            handler.send(_make_alert())
        url = m.call_args[0][0].full_url
        assert "us-east-1" in url

    def test_payload_contains_topic_arn(self, handler):
        with mock_urlopen() as m:
            handler.send(_make_alert())
        body = m.call_args[0][0].data.decode()
        assert "arn%3Aaws%3Asns" in body or "TopicArn" in body

    def test_subject_contains_level_and_job_name(self, handler):
        with mock_urlopen() as m:
            handler.send(_make_alert(level=AlertLevel.CRITICAL, job_name="db-backup"))
        body = m.call_args[0][0].data.decode()
        assert "CRITICAL" in body
        assert "db-backup" in body

    def test_custom_subject_prefix(self):
        h = SNSAlertHandler(
            topic_arn="arn:aws:sns:eu-west-1:999:alerts",
            region="eu-west-1",
            aws_access_key_id="K",
            aws_secret_access_key="S",
            subject_prefix="[myapp]",
        )
        with mock_urlopen() as m:
            h.send(_make_alert())
        body = m.call_args[0][0].data.decode()
        assert "myapp" in body

    def test_non_200_response_raises(self, handler):
        with mock_urlopen(status=503):
            with pytest.raises(RuntimeError, match="503"):
                handler.send(_make_alert())
