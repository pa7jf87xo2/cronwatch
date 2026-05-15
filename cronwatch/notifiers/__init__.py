"""Notifier registry for cronwatch."""

from __future__ import annotations

from typing import Any

from cronwatch.alerting import AlertHandler


def get_handler(cfg: dict[str, Any]) -> AlertHandler:  # noqa: C901
    """Instantiate and return the correct AlertHandler from a config dict."""
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
            bot_token=cfg["bot_token"],
            chat_id=cfg["chat_id"],
        )

    if kind == "gotify":
        from cronwatch.notifiers.gotify import GotifyAlertHandler
        return GotifyAlertHandler(
            url=cfg["url"],
            app_token=cfg["app_token"],
        )

    if kind == "ntfy":
        from cronwatch.notifiers.ntfy import NtfyAlertHandler
        return NtfyAlertHandler(
            topic=cfg["topic"],
            server=cfg.get("server", "https://ntfy.sh"),
        )

    if kind == "matrix":
        from cronwatch.notifiers.matrix import MatrixAlertHandler
        return MatrixAlertHandler(
            homeserver=cfg["homeserver"],
            access_token=cfg["access_token"],
            room_id=cfg["room_id"],
        )

    if kind == "mattermost":
        from cronwatch.notifiers.mattermost import MattermostAlertHandler
        return MattermostAlertHandler(webhook_url=cfg["webhook_url"])

    if kind == "pushover":
        from cronwatch.notifiers.pushover import PushoverAlertHandler
        return PushoverAlertHandler(
            user_key=cfg["user_key"],
            api_token=cfg["api_token"],
        )

    if kind == "rocketchat":
        from cronwatch.notifiers.rocketchat import RocketChatAlertHandler
        return RocketChatAlertHandler(webhook_url=cfg["webhook_url"])

    if kind == "signalwire":
        from cronwatch.notifiers.signalwire import SignalWireAlertHandler
        return SignalWireAlertHandler(
            space_url=cfg["space_url"],
            project_id=cfg["project_id"],
            api_token=cfg["api_token"],
            from_number=cfg["from_number"],
            to_number=cfg["to_number"],
        )

    raise ValueError(f"Unknown notifier type: {kind!r}")
