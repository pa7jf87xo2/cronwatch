"""Integration tests: parse a Freshdesk notifier block from TOML config."""

from __future__ import annotations

import os
import tempfile

import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.freshdesk import FreshdeskAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestFreshdeskConfigParsing:
    def teardown_method(self):
        pass  # temp files cleaned up per-test

    def _load(self, toml: str):
        path = _write_toml(toml)
        try:
            return load_config(path)
        finally:
            os.unlink(path)

    def test_freshdesk_handler_loaded(self):
        cfg = self._load(
            """
[notifiers.fd]
type = "freshdesk"
domain = "acme.freshdesk.com"
api_key = "abc123"
email = "ops@acme.com"
"""
        )
        assert isinstance(cfg.notifiers["fd"], FreshdeskAlertHandler)

    def test_freshdesk_custom_tags(self):
        cfg = self._load(
            """
[notifiers.fd]
type = "freshdesk"
domain = "acme.freshdesk.com"
api_key = "abc123"
email = "ops@acme.com"
tags = ["infra", "cron"]
"""
        )
        handler = cfg.notifiers["fd"]
        assert isinstance(handler, FreshdeskAlertHandler)
        # tags stored internally
        assert handler._tags == ["infra", "cron"]

    def test_missing_domain_raises(self):
        with pytest.raises(Exception):
            self._load(
                """
[notifiers.fd]
type = "freshdesk"
api_key = "abc123"
email = "ops@acme.com"
"""
            )
