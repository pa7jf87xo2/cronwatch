"""Simple polling daemon that runs the checker on a configurable interval."""

from __future__ import annotations

import logging
import time
from typing import List

from cronwatch.alerting import AlertHandler
from cronwatch.checker import CronChecker
from cronwatch.schedule import CronJob

logger = logging.getLogger(__name__)


class CronWatchDaemon:
    """Polls job schedules and fires alerts via the supplied handler."""

    def __init__(
        self,
        jobs: List[CronJob],
        handler: AlertHandler,
        poll_interval: int = 60,
    ) -> None:
        self._jobs = jobs
        self._checker = CronChecker(handler)
        self._poll_interval = poll_interval
        self._running = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:  # pragma: no cover
        """Run the daemon loop indefinitely (blocking)."""
        self._running = True
        logger.info(
            "cronwatch daemon started — monitoring %d job(s), poll interval %ds",
            len(self._jobs),
            self._poll_interval,
        )
        try:
            while self._running:
                self._tick()
                time.sleep(self._poll_interval)
        except KeyboardInterrupt:
            logger.info("cronwatch daemon stopped by user.")
        finally:
            self._running = False

    def stop(self) -> None:
        """Signal the daemon loop to stop after the current tick."""
        self._running = False

    def _tick(self) -> None:
        """Single evaluation pass — separated for testability."""
        alerts = self._checker.check(self._jobs)
        if alerts:
            logger.warning("%d alert(s) dispatched in this tick.", len(alerts))
        else:
            logger.debug("All jobs healthy.")
