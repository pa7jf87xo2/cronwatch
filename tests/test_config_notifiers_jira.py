"""Config-parsing tests for the Jira notifier."""

from __future__ import annotations

import os
import tempfile
import unittest

from cronwatch.config import load_config
from cronwatch.notifiers.jira import JiraAlertHandler


def _write_toml(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as fh:
        fh.write(content)
    return path


class TestJiraConfigParsing(unittest.TestCase):
    def teardown_method(self, _method: object) -> None:  # pytest compat
        pass

    def tearDown(self) -> None:
        pass

    def _load(self, toml: str) -> object:
        path = _write_toml(toml)
        try:
            return load_config(path)
        finally:
            os.unlink(path)

    def test_jira_handler_loaded(self) -> None:
        cfg = self._load("""
[notifiers.jira]
type = "jira"
base_url = "https://myorg.atlassian.net"
email = "ops@myorg.com"
api_token = "abc123"
project_key = "OPS"
""")
        handler = cfg.notifiers["jira"]
        self.assertIsInstance(handler, JiraAlertHandler)

    def test_jira_handler_custom_issue_type(self) -> None:
        cfg = self._load("""
[notifiers.jira]
type = "jira"
base_url = "https://myorg.atlassian.net"
email = "ops@myorg.com"
api_token = "abc123"
project_key = "OPS"
issue_type = "Task"
""")
        handler = cfg.notifiers["jira"]
        self.assertIsInstance(handler, JiraAlertHandler)
        self.assertEqual(handler._issue_type, "Task")

    def test_jira_default_issue_type_is_bug(self) -> None:
        cfg = self._load("""
[notifiers.jira]
type = "jira"
base_url = "https://myorg.atlassian.net"
email = "ops@myorg.com"
api_token = "abc123"
project_key = "INFRA"
""")
        handler = cfg.notifiers["jira"]
        self.assertEqual(handler._issue_type, "Bug")
