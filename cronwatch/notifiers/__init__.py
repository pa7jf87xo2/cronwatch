"""Notifier registry for cronwatch."""

from typing import Any, Dict

from cronwatch.alerting import AlertHandler


def get_handler(cfg: Dict[str, Any]) -> AlertHandler:
    """Instantiate the correct AlertHandler from a notifier config dict."""
    kind = cfg.get("type", "").lower()

    if kind == "stdout":
        from cronwatch.notifiers.stdout import StdoutAlertHandler
        return StdoutAlertHandler()

    if kind == "slack":
        from cronwatch.notifiers.slack import SlackAlertHandler
        return SlackAlertHandler(webhook_url=cfg["webhook_url"])

    if kind == "email":
        from cronwatch.notifiers.email import EmailAlertHandler
        return EmailAlertHandler(
            host=cfg["host"],
            port=int(cfg.get("port", 587)),
            username=cfg["username"],
            password=cfg["password"],
            from_addr=cfg["from"],
            to_addrs=cfg["to"],
            use_tls=cfg.get("use_tls", True),
        )

    if kind == "webhook":
        from cronwatch.notifiers.webhook import WebhookAlertHandler
        return WebhookAlertHandler(
            url=cfg["url"],
            headers=cfg.get("headers", {}),
        )

    if kind == "pagerduty":
        from cronwatch.notifiers.pagerduty import PagerDutyAlertHandler
        return PagerDutyAlertHandler(integration_key=cfg["integration_key"])

    if kind == "sms":
        from cronwatch.notifiers.sms import SMSAlertHandler
        return SMSAlertHandler(
            account_sid=cfg["account_sid"],
            auth_token=cfg["auth_token"],
            from_number=cfg["from_number"],
            to_number=cfg["to_number"],
        )

    if kind == "opsgenie":
        from cronwatch.notifiers.opsgenie import OpsGenieAlertHandler
        return OpsGenieAlertHandler(api_key=cfg["api_key"])

    if kind == "victorops":
        from cronwatch.notifiers.victorops import VictorOpsAlertHandler
        return VictorOpsAlertHandler(endpoint=cfg["endpoint"])

    if kind == "teams":
        from cronwatch.notifiers.teams import TeamsAlertHandler
        return TeamsAlertHandler(webhook_url=cfg["webhook_url"])

    if kind == "discord":
        from cronwatch.notifiers.discord import DiscordAlertHandler
        return DiscordAlertHandler(
            webhook_url=cfg["webhook_url"],
            username=cfg.get("username", "cronwatch"),
        )

    if kind == "telegram":
        from cronwatch.notifiers.telegram import TelegramAlertHandler
        return TelegramAlertHandler(
            token=cfg["token"],
            chat_id=cfg["chat_id"],
            parse_mode=cfg.get("parse_mode", "Markdown"),
        )

    raise ValueError(f"Unknown notifier type: {kind!r}")
