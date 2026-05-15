"""Integration tests: loading a Linear notifier from TOML config."""
from __future__ import annotations

import os
import tempfile

import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.linear import LinearAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestLinearConfigParsing:
    def teardown_method(self):
        if hasattr(self, "_path") and os.path.exists(self._path):
            os.unlink(self._path)

    def _load(self, toml: str):
        self._path = _write_toml(toml)
        cfg = load_config(self._path)
        return cfg

    def test_linear_handler_loaded(self):
        cfg = self._load("""
[notifiers.linear]
type = "linear"
api_key = "lin_api_abc"
team_id = "TEAM-X"
""")
        assert "linear" in cfg["notifiers"]
        handler = cfg["notifiers"]["linear"]
        assert isinstance(handler, LinearAlertHandler)

    def test_linear_handler_with_optional_fields(self):
        cfg = self._load("""
[notifiers.linear]
type = "linear"
api_key = "lin_api_xyz"
team_id = "TEAM-Y"
label_id = "LBL-1"
assignee_id = "USR-7"
""")
        handler = cfg["notifiers"]["linear"]
        assert isinstance(handler, LinearAlertHandler)
        assert handler._label_id == "LBL-1"
        assert handler._assignee_id == "USR-7"

    def test_missing_api_key_raises(self):
        with pytest.raises(Exception):
            self._load("""
[notifiers.linear]
type = "linear"
team_id = "TEAM-Z"
""")

    def test_missing_team_id_raises(self):
        with pytest.raises(Exception):
            self._load("""
[notifiers.linear]
type = "linear"
api_key = "lin_api_nope"
""")
