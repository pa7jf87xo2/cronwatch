"""Tests for Datadog notifier config parsing."""

import os
import tempfile
import unittest

from cronwatch.config import load_config
from cronwatch.notifiers.datadog import DatadogAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


class TestDatadogConfigParsing(unittest.TestCase):
    def teardown_method(self, _):
        pass

    def tearDown(self):
        pass

    def _load(self, toml: str):
        path = _write_toml(toml)
        try:
            return load_config(path)
        finally:
            os.unlink(path)

    def test_datadog_handler_loaded(self):
        cfg = self._load(
            """
[jobs.heartbeat]
schedule = "* * * * *"
warn_after = 120
crit_after = 300

[[notifiers]]
type = "datadog"
api_key = "abc123"
"""
        )
        self.assertEqual(len(cfg.notifiers), 1)
        self.assertIsInstance(cfg.notifiers[0], DatadogAlertHandler)

    def test_datadog_handler_with_app_key(self):
        cfg = self._load(
            """
[jobs.heartbeat]
schedule = "* * * * *"
warn_after = 120
crit_after = 300

[[notifiers]]
type = "datadog"
api_key = "abc123"
app_key = "appxyz"
"""
        )
        handler = cfg.notifiers[0]
        self.assertIsInstance(handler, DatadogAlertHandler)
        self.assertEqual(handler._app_key, "appxyz")

    def test_datadog_handler_custom_site(self):
        cfg = self._load(
            """
[jobs.heartbeat]
schedule = "* * * * *"
warn_after = 120
crit_after = 300

[[notifiers]]
type = "datadog"
api_key = "abc123"
site = "datadoghq.eu"
"""
        )
        handler = cfg.notifiers[0]
        self.assertIsInstance(handler, DatadogAlertHandler)
        self.assertIn("datadoghq.eu", handler._base_url)


if __name__ == "__main__":
    unittest.main()
