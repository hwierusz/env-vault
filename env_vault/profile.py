"""Profile support: named sets of variables within a vault (e.g. dev, staging, prod)."""

from __future__ import annotations

from typing import Dict, List, Optional

from env_vault.storage import load_vault, save_vault

_PROFILES_KEY = "__profiles__"


class ProfileError(Exception):
    pass


def _get_profiles(data: dict) -> Dict[str, Dict[str, str]]:
    return data.get(_PROFILES_KEY, {})


def list_profiles(vault_name: str, password: str) -> List[str]:
    """Return names of all profiles in the vault."""
    data = load_vault(vault_name, password)
    return sorted(_get_profiles(data).keys())


def set_profile_var(vault_name: str, password: str, profile: str, key: str, value: str) -> None:
    """Set a variable inside a named profile."""
    if not profile:
        raise ProfileError("Profile name must not be empty.")
    data = load_vault(vault_name, password)
    profiles = _get_profiles(data)
    profiles.setdefault(profile, {})[key] = value
    data[_PROFILES_KEY] = profiles
    save_vault(vault_name, password, data)


def get_profile_var(vault_name: str, password: str, profile: str, key: str) -> Optional[str]:
    """Get a variable from a named profile, or None if absent."""
    data = load_vault(vault_name, password)
    return _get_profiles(data).get(profile, {}).get(key)


def get_profile(vault_name: str, password: str, profile: str) -> Dict[str, str]:
    """Return all variables for a profile."""
    data = load_vault(vault_name, password)
    profiles = _get_profiles(data)
    if profile not in profiles:
        raise ProfileError(f"Profile '{profile}' does not exist.")
    return dict(profiles[profile])


def delete_profile(vault_name: str, password: str, profile: str) -> int:
    """Delete an entire profile. Returns number of variables removed."""
    data = load_vault(vault_name, password)
    profiles = _get_profiles(data)
    if profile not in profiles:
        raise ProfileError(f"Profile '{profile}' does not exist.")
    count = len(profiles.pop(profile))
    data[_PROFILES_KEY] = profiles
    save_vault(vault_name, password, data)
    return count
