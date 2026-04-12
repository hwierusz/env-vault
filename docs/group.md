# Variable Groups

The **group** feature lets you organise vault variables into named groups for easier bulk operations and documentation.

## Concepts

- A **group** is a named list of variable keys stored inside the vault under the reserved `__groups__` metadata key.
- Groups do **not** copy values — they reference existing keys in the vault.
- Deleting a variable from the vault does not automatically remove it from groups; use `group remove` first.

## CLI Usage

### Add a key to a group

```bash
env-vault group add <vault> <group> <key>
```

### Remove a key from a group

```bash
env-vault group remove <vault> <group> <key>
```

### List all groups

```bash
env-vault group list <vault>
```

### Show group members and their values

```bash
env-vault group show <vault> <group>
```

### Delete an entire group

```bash
env-vault group delete <vault> <group>
```

## Python API

```python
from env_vault.group import (
    add_to_group,
    remove_from_group,
    list_groups,
    get_group_members,
    get_vars_for_group,
    delete_group,
)

# data is the decrypted vault dict
add_to_group(data, "database", "DB_URL")
add_to_group(data, "database", "DB_PORT")

print(list_groups(data))          # ['database']
print(get_group_members(data, "database"))  # ['DB_URL', 'DB_PORT']
print(get_vars_for_group(data, "database")) # {'DB_URL': '...', 'DB_PORT': '...'}

remove_from_group(data, "database", "DB_PORT")
delete_group(data, "database")
```

## Errors

| Situation | Exception |
|---|---|
| Key not in vault | `GroupError` |
| Empty group name | `GroupError` |
| Group not found | `GroupError` |
| Key not in group | `GroupError` |
