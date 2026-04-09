# env-vault

> CLI tool for managing environment variables across multiple projects with encrypted storage

---

## Installation

```bash
pip install env-vault
```

Or with pipx (recommended):

```bash
pipx install env-vault
```

---

## Usage

Initialize a new vault for your project:

```bash
# Initialize env-vault in your project
env-vault init

# Add an environment variable
env-vault set MY_PROJECT API_KEY=supersecret123

# Retrieve and export variables for a project
env-vault load MY_PROJECT

# List all stored projects
env-vault list
```

Variables are encrypted at rest using AES-256 and stored in `~/.env-vault/`. Each project maintains its own isolated namespace, and secrets are never written to disk in plaintext.

---

## How It Works

- **Encrypted storage** — All secrets are encrypted before being saved locally
- **Multi-project support** — Manage separate variable sets per project
- **Shell integration** — Use `eval $(env-vault load PROJECT)` to export variables directly into your shell session

---

## Requirements

- Python 3.8+
- `cryptography` >= 41.0

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Contributions welcome! Please open an issue or pull request on GitHub.*