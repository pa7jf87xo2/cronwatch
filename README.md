# cronwatch

Lightweight daemon that monitors cron job execution times and alerts on missed or overdue runs.

---

## Installation

```bash
pip install cronwatch
```

Or install from source:

```bash
git clone https://github.com/yourname/cronwatch.git && cd cronwatch && pip install .
```

---

## Usage

Define your monitored jobs in a YAML config file:

```yaml
# cronwatch.yml
jobs:
  daily-backup:
    schedule: "0 2 * * *"
    timeout: 300
    alert: email

  hourly-sync:
    schedule: "0 * * * *"
    timeout: 60
    alert: slack
```

Start the daemon:

```bash
cronwatch --config cronwatch.yml
```

Wrap an existing cron job to report its status:

```bash
cronwatch run --job daily-backup -- /usr/local/bin/backup.sh
```

View job status:

```bash
cronwatch status
```

---

## Configuration

| Key        | Description                              | Default  |
|------------|------------------------------------------|----------|
| `schedule` | Cron expression for expected run time    | required |
| `timeout`  | Max allowed runtime in seconds           | `3600`   |
| `alert`    | Alert channel (`email`, `slack`, `log`)  | `log`    |

---

## License

MIT © 2024 [yourname](https://github.com/yourname)