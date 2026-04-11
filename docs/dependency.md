# Variable Dependency Tracking

env-vault can track logical dependencies between variables stored in a vault.
This is useful when one variable's value is derived from or must be set after another.

## Concepts

- **Dependency**: `KEY` depends on `DEPENDS_ON` means `DEPENDS_ON` should be
  resolved/set before `KEY`.
- **Topological order**: `dep order` prints variables sorted so that each
  variable appears after all of its dependencies.
- **Cycle detection**: Adding a dependency that would create a circular chain
  raises an error at resolution time.

## CLI Usage

```bash
# Record that DATABASE_URL depends on DB_HOST
env-vault dep add myproject DATABASE_URL DB_HOST

# List what DATABASE_URL depends on
env-vault dep list myproject DATABASE_URL

# Remove a dependency
env-vault dep remove myproject DATABASE_URL DB_HOST

# Print all variables in dependency order
env-vault dep order myproject
```

## Python API

```python
from env_vault.storage import load_vault, save_vault
from env_vault.dependency import (
    add_dependency,
    remove_dependency,
    list_dependencies,
    dependents_of,
    resolve_order,
)

data = load_vault("myproject", password)
add_dependency(data, "DATABASE_URL", "DB_HOST")
save_vault("myproject", password, data)

order = resolve_order(data)  # topologically sorted list
```

## Storage Format

Dependencies are stored inside the vault under the `__dependencies__` key:

```json
{
  "vars": { "DB_HOST": "localhost", "DATABASE_URL": "postgres://..." },
  "__dependencies__": {
    "DATABASE_URL": ["DB_HOST"]
  }
}
```

This section is encrypted along with the rest of the vault data.
