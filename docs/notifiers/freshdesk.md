# Freshdesk Notifier

The **Freshdesk** notifier opens a support ticket in your Freshdesk account
whenever cronwatch fires an alert.

## Configuration

```toml
[notifiers.freshdesk]
type     = "freshdesk"
domain   = "yourcompany.freshdesk.com"  # required
api_key  = "YOUR_API_KEY"               # required
email    = "requester@example.com"      # required – ticket requester
tags     = ["cronwatch", "infra"]       # optional, default: ["cronwatch"]
```

### Fields

| Field     | Required | Description |
|-----------|----------|-------------|
| `domain`  | ✅       | Your Freshdesk subdomain, e.g. `acme.freshdesk.com` |
| `api_key` | ✅       | API key from **Profile Settings → API Key** |
| `email`   | ✅       | Email address used as the ticket requester |
| `tags`    | ❌       | List of tags applied to every ticket (default: `["cronwatch"]`) |

## Alert → Ticket priority mapping

| cronwatch level | Freshdesk priority |
|-----------------|--------------------|
| `INFO`          | Low (1)            |
| `WARNING`       | Medium (2)         |
| `CRITICAL`      | High (3)           |

## Obtaining an API key

1. Log in to your Freshdesk portal.
2. Click your avatar in the top-right corner → **Profile Settings**.
3. Copy the **API Key** shown on the right-hand side.

## Example

```toml
[notifiers.ops_desk]
type    = "freshdesk"
domain  = "acme.freshdesk.com"
api_key = "xxxxxxxxxxxxxxxxxxx"
email   = "oncall@acme.com"
tags    = ["cron", "automated"]
```
