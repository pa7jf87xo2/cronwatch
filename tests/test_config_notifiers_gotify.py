"""Integration tests: load Gotify notifier from TOML config."""
from __future__ import annotations

import os
import tempfile

import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.gotify import GotifyAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestGotifyConfigParsing:
    def teardown_method(self):
        for attr in ("_tmp_path",):
            path = getattr(self, attr, None)
            if path and os.path.exists(path):
                os.unlink(path)

    def _load(self, toml: str):
        self._tmp_path = _write_toml(toml)
        cfg = load_config(self._tmp_path)
        return cfg["notifiers"]

    def test_gotify_handler_loaded(self):
        notifiers = self._load(
            """
            [notifiers.push]
            type = "gotify"
            url = "http://gotify.local"
            token = "mytoken"
            """
        )
        assert isinstance(notifiers["push"], GotifyAlertHandler)

    def test_gotify_handler_custom_priority(self):
        notifiers = self._load(
            """
            [notifiers.push]
            type = "gotify"
            url = "http://gotify.local"
            token = "mytoken"
            priority = 7
            """
        )
        h = notifiers["push"]
        assert isinstance(h, GotifyAlertHandler)
        assert h._priority_override == 7

    def test_missing_url_raises(self):
        with pytest.raises(Exception):
            self._load(
                """
                [notifiers.push]
                type = "gotify"
                token = "mytoken"
                """
            )
