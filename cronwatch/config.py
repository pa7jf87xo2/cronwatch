"""Load and validate cronwatch configuration from a YAML file."""

from pathlib import Path
from typing import Any

import yaml

from cronwatch.schedule import CronJob

DEFAULT_GRACE_PERIOD = 60


def _parse_job(raw: dict[str, Any]) -> CronJob:
    """Convert a raw config dict into a CronJob instance."""
    required = {"name", "schedule"}
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"Job config missing required fields: {missing}")

    return CronJob(
        name=raw["name"],
        schedule=raw["schedule"],
        grace_period_seconds=int(raw.get("grace_period_seconds", DEFAULT_GRACE_PERIOD)),
        tags=list(raw.get("tags", [])),
    )


def load_config(path: str | Path) -> list[CronJob]:
    """Parse *path* (YAML) and return a list of configured CronJob objects.

    Expected format::

        jobs:
          - name: backup
            schedule: "0 2 * * *"
            grace_period_seconds: 300
            tags: [infra]
          - name: report
            schedule: "0 8 * * 1-5"
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open() as fh:
        data = yaml.safe_load(fh) or {}

    raw_jobs = data.get("jobs", [])
    if not isinstance(raw_jobs, list):
        raise ValueError("'jobs' must be a list in the config file.")

    return [_parse_job(j) for j in raw_jobs]
