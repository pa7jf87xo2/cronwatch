"""Core schedule model for cronwatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from croniter import CroniterBadCronError, croniter


@dataclass
class CronJob:
    name: str
    schedule: str  # standard 5-field cron expression
    grace_period: int = 300  # seconds before a job is considered overdue
    last_run_at: Optional[datetime] = field(default=None)

    def __post_init__(self) -> None:
        if not croniter.is_valid(self.schedule):
            raise ValueError(f"Invalid cron expression for job '{self.name}': '{self.schedule}'")

    def expected_run_at(self, base: Optional[datetime] = None) -> datetime:
        """Return the most recent scheduled run time relative to *base* (default: now)."""
        base = base or datetime.utcnow()
        itr = croniter(self.schedule, base)
        return itr.get_prev(datetime)

    def next_run_at(self, base: Optional[datetime] = None) -> datetime:
        """Return the next scheduled run time relative to *base* (default: now)."""
        base = base or datetime.utcnow()
        itr = croniter(self.schedule, base)
        return itr.get_next(datetime)

    def is_overdue(self) -> bool:
        """Return True when the job has missed its last expected run (+ grace period)."""
        expected = self.expected_run_at()
        deadline = expected + timedelta(seconds=self.grace_period)
        if self.last_run_at is None:
            return datetime.utcnow() > deadline
        return self.last_run_at < expected and datetime.utcnow() > deadline

    def overdue_by(self) -> Optional[timedelta]:
        """Return how long the job has been overdue, or None if it is not overdue."""
        if not self.is_overdue():
            return None
        expected = self.expected_run_at()
        deadline = expected + timedelta(seconds=self.grace_period)
        return datetime.utcnow() - deadline

    def mark_ran(self, ran_at: Optional[datetime] = None) -> None:
        """Record that the job ran at *ran_at* (default: now)."""
        self.last_run_at = ran_at or datetime.utcnow()
