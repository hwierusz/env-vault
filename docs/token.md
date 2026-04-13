# Token-Based Access Management

env-vault supports issuing short-lived access tokens that grant read access to
a specific subset of vault variables. This is useful for CI pipelines, scripts,
or third-party integrations that should only see certain keys.

## Concepts

- **Token**: A 64-character hex string generated with `secrets.token_hex`.
- **Label**: A human-readable name for the token (e.g. `ci-pipeline`).
- **Allowed keys**: The list of vault variable names the token can resolve.
- **TTL**: Time-to-live in seconds. After expiry the token cannot be resolved.

## CLI Usage

### Issue a token

```bash
env-vault token issue myvault ci DB_URL API_KEY --ttl 7200
```

Outputs the full 64-character token. Store it securely — it is not shown again.

### Resolve a token

```bash
env-vault token resolve myvault <token>
# or as JSON
env-vault token resolve myvault <token> --format json
```

Returns the key/value pairs the token is authorised to read. Raises an error if
the token has expired.

### Revoke a token

```bash
env-vault token revoke myvault <token>
```

### List tokens

```bash
env-vault token list myvault
```

Shows truncated token values, labels, allowed keys, and expiry status.

### Purge expired tokens

```bash
env-vault token purge myvault
```

Removes all expired tokens from the vault and saves it.

## Python API

```python
from env_vault.token import issue_token, resolve_token, revoke_token

data = load_vault("myvault", password)
token = issue_token(data, label="ci", allowed_keys=["DB_URL"], ttl_seconds=3600)
save_vault("myvault", password, data)

# Later:
result = resolve_token(data, token)  # {"DB_URL": "..."}
```

## Errors

| Situation | Exception |
|---|---|
| Key not in vault | `TokenError` |
| Token not found | `TokenError` |
| Token expired | `TokenError` |
| TTL ≤ 0 | `TokenError` |
| Empty allowed_keys | `TokenError` |
