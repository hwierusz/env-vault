# Vault Inheritance

Vault inheritance lets you define a chain of vaults where variables in
"child" vaults override those in "parent" vaults — similar to how
environment variables work in shell profiles or Docker layers.

## Concepts

| Term | Meaning |
|------|---------|
| **Child vault** | Highest-priority vault (index 0 in the chain). |
| **Parent vault** | Lower-priority vault consulted when a key is absent in the child. |
| **Depth** | Position of the vault in the chain (0 = child). |

## Python API

```python
from env_vault.inherit import resolve_inherited, inherit_all
from env_vault.storage import load_vault, vault_exists

# Resolve a single key
result = resolve_inherited(
    key="DATABASE_URL",
    vaults=["myapp-prod", "myapp-base", "global-defaults"],
    load_fn=load_vault,
    exists_fn=vault_exists,
    password="s3cr3t",
)
print(result.value, result.source_vault, result.depth)

# Merge all variables (child wins)
merged = inherit_all(
    vaults=["myapp-prod", "myapp-base"],
    load_fn=load_vault,
    exists_fn=vault_exists,
    password="s3cr3t",
)
for key, r in merged.items():
    print(f"{key}={r.value}  # from {r.source_vault}")
```

## CLI

### Resolve a single key

```bash
env-vault inherit resolve DATABASE_URL \
  --vault myapp-prod \
  --vault myapp-base \
  --vault global-defaults
```

Output:
```
DATABASE_URL=postgres://...  (from 'myapp-prod', depth 0)
```

Add `--json` for machine-readable output:
```bash
env-vault inherit resolve DATABASE_URL --vault myapp-prod --vault global-defaults --json
```

### Show merged variables

```bash
env-vault inherit show \
  --vault myapp-prod \
  --vault global-defaults
```

Output:
```
API_KEY=abc123  (from 'myapp-prod', depth 0)
DATABASE_URL=postgres://...  (from 'global-defaults', depth 1)
LOG_LEVEL=info  (from 'global-defaults', depth 1)
```

## Error handling

`InheritError` is raised when:

- No vaults are provided.
- A vault in the chain does not exist.
- The requested key is absent from every vault in the chain.
