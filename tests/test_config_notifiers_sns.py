"""Integration tests: load SNS notifier from TOML config."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.sns import SNSAlertHandler


def _write_toml(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False
    )
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


class TestSNSConfigParsing:
    def teardown_method(self, _method):
        # clean up any temp files created during the test
        pass

    def _load(self, toml: str):
        path = _write_toml(toml)
        try:
            cfg = load_config(str(path))
        finally:
            os.unlink(path)
        return cfg

    def test_sns_handler_loaded(self):
        cfg = self._load(
            """
[notifiers.ops_sns]
type = "sns"
topic_arn = "arn:aws:sns:us-east-1:123:cron-alerts"
region = "us-east-1"
aws_access_key_id = "AKIA123"
aws_secret_access_key = "SECRET"
"""
        )
        handler = cfg.notifiers["ops_sns"]
        assert isinstance(handler, SNSAlertHandler)

    def test_sns_handler_attributes(self):
        cfg = self._load(
            """
[notifiers.prod_sns]
type = "sns"
topic_arn = "arn:aws:sns:eu-central-1:456:alerts"
region = "eu-central-1"
aws_access_key_id = "AKIATEST"
aws_secret_access_key = "MYSECRET"
subject_prefix = "[prod]"
"""
        )
        h: SNSAlertHandler = cfg.notifiers["prod_sns"]
        assert h.topic_arn == "arn:aws:sns:eu-central-1:456:alerts"
        assert h.region == "eu-central-1"
        assert h.subject_prefix == "[prod]"

    def test_sns_missing_topic_arn_raises(self):
        with pytest.raises(Exception):
            self._load(
                """
[notifiers.bad_sns]
type = "sns"
region = "us-east-1"
aws_access_key_id = "K"
aws_secret_access_key = "S"
"""
            )
