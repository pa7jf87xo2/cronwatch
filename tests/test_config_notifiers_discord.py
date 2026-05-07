"""Integration tests: loading Discord notifier via load_config."""

import textwrap
import tempfile
import os
import pytest

from cronwatch.config import load_config
from cronwatch.notifiers.discord import DiscordAlertHandler


def _write_toml(content: str) -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False
    )
    f.write(textwrap.dedent(content))
    f.close()
    return f.name


class TestDiscordConfigParsing:
    def teardown_method(self):
        # nothing persistent to clean up
        pass

    def test_discord_handler_loaded(self):
        path = _write_toml("""
            [notifiers.my_discord]
            type = "discord"
            webhook_url = "https://discord.com/api/webhooks/99/xyz"

            [[jobs]]
            name = "test_job"
            schedule = "* * * * *"
            notifiers = ["my_discord"]
        """)
        try:
            config = load_config(path)
            handler = config["notifiers"]["my_discord"]
            assert isinstance(handler, DiscordAlertHandler)
        finally:
            os.unlink(path)

    def test_discord_handler_custom_username(self):
        path = _write_toml("""
            [notifiers.disc]
            type = "discord"
            webhook_url = "https://discord.com/api/webhooks/1/a"
            username = "AlertBot"

            [[jobs]]
            name = "ping"
            schedule = "* * * * *"
            notifiers = ["disc"]
        """)
        try:
            config = load_config(path)
            handler = config["notifiers"]["disc"]
            assert isinstance(handler, DiscordAlertHandler)
            assert handler._username == "AlertBot"
        finally:
            os.unlink(path)

    def test_discord_missing_webhook_url_raises(self):
        path = _write_toml("""
            [notifiers.bad]
            type = "discord"

            [[jobs]]
            name = "ping"
            schedule = "* * * * *"
            notifiers = ["bad"]
        """)
        try:
            with pytest.raises((KeyError, ValueError)):
                load_config(path)
        finally:
            os.unlink(path)
