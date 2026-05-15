# Zenduty Notifier

Send cronwatch alerts to [Zenduty](https://www.zenduty.com/) via its
**Events API**.

## Configuration

Add a `[[notifiers]]` block to your `cronwatch.toml`:

```toml
[[notifiers]]
type = "zenduty"
integration_key = "YOUR_INTEGRATION_KEY"
# timeout = 10  # optional, seconds (default: 10)
```

### Fields

| Field             | Required | Default | Description                                      |
|-------------------|----------|---------|--------------------------------------------------|
| `integration_key` | ✅        | —       | Service integration key from the Zenduty dashboard |
| `timeout`         | ❌        | `10`    | HTTP request timeout in seconds                  |

## Finding your Integration Key

1. Log in to [app.zenduty.com](https://app.zenduty.com).
2. Navigate to **Teams → Services → Integrations**.
3. Add or select an **API** integration.
4. Copy the **Integration Key**.

## Alert Mapping

| cronwatch level | Zenduty `alert_type` |
|-----------------|----------------------|
| `WARNING`       | `warning`            |
| `CRITICAL`      | `critical`           |

## Example

```toml
[[jobs]]
name = "database-backup"
schedule = "0 2 * * *"
timeout_minutes = 30

[[notifiers]]
type = "zenduty"
integration_key = "abc123xyz"
```
