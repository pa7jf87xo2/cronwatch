"""Notifier registry – maps type strings to handler classes."""

from __future__ import annotations

from typing import Any

from cronwatch.alerting import AlertHandler


def get_handler(cfg: dict[str, Any]) -> AlertHandler:
    """Instantiate the correct AlertHandler from a notifier config dict."""
    kind = cfg.get("type", "").lower()

    if kind == "stdout":
        from cronwatch.notifiers.stdout import StdoutAlertHandler
        return StdoutAlertHandler()

    if kind == "slack":
        from cronwatch.notifiers.slack import SlackAlertHandler
        return SlackAlertHandler(
            webhook_url=cfg["webhook_url"],
            channel=cfg.get("channel", ""),
        )

    if kind == "email":
        from cronwatch.notifiers.email import EmailAlertHandler
        return EmailAlertHandler(
            host=cfg["host"],
            port=int(cfg.get("port", 587)),
            username=cfg["username"],
            password=cfg["password"],
            from_addr=cfg["from_addr"],
            to_addrs=cfg["to_addrs"],
            use_tls=bool(cfg.get("use_tls", True)),
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
        return VictorOpsAlertHandler(endpoint_url=cfg["endpoint_url"])

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
            token=cfg.get("token", ""),
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

    if kind == "zulip":
        from cronwatch.notifiers.zulip import ZulipAlertHandler
        return ZulipAlertHandler(
            site=cfg["site"],
            email=cfg["email"],
            api_key=cfg["api_key"],
            stream=cfg["stream"],
            topic=cfg.get("topic", "cronwatch"),
        )

    if kind == "datadog":
        from cronwatch.notifiers.datadog import DatadogAlertHandler
        return DatadogAlertHandler(
            api_key=cfg["api_key"],
            tags=cfg.get("tags", []),
        )

    if kind == "grafana":
        from cronwatch.notifiers.grafana import GrafanaAlertHandler
        return GrafanaAlertHandler(
            url=cfg["url"],
            api_key=cfg["api_key"],
        )

    if kind == "splunk":
        from cronwatch.notifiers.splunk import SplunkAlertHandler
        return SplunkAlertHandler(
            hec_url=cfg["hec_url"],
            hec_token=cfg["hec_token"],
            index=cfg.get("index", "main"),
        )

    if kind == "sns":
        from cronwatch.notifiers.sns import SNSAlertHandler
        return SNSAlertHandler(
            topic_arn=cfg["topic_arn"],
            region=cfg.get("region", "us-east-1"),
            aws_access_key_id=cfg.get("aws_access_key_id", ""),
            aws_secret_access_key=cfg.get("aws_secret_access_key", ""),
        )

    if kind == "hipchat":
        from cronwatch.notifiers.hipchat import HipChatAlertHandler
        return HipChatAlertHandler(
            token=cfg["token"],
            room_id=cfg["room_id"],
        )

    if kind == "googlechat":
        from cronwatch.notifiers.googlechat import GoogleChatAlertHandler
        return GoogleChatAlertHandler(webhook_url=cfg["webhook_url"])

    if kind == "linear":
        from cronwatch.notifiers.linear import LinearAlertHandler
        return LinearAlertHandler(
            api_key=cfg["api_key"],
            team_id=cfg["team_id"],
            label_ids=cfg.get("label_ids", []),
        )

    if kind == "jira":
        from cronwatch.notifiers.jira import JiraAlertHandler
        return JiraAlertHandler(
            base_url=cfg["base_url"],
            email=cfg["email"],
            api_token=cfg["api_token"],
            project_key=cfg["project_key"],
            issue_type=cfg.get("issue_type", "Bug"),
        )

    raise ValueError(f"Unknown notifier type: {kind!r}")
