"""Notifier plugin registry for cronwatch."""

from cronwatch.notifiers.stdout import StdoutAlertHandler
from cronwatch.notifiers.slack import SlackAlertHandler
from cronwatch.notifiers.email import EmailAlertHandler
from cronwatch.notifiers.webhook import WebhookAlertHandler
from cronwatch.notifiers.pagerduty import PagerDutyAlertHandler
from cronwatch.notifiers.sms import SMSAlertHandler
from cronwatch.notifiers.opsgenie import OpsGenieAlertHandler
from cronwatch.notifiers.victorops import VictorOpsAlertHandler

__all__ = [
    "StdoutAlertHandler",
    "SlackAlertHandler",
    "EmailAlertHandler",
    "WebhookAlertHandler",
    "PagerDutyAlertHandler",
    "SMSAlertHandler",
    "OpsGenieAlertHandler",
    "VictorOpsAlertHandler",
]

REGISTRY: dict[str, type] = {
    "stdout": StdoutAlertHandler,
    "slack": SlackAlertHandler,
    "email": EmailAlertHandler,
    "webhook": WebhookAlertHandler,
    "pagerduty": PagerDutyAlertHandler,
    "sms": SMSAlertHandler,
    "opsgenie": OpsGenieAlertHandler,
    "victorops": VictorOpsAlertHandler,
}


def get_handler(name: str, **kwargs):
    """Instantiate a notifier by its registry name."""
    try:
        cls = REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Unknown notifier '{name}'. Available: {list(REGISTRY)}"
        ) from None
    return cls(**kwargs)
