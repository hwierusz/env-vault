# Vault Maturity

The `maturity` module assesses how well-managed a vault is across multiple operational dimensions, producing a score and a named maturity level.

## Levels

| Level | Score range |
|------------|-------------|
| initial | 0 – 34 |
| developing | 35 – 54 |
| defined | 55 – 74 |
| managed | 75 – 89 |
| optimizing | 90 – 100 |

## Dimensions

- **ttl_coverage** — percentage of keys that have a TTL set.
- **audit_activity** — based on the number of recorded audit events (capped at 100).
- **key_hygiene** — percentage of keys that follow `UPPER_SNAKE_CASE` convention.

## Python API

```python
from env_vault.maturity import assess_maturity

report = assess_maturity("prod", password="s3cr3t")
print(report.level)    # e.g. "managed"
print(report.overall)  # e.g. 78
print(report.scores)   # {'ttl_coverage': 60, 'audit_activity': 80, 'key_hygiene': 95}
```

## CLI

```bash
# Text report
env-vault maturity show prod

# JSON report
env-vault maturity show prod --format json

# List all maturity levels
env-vault maturity levels
```
