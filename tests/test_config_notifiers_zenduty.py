"""Integration tests: load Zenduty notifier from TOML config."""
from __future__ import annotations

import os
import tempfile

import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.zenduty import ZendutyAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestZendutyConfigParsing:
    def teardown_method(self):
        for attr in ("_path",):
            path = getattr(self, attr, None)
            if path and os.path.exists(path):
                os.unlink(path)

    def _load(self, toml: str):
        self._path = _write_toml(toml)
        _, handlers = load_config(self._path)
        return handlers

    def test_zenduty_handler_loaded(self):
        handlers = self._load(
            """
            [[jobs]]
            name = "ping"
            schedule = "* * * * *"
            timeout_minutes = 5

            [[notifiers]]
            type = "zenduty"
            integration_key = "abc123"
            """
        )
        assert len(handlers) == 1
        assert isinstance(handlers[0], ZendutyAlertHandler)

    def test_zenduty_custom_timeout(self):
        handlers = self._load(
            """
            [[jobs]]
            name = "ping"
            schedule = "* * * * *"
            timeout_minutes = 5

            [[notifiers]]
            type = "zenduty"
            integration_key = "mykey"
            timeout = 20
            """
        )
        assert handlers[0]._timeout == 20

    def test_missing_integration_key_raises(self):
        with pytest.raises((KeyError, ValueError)):
            self._load(
                """
                [[jobs]]
                name = "ping"
                schedule = "* * * * *"
                timeout_minutes = 5

                [[notifiers]]
                type = "zenduty"
                """
            )
