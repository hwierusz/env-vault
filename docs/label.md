# Label Management

Labels are free-form string tags you can attach to individual vault variables.
Unlike **namespaces** or **groups** (which impose structural relationships),
labels are purely descriptive and carry no special behaviour.

## Concepts

| Term  | Description |
|-------|-------------|
| Key   | A variable stored in a vault (`DB_URL`, `API_KEY`, …) |
| Label | An arbitrary short string attached to a key (`production`, `rotate-monthly`, …) |

A key may have zero or more labels.  The same label may be attached to many
keys, making it easy to query across a vault.

## CLI Usage

### Add a label

```bash
env-vault label add <vault> <key> <label>
```

```bash
env-vault label add myapp DB_URL production
# Label 'production' added to 'DB_URL'.
```

### Remove a label

```bash
env-vault label remove <vault> <key> <label>
```

### List labels on a key

```bash
env-vault label list <vault> <key>
```

```
production
critical
```

### Find keys by label

```bash
env-vault label find <vault> <label>
```

```
DB_URL: production, critical
API_KEY: production
```

## Python API

```python
from env_vault.label import add_label, remove_label, list_labels, find_by_label
from env_vault.storage import load_vault, save_vault

add_label("myapp", "DB_URL", "production", load_vault, save_vault)
print(list_labels("myapp", "DB_URL", load_vault))
# ['production']

matches = find_by_label("myapp", "production", load_vault)
# {'DB_URL': ['production']}
```

## Storage

Labels are stored inside the vault's encrypted JSON under the reserved
`__labels__` key:

```json
{
  "vars": { "DB_URL": "postgres://...", "API_KEY": "s3cr3t" },
  "__labels__": {
    "DB_URL": ["production", "critical"],
    "API_KEY": ["production"]
  }
}
```

This means labels are encrypted alongside your variables and require the
vault password to read or modify.
