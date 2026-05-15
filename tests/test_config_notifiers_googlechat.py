"""Integration tests: loading a Google Chat notifier from TOML config."""

import os
import tempfile

import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.googlechat import GoogleChatAlertHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGoogleChatConfigParsing:
    def teardown_method(self, _method):
        if hasattr(self, "_cfg_path") and os.path.exists(self._cfg_path):
            os.unlink(self._cfg_path)

    def _load(self, toml: str):
        self._cfg_path = _write_toml(toml)
        _jobs, handlers = load_config(self._cfg_path)
        return handlers

    def test_googlechat_handler_loaded(self):
        handlers = self._load(
            """
[[notifier]]
type = "googlechat"
webhook_url = "https://chat.googleapis.com/v1/spaces/XYZ/messages?key=abc"
"""
        )
        assert len(handlers) == 1
        assert isinstance(handlers[0], GoogleChatAlertHandler)

    def test_googlechat_webhook_url_passed(self):
        handlers = self._load(
            """
[[notifier]]
type = "googlechat"
webhook_url = "https://chat.googleapis.com/v1/spaces/XYZ/messages?key=abc"
"""
        )
        assert handlers[0]._webhook_url == "https://chat.googleapis.com/v1/spaces/XYZ/messages?key=abc"

    def test_missing_webhook_url_raises(self):
        with pytest.raises((KeyError, ValueError)):
            self._load(
                """
[[notifier]]
type = "googlechat"
"""
            )
