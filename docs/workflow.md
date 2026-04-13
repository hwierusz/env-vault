# Workflow

The **workflow** feature lets you define and run ordered sequences of built-in
operations against a vault in a single command.

## Concepts

| Term | Description |
|---|---|
| **Step** | A named transformation applied to the full set of vault variables. |
| **Workflow** | An ordered list of steps executed in sequence. |
| **Registry** | The dictionary of available steps. |

## Built-in Steps

| Step name | Description |
|---|---|
| `strip_empty` | Remove all keys whose value is empty or whitespace-only. |
| `uppercase_keys` | Convert every key name to uppercase. |
| `strip_whitespace` | Strip leading/trailing whitespace from all values. |

## CLI Usage

### List available steps

```bash
env-vault workflow list
```

### Run a workflow

```bash
env-vault workflow run <vault> <step1> [step2 ...] --password <pwd>
```

Steps are executed left-to-right. The vault is updated in-place after all
steps complete successfully.

#### Options

| Option | Description |
|---|---|
| `--dry-run` | Preview the result without saving to the vault. |
| `--no-stop` | Continue executing subsequent steps even if one fails. |

### Examples

```bash
# Clean up a vault: strip whitespace then remove empty keys
env-vault workflow run myapp strip_whitespace strip_empty --password secret

# Normalise key casing without committing changes
env-vault workflow run myapp uppercase_keys --password secret --dry-run

# Run all three built-in steps, ignoring individual errors
env-vault workflow run myapp strip_whitespace strip_empty uppercase_keys \
  --password secret --no-stop
```

## Python API

```python
from env_vault.workflow import build_workflow, run_workflow, DEFAULT_REGISTRY

vars_ = {"db_host": "  localhost  ", "empty_key": ""}
steps = build_workflow(["strip_whitespace", "strip_empty", "uppercase_keys"], DEFAULT_REGISTRY)
result = run_workflow(vars_, steps)

print(result.success)     # True
print(result.vars_after)  # {'DB_HOST': 'localhost'}
print(result.steps_run)   # ['strip_whitespace', 'strip_empty', 'uppercase_keys']
```

## Error Handling

- `WorkflowError` is raised by `build_workflow` when an unknown step name is
  requested.
- Individual step exceptions are caught by `run_workflow` and recorded in
  `WorkflowResult.errors`. Pass `stop_on_error=False` to continue after a
  failing step.
