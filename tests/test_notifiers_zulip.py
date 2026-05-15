"""Tests for the Zulip notifier."""

import json
import unittest
from unittest.mock import MagicMock, patch
from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.zulip import ZulipAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(job_name="nightly-backup", level=level, message="Job is overdue")


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> ZulipAlertHandler:
    return ZulipAlertHandler(
        site="https://myorg.zulipchat.com",
        email="bot@myorg.zulipchat.com",
        api_key="supersecret",
        stream="ops-alerts",
        topic="cronwatch",
    )


class TestZulipAlertHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = ZulipAlertHandler(
            site="https://myorg.zulipchat.com",
            email="bot@myorg.zulipchat.com",
            api_key="supersecret",
            stream="ops-alerts",
            topic="cronwatch",
        )

    def _mock_urlopen(self):
        fake_resp = MagicMock()
        fake_resp.status = 200
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        return patch("cronwatch.notifiers.zulip.urllib.request.urlopen", return_value=fake_resp)

    def test_empty_site_raises(self) -> None:
        with self.assertRaises(ValueError):
            ZulipAlertHandler(site="", email="a@b.com", api_key="k", stream="ops")

    def test_empty_email_raises(self) -> None:
        with self.assertRaises(ValueError):
            ZulipAlertHandler(site="https://z.com", email="", api_key="k", stream="ops")

    def test_empty_api_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            ZulipAlertHandler(site="https://z.com", email="a@b.com", api_key="", stream="ops")

    def test_empty_stream_raises(self) -> None:
        with self.assertRaises(ValueError):
            ZulipAlertHandler(site="https://z.com", email="a@b.com", api_key="k", stream="")

    def test_posts_to_correct_url(self) -> None:
        with self._mock_urlopen() as mock_open:
            self.handler.send(_make_alert())
            req = mock_open.call_args[0][0]
            self.assertIn("/api/v1/messages", req.full_url)

    def test_request_uses_post(self) -> None:
        with self._mock_urlopen() as mock_open:
            self.handler.send(_make_alert())
            req = mock_open.call_args[0][0]
            self.assertEqual(req.method, "POST")

    def test_authorization_header_present(self) -> None:
        with self._mock_urlopen() as mock_open:
            self.handler.send(_make_alert())
            req = mock_open.call_args[0][0]
            self.assertIn("Authorization", req.headers)
            self.assertTrue(req.headers["Authorization"].startswith("Basic "))

    def test_payload_contains_stream_and_topic(self) -> None:
        with self._mock_urlopen() as mock_open:
            self.handler.send(_make_alert())
            req = mock_open.call_args[0][0]
            body = req.data.decode()
            self.assertIn("ops-alerts", body)
            self.assertIn("cronwatch", body)

    def test_payload_contains_alert_message(self) -> None:
        alert = _make_alert(AlertLevel.CRITICAL)
        with self._mock_urlopen() as mock_open:
            self.handler.send(alert)
            req = mock_open.call_args[0][0]
            body = req.data.decode()
            self.assertIn("nightly-backup", body)

    def test_trailing_slash_stripped_from_site(self) -> None:
        h = ZulipAlertHandler(
            site="https://myorg.zulipchat.com/",
            email="bot@myorg.zulipchat.com",
            api_key="key",
            stream="ops",
        )
        with self._mock_urlopen() as mock_open:
            h.send(_make_alert())
            req = mock_open.call_args[0][0]
            self.assertNotIn("//api", req.full_url)
