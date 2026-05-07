"""Tests for Telegram notifier config parsing."""

import os
import tempfile
import unittest

from cronwatch.config import load_config
from cronwatch.notifiers.telegram import TelegramAlertHandler


def _write_toml(content: str) -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False
    )
    f.write(content)
    f.close()
    return f.name


class TestTelegramConfigParsing(unittest.TestCase):
    def teardown_method(self, method):
        pass

    def tearDown(self):
        pass

    def _load(self, toml: str):
        path = _write_toml(toml)
        try:
            return load_config(path)
        finally:
            os.unlink(path)

    def test_telegram_handler_loaded(self):
        cfg = self._load(
            """
[jobs.nightly]
schedule = "0 2 * * *"
warning_after = 60
critical_after = 120

[[notifiers]]
type = "telegram"
token = "bot-abc-123"
chat_id = "-100999"
"""
        )
        assert len(cfg.notifiers) == 1
        assert isinstance(cfg.notifiers[0], TelegramAlertHandler)

    def test_telegram_handler_custom_parse_mode(self):
        cfg = self._load(
            """
[jobs.nightly]
schedule = "0 2 * * *"
warning_after = 60
critical_after = 120

[[notifiers]]
type = "telegram"
token = "bot-abc-123"
chat_id = "-100999"
parse_mode = "HTML"
"""
        )
        handler = cfg.notifiers[0]
        assert isinstance(handler, TelegramAlertHandler)
        assert handler._parse_mode == "HTML"

    def test_missing_token_raises(self):
        with self.assertRaises(Exception):
            self._load(
                """
[jobs.nightly]
schedule = "0 2 * * *"
warning_after = 60
critical_after = 120

[[notifiers]]
type = "telegram"
chat_id = "-100999"
"""
            )
