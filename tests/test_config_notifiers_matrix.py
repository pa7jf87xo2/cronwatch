"""Integration tests: load a Matrix notifier from a TOML config file."""

from __future__ import annotations

import os
import tempfile

import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.matrix import MatrixAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestMatrixConfigParsing:
    def teardown_method(self):
        if hasattr(self, "_path") and os.path.exists(self._path):
            os.unlink(self._path)

    def _load(self, toml: str):
        self._path = _write_toml(toml)
        cfg = load_config(self._path)
        return cfg

    def test_matrix_handler_loaded(self):
        cfg = self._load(
            """
[notifiers.matrix]
type = "matrix"
homeserver = "https://matrix.org"
access_token = "syt_abc"
room_id = "!xyz:matrix.org"
"""
        )
        handler = cfg["notifiers"]["matrix"]
        assert isinstance(handler, MatrixAlertHandler)

    def test_matrix_homeserver_stored(self):
        cfg = self._load(
            """
[notifiers.matrix]
type = "matrix"
homeserver = "https://my.server"
access_token = "tok"
room_id = "!r:my.server"
"""
        )
        handler = cfg["notifiers"]["matrix"]
        assert handler.homeserver == "https://my.server"

    def test_matrix_room_id_stored(self):
        cfg = self._load(
            """
[notifiers.matrix]
type = "matrix"
homeserver = "https://my.server"
access_token = "tok"
room_id = "!roomABC:my.server"
"""
        )
        handler = cfg["notifiers"]["matrix"]
        assert handler.room_id == "!roomABC:my.server"

    def test_missing_homeserver_raises(self):
        with pytest.raises((KeyError, ValueError)):
            self._load(
                """
[notifiers.matrix]
type = "matrix"
access_token = "tok"
room_id = "!r:h"
"""
            )
