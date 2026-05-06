"""Tests verifying that load_config correctly wires up notifiers."""

import textwrap
import tempfile
from pathlib import Path

import pytest

from cronwatch.config import load_config, _parse_notifier
from cronwatch.notifiers.stdout import StdoutAlertHandler
from cronwatch.notifiers.victorops import VictorOpsAlertHandler
from cronwatch.notifiers.slack import SlackAlertHandler


def _write_toml(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".toml", delete=False, mode="w")
    tmp.write(textwrap.dedent(content))
    tmp.flush()
    return Path(tmp.name)


class TestParseNotifier:
    def test_stdout_handler(self):
        handler = _parse_notifier({"type": "stdout"})
        assert isinstance(handler, StdoutAlertHandler)

    def test_victorops_handler(self):
        handler = _parse_notifier({
            "type": "victorops",
            "rest_endpoint_url": "https://alert.victorops.com/TOKEN",
            "routing_key": "ops",
        })
        assert isinstance(handler, VictorOpsAlertHandler)

    def test_slack_handler(self):
        handler = _parse_notifier({
            "type": "slack",
            "webhook_url": "https://hooks.slack.com/services/XXX",
        })
        assert isinstance(handler, SlackAlertHandler)

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown notifier"):
            _parse_notifier({"type": "nonexistent"})


class TestLoadConfigNotifiers:
    def test_defaults_to_stdout_when_no_notifiers(self):
        path = _write_toml("""
            [[jobs]]
            name = "test-job"
            schedule = "* * * * *"
        """)
        _, handlers = load_config(path)
        assert len(handlers) == 1
        assert isinstance(handlers[0], StdoutAlertHandler)

    def test_victorops_notifier_loaded_from_toml(self):
        path = _write_toml("""
            [[jobs]]
            name = "test-job"
            schedule = "* * * * *"

            [[notifiers]]
            type = "victorops"
            rest_endpoint_url = "https://alert.victorops.com/TOKEN"
            routing_key = "default"
        """)
        _, handlers = load_config(path)
        assert any(isinstance(h, VictorOpsAlertHandler) for h in handlers)

    def test_multiple_notifiers_loaded(self):
        path = _write_toml("""
            [[jobs]]
            name = "test-job"
            schedule = "* * * * *"

            [[notifiers]]
            type = "stdout"

            [[notifiers]]
            type = "victorops"
            rest_endpoint_url = "https://alert.victorops.com/TOKEN"
            routing_key = "default"
        """)
        _, handlers = load_config(path)
        assert len(handlers) == 2
        types = {type(h) for h in handlers}
        assert StdoutAlertHandler in types
        assert VictorOpsAlertHandler in types
