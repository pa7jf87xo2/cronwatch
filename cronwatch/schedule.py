"""Cron schedule parsing and next-run calculation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from croniter import croniter


@dataclass
class CronJob:
    """Represents a monitored cron job."""

    name: str
    schedule: str  # standard cron expression, e.g. "*/5 * * * *"
    grace_period_seconds: int = 60
    last_run: Optional[datetime] = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not croniter.is_valid(self.schedule):
            raise ValueError(f"Invalid cron expression for job '{self.name}': {self.schedule}")

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

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        """Return True if the job has missed its last scheduled window (+ grace period)."""
        now = now or datetime.utcnow()
        expected = self.expected_run_at(now)
        deadline = expected.timestamp() + self.grace_period_seconds

        if self.last_run is None:
            return now.timestamp() > deadline

        return self.last_run < expected and now.timestamp() > deadline

    def seconds_overdue(self, now: Optional[datetime] = None) -> float:
        """Return how many seconds past the grace-period deadline the job is (0 if not overdue)."""
        now = now or datetime.utcnow()
        if not self.is_overdue(now):
            return 0.0
        expected = self.expected_run_at(now)
        deadline = expected.timestamp() + self.grace_period_seconds
        return now.timestamp() - deadline
