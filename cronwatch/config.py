"""Configuration loading for cronwatch."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from cronwatch.schedule import CronJob
from cronwatch.notifiers import get_handler
from cronwatch.alerting import AlertHandler


def _parse_job(raw: dict[str, Any]) -> CronJob:
    """Build a CronJob from a raw config mapping."""
    return CronJob(
        name=raw["name"],
        schedule=raw["schedule"],
        warning_threshold=raw.get("warning_threshold", 300),
        critical_threshold=raw.get("critical_threshold", 900),
        last_run_at=raw.get("last_run_at"),
    )


def _parse_notifier(raw: dict[str, Any]) -> AlertHandler:
    """Build an AlertHandler from a raw notifier config mapping."""
    raw = dict(raw)  # copy so we can mutate
    kind = raw.pop("type")
    return get_handler(kind, **raw)


def load_config(path: str | Path) -> tuple[list[CronJob], list[AlertHandler]]:
    """Load jobs and notifiers from a TOML config file.

    Returns a tuple of (jobs, handlers).
    """
    path = Path(path)
    with path.open("rb") as fh:
        data = tomllib.load(fh)

    jobs = [_parse_job(j) for j in data.get("jobs", [])]

    handlers: list[AlertHandler] = []
    for raw_notifier in data.get("notifiers", []):
        handlers.append(_parse_notifier(raw_notifier))

    if not handlers:
        # Fall back to stdout if nothing is configured
        from cronwatch.notifiers.stdout import StdoutAlertHandler
        handlers.append(StdoutAlertHandler())

    return jobs, handlers
