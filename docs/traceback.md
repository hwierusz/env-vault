# Traceback

The **traceback** module records the origin of variable changes in a vault, allowing you to audit where each value came from.

## Concepts

- **TraceEntry** — a single record containing the key, value, source label, timestamp, and optional note.
- Entries are appended to a `.trace.jsonl` file alongside the vault.

## Python API

```python
from env_vault.traceback import record_trace, read_traces, clear_traces

# Record that DB_URL was set via the import command
entry = record_trace(
    vault_dir=".vaults",
    vault_name="myapp",

    value="postgres://localhost/mydb",
    source="import",
    note="initial seed",
)

# Read all traces
entries = read_traces(".vaults", "myapp")

# Read traces for a specific key
entries = read_traces(".vaults", "myapp", key="DB_URL")

# Clear all traces (returns count removed)
count = clear_traces(".vaults", "myapp")
```

## CLI

### Record a trace

```bash
env-vault traceback record myapp DB_URL "postgres://" --source cli --note "manual update"
```

### Show traces

```bash
# All entries
env-vault traceback show myapp

# Filter by key
env-vault traceback show myapp --key DB_URL

# JSON output
env-vault traceback show myapp --format json
```

### Clear traces

```bash
env-vault traceback clear myapp
```

## Output format (text)

```
[2024-06-01T12:00:00+00:00] DB_URL <- import (initial seed)
[2024-06-02T09:30:00+00:00] API_KEY <- cli
```

## Notes

- Traces are append-only; clearing removes the file entirely.
- The `source` field is free-form — use values like `cli`, `import`, `api`, `migration`, etc.
