"""Tests for Grafana notifier config parsing."""

import os
import tempfile
import unittest

import tomllib

from cronwatch.config import load_config
from cronwatch.notifiers.grafana import GrafanaAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


class TestGrafanaConfigParsing(unittest.TestCase):
    def teardown_method(self, _method):
        pass

    def _load(self, toml: str):
        path = _write_toml(toml)
        try:
            return load_config(path)
        finally:
            os.unlink(path)

    def test_grafana_handler_loaded(self):
        cfg = self._load(
            """
[notifiers.grafana]
type = "grafana"
url = "https://grafana.example.com/api/alerts"
"""
        )
        self.assertIn("grafana", cfg.notifiers)
        self.assertIsInstance(cfg.notifiers["grafana"], GrafanaAlertHandler)

    def test_grafana_handler_with_api_key(self):
        cfg = self._load(
            """
[notifiers.grafana]
type = "grafana"
url = "https://grafana.example.com/api/alerts"
api_key = "secret-token"
"""
        )
        handler = cfg.notifiers["grafana"]
        self.assertIsInstance(handler, GrafanaAlertHandler)
        self.assertEqual(handler._api_key, "secret-token")

    def test_grafana_handler_custom_title_prefix(self):
        cfg = self._load(
            """
[notifiers.grafana]
type = "grafana"
url = "https://grafana.example.com/api/alerts"
title_prefix = "[prod]"
"""
        )
        handler = cfg.notifiers["grafana"]
        self.assertEqual(handler._title_prefix, "[prod]")

    def test_grafana_missing_url_raises(self):
        with self.assertRaises((ValueError, KeyError)):
            self._load(
                """
[notifiers.grafana]
type = "grafana"
"""
            )
