"""AWS SNS alert handler for cronwatch."""

from __future__ import annotations

import urllib.parse
import urllib.request
from typing import Any

from cronwatch.alerting import Alert, AlertHandler, AlertLevel


class SNSAlertHandler(AlertHandler):
    """Send alerts via AWS SNS using the HTTP Query API.

    This implementation uses only the Python standard library so that no
    third-party packages (e.g. boto3) are required.  Authentication is
    performed via simple query-string credentials; for production workloads
    consider using boto3 with SigV4 signing instead.
    """

    def __init__(
        self,
        topic_arn: str,
        region: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        subject_prefix: str = "[cronwatch]",
        timeout: int = 10,
    ) -> None:
        if not topic_arn:
            raise ValueError("topic_arn must not be empty")
        if not region:
            raise ValueError("region must not be empty")
        if not aws_access_key_id:
            raise ValueError("aws_access_key_id must not be empty")
        if not aws_secret_access_key:
            raise ValueError("aws_secret_access_key must not be empty")

        self.topic_arn = topic_arn
        self.region = region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.subject_prefix = subject_prefix
        self.timeout = timeout

    def send(self, alert: Alert) -> None:
        """Publish *alert* to the configured SNS topic."""
        level_label = alert.level.name
        subject = f"{self.subject_prefix} [{level_label}] {alert.job_name}"

        params: dict[str, Any] = {
            "Action": "Publish",
            "TopicArn": self.topic_arn,
            "Subject": subject[:100],  # SNS subject limit is 100 chars
            "Message": str(alert),
            "Version": "2010-03-31",
            "AWSAccessKeyId": self.aws_access_key_id,
            "Signature": self.aws_secret_access_key,
        }

        encoded = urllib.parse.urlencode(params).encode()
        url = f"https://sns.{self.region}.amazonaws.com/"
        req = urllib.request.Request(
            url,
            data=encoded,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
            if resp.status not in (200, 201):
                body = resp.read().decode(errors="replace")
                raise RuntimeError(
                    f"SNS publish failed ({resp.status}): {body}"
                )
