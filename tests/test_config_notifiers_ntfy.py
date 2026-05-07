"""Integration tests: ntfy handler loaded from TOML config."""

from __future__ import annotations

import os
import tempfile

import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.ntfy import NtfyAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestNtfyConfigParsing:
    def teardown_method(self):
        if hasattr(self, "_path") and os.path.exists(self._path):
            os.unlink(self._path)

    def _load(self, toml: str):
        self._path = _write_toml(toml)
        _, handlers = load_config(self._path)
        return handlers

    def test_ntfy_handler_loaded(self):
        handlers = self._load(
            """
[[notifier]]
type = "ntfy"
topic = "cronwatch"
"""
        )
        assert len(handlers) == 1
        assert isinstance(handlers[0], NtfyAlertHandler)

    def test_ntfy_topic_set(self):
        handlers = self._load(
            """
[[notifier]]
type = "ntfy"
topic = "my-topic"
"""
        )
        assert handlers[0].topic == "my-topic"

    def test_ntfy_custom_server(self):
        handlers = self._load(
            """
[[notifier]]
type = "ntfy"
topic = "alerts"
server = "https://ntfy.example.com"
"""
        )
        assert handlers[0].server == "https://ntfy.example.com"

    def test_ntfy_token_optional(self):
        handlers = self._load(
            """
[[notifier]]
type = "ntfy"
topic = "alerts"
token = "tok_abc"
"""
        )
        assert handlers[0].token == "tok_abc"

    def test_ntfy_missing_topic_raises(self):
        with pytest.raises(Exception):
            self._load(
                """
[[notifier]]
type = "ntfy"
"""
            )
