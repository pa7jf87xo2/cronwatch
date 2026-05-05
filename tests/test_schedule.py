"""Tests for cronwatch.schedule and cronwatch.config."""

from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent

import pytest

from cronwatch.schedule import CronJob
from cronwatch.config import load_config


# ---------------------------------------------------------------------------
# CronJob
# ---------------------------------------------------------------------------

class TestCronJob:
    def test_invalid_schedule_raises(self):
        with pytest.raises(ValueError, match="Invalid cron expression"):
            CronJob(name="bad", schedule="not-a-cron")

    def test_next_run_is_in_future(self):
        job = CronJob(name="tick", schedule="* * * * *")
        now = datetime.utcnow()
        assert job.next_run_at(now) > now

    def test_expected_run_is_in_past(self):
        job = CronJob(name="tick", schedule="* * * * *")
        now = datetime.utcnow()
        assert job.expected_run_at(now) <= now

    def test_not_overdue_when_last_run_is_recent(self):
        job = CronJob(name="tick", schedule="* * * * *", grace_period_seconds=60)
        now = datetime(2024, 1, 1, 12, 0, 30)  # 30 s into the minute
        job.last_run = datetime(2024, 1, 1, 12, 0, 0)  # ran at top of minute
        assert not job.is_overdue(now)

    def test_overdue_when_no_last_run_and_past_grace(self):
        job = CronJob(name="tick", schedule="0 * * * *", grace_period_seconds=60)
        # 2 minutes after the hour — no last_run recorded
        now = datetime(2024, 1, 1, 12, 2, 0)
        assert job.is_overdue(now)

    def test_seconds_overdue_returns_zero_when_not_overdue(self):
        job = CronJob(name="tick", schedule="* * * * *", grace_period_seconds=300)
        now = datetime(2024, 1, 1, 12, 0, 10)
        job.last_run = datetime(2024, 1, 1, 12, 0, 0)
        assert job.seconds_overdue(now) == 0.0

    def test_seconds_overdue_positive_when_overdue(self):
        job = CronJob(name="hourly", schedule="0 * * * *", grace_period_seconds=60)
        now = datetime(2024, 1, 1, 12, 5, 0)  # 5 min after hour, no last_run
        assert job.seconds_overdue(now) > 0


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_load_valid_config(self, tmp_path: Path):
        cfg = tmp_path / "cronwatch.yml"
        cfg.write_text(dedent("""
            jobs:
              - name: backup
                schedule: "0 2 * * *"
                grace_period_seconds: 300
                tags: [infra]
              - name: report
                schedule: "0 8 * * 1-5"
        """))
        jobs = load_config(cfg)
        assert len(jobs) == 2
        assert jobs[0].name == "backup"
        assert jobs[0].grace_period_seconds == 300
        assert jobs[0].tags == ["infra"]
        assert jobs[1].grace_period_seconds == 60  # default

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yml")

    def test_missing_name_raises(self, tmp_path: Path):
        cfg = tmp_path / "bad.yml"
        cfg.write_text("jobs:\n  - schedule: '* * * * *'\n")
        with pytest.raises(ValueError, match="missing required fields"):
            load_config(cfg)
