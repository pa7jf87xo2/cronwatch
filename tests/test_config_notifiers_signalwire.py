"""Tests for SignalWire notifier config parsing."""

from __future__ import annotations

import os
import tempfile

import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.signalwire import SignalWireAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestSignalWireConfigParsing:
    def teardown_method(self, _method):
        pass  # temp files cleaned up per-test

    def _load(self, toml: str):
        path = _write_toml(toml)
        try:
            return load_config(path)
        finally:
            os.unlink(path)

    def test_signalwire_handler_loaded(self):
        cfg = self._load(
            """
            [notifiers.sw]
            type = "signalwire"
            space_url = "myspace.signalwire.com"
            project_id = "proj-abc"
            api_token = "tok-xyz"
            from_number = "+15550001111"
            to_number = "+15559998888"
            """
        )
        handler = cfg["notifiers"]["sw"]
        assert isinstance(handler, SignalWireAlertHandler)

    def test_signalwire_space_url_set(self):
        cfg = self._load(
            """
            [notifiers.sw]
            type = "signalwire"
            space_url = "myspace.signalwire.com"
            project_id = "proj-abc"
            api_token = "tok-xyz"
            from_number = "+15550001111"
            to_number = "+15559998888"
            """
        )
        handler = cfg["notifiers"]["sw"]
        assert handler.space_url == "myspace.signalwire.com"

    def test_signalwire_numbers_set(self):
        cfg = self._load(
            """
            [notifiers.sw]
            type = "signalwire"
            space_url = "myspace.signalwire.com"
            project_id = "proj-abc"
            api_token = "tok-xyz"
            from_number = "+15550001111"
            to_number = "+15559998888"
            """
        )
        handler = cfg["notifiers"]["sw"]
        assert handler.from_number == "+15550001111"
        assert handler.to_number == "+15559998888"
