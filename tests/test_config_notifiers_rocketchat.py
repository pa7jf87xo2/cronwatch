"""Integration tests: parse Rocket.Chat notifier from TOML config."""

from __future__ import annotations

import os
import tempfile

import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.rocketchat import RocketChatAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestRocketChatConfigParsing:
    def teardown_method(self):
        for attr in ("_path",):
            path = getattr(self, attr, None)
            if path and os.path.exists(path):
                os.unlink(path)

    def _load(self, toml: str):
        self._path = _write_toml(toml)
        _, notifiers = load_config(self._path)
        return notifiers

    def test_rocketchat_handler_loaded(self):
        notifiers = self._load(
            """
            [[notifiers]]
            type = "rocketchat"
            webhook_url = "https://rc.example.com/hooks/xyz"
            """
        )
        assert len(notifiers) == 1
        assert isinstance(notifiers[0], RocketChatAlertHandler)

    def test_rocketchat_custom_username(self):
        notifiers = self._load(
            """
            [[notifiers]]
            type = "rocketchat"
            webhook_url = "https://rc.example.com/hooks/xyz"
            username = "alertbot"
            """
        )
        handler = notifiers[0]
        assert isinstance(handler, RocketChatAlertHandler)
        assert handler._username == "alertbot"

    def test_rocketchat_missing_webhook_raises(self):
        with pytest.raises((KeyError, ValueError)):
            self._load(
                """
                [[notifiers]]
                type = "rocketchat"
                """
            )
