"""Simple stdout alert handler — useful for local development and testing."""

from __future__ import annotations

import sys
from typing import TextIO

from cronwatch.alerting import Alert, AlertHandler


class StdoutAlertHandler(AlertHandler):
    """Prints alerts to stdout (or any writable stream)."""

    def __init__(self, stream: TextIO = sys.stdout) -> None:
        self._stream = stream

    def send(self, alert: Alert) -> None:
        print(str(alert), file=self._stream, flush=True)
