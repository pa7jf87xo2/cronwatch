# Jira Notifier

The Jira notifier opens a new Jira issue whenever cronwatch fires an alert.
It uses the [Jira REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/) and authenticates with an API token.

## Configuration

```toml
[notifiers.jira]
type         = "jira"
base_url     = "https://myorg.atlassian.net"   # required
email        = "ops@myorg.com"                  # required – Atlassian account email
api_token    = "YOUR_API_TOKEN"                 # required – create at id.atlassian.com
project_key  = "OPS"                            # required – Jira project key
issue_type   = "Bug"                            # optional, default: "Bug"
```

## Priority mapping

| cronwatch level | Jira priority |
|-----------------|---------------|
| `CRITICAL`      | Highest       |
| `WARNING`       | Medium        |
| `INFO`          | Low           |

## Generating an API token

1. Log in to <https://id.atlassian.com/manage-profile/security/api-tokens>.
2. Click **Create API token**, give it a label, and copy the value.
3. Store it securely – treat it like a password.

## Issue description format

The issue description is written using the Atlassian Document Format (ADF) and
contains the full `str(alert)` output, which includes the job name, alert level,
timestamp, and human-readable message.

## Notes

- One Jira issue is created per alert firing.  cronwatch does **not** deduplicate
  or auto-resolve issues; use Jira automation rules or a separate reconciliation
  step if you need that behaviour.
- The notifier requires outbound HTTPS access to your Atlassian Cloud instance.
