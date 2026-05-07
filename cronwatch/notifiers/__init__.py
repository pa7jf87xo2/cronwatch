"""Registry that maps notifier type strings to handler instances."""
from __future__ import annotations

from typing import Any

from cronwatch.alerting import AlertHandler


def get_handler(cfg: dict[str, Any]) -> AlertHandler:
    """Instantiate the correct AlertHandler from a notifier config dict."""
    ntype = cfg.get("type", "").lower()

    if ntype == "stdout":
        from cronwatch.notifiers.stdout import StdoutAlertHandler

        return StdoutAlertHandler()

    if ntype == "slack":
        from cronwatch.notifiers.slack import SlackAlertHandler

        return SlackAlertHandler(
            webhook_url=cfg["webhook_url"],
            channel=cfg.get("channel"),
        )

    if ntype == "email":
        from cronwatch.notifiers.email import EmailAlertHandler

        return EmailAlertHandler(
            host=cfg["host"],
            port=int(cfg.get("port", 587)),
            username=cfg["username"],
            password=cfg["password"],
            sender=cfg["sender"],
            recipients=cfg["recipients"],
            use_tls=bool(cfg.get("use_tls", True)),
        )

    if ntype == "webhook":
        from cronwatch.notifiers.webhook import WebhookAlertHandler

        return WebhookAlertHandler(
            url=cfg["url"],
            headers=cfg.get("headers", {}),
        )

    if ntype == "pagerduty":
        from cronwatch.notifiers.pagerduty import PagerDutyAlertHandler

        return PagerDutyAlertHandler(integration_key=cfg["integration_key"])

    if ntype == "sms":
        from cronwatch.notifiers.sms import SMSAlertHandler

        return SMSAlertHandler(
            account_sid=cfg["account_sid"],
            auth_token=cfg["auth_token"],
            from_number=cfg["from_number"],
            to_number=cfg["to_number"],
        )

    if ntype == "opsgenie":
        from cronwatch.notifiers.opsgenie import OpsGenieAlertHandler

        return OpsGenieAlertHandler(api_key=cfg["api_key"])

    if ntype == "victorops":
        from cronwatch.notifiers.victorops import VictorOpsAlertHandler

        return VictorOpsAlertHandler(endpoint=cfg["endpoint"])

    if ntype == "teams":
        from cronwatch.notifiers.teams import TeamsAlertHandler

        return TeamsAlertHandler(webhook_url=cfg["webhook_url"])

    if ntype == "discord":
        from cronwatch.notifiers.discord import DiscordAlertHandler

        return DiscordAlertHandler(
            webhook_url=cfg["webhook_url"],
            username=cfg.get("username", "cronwatch"),
        )

    if ntype == "telegram":
        from cronwatch.notifiers.telegram import TelegramAlertHandler

        return TelegramAlertHandler(
            bot_token=cfg["bot_token"],
            chat_id=cfg["chat_id"],
        )

    if ntype == "gotify":
        from cronwatch.notifiers.gotify import GotifyAlertHandler

        return GotifyAlertHandler(
            url=cfg["url"],
            token=cfg["token"],
            priority=cfg.get("priority"),
        )

    raise ValueError(f"Unknown notifier type: {ntype!r}")
