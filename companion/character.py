"""
character.py
Reads the active player's name and realm from the Snap addon's SavedVariables.

WoW writes this file on logout / /reload:
  <wow_retail>\\WTF\\Account\\<ACCOUNT_NAME>\\SavedVariables\\Snap.lua

The file contains:
  SnapCurrentCharacter = {
      ["name"]  = "Ivokir",
      ["realm"] = "Hyjal",
      ["class"] = "EVOKER",
      ["time"]  = 1772779737,
  }

The account folder with the most recent modification time is used so that
the companion always reflects the last character that logged out.
"""

import os
import re


# ── Path helpers ──────────────────────────────────────────────────────────────

def _wtf_account_dir(screenshots_folder: str) -> str | None:
    """Derives WTF/Account path from the configured Screenshots folder."""
    retail = os.path.normpath(os.path.join(screenshots_folder, ".."))
    path   = os.path.join(retail, "WTF", "Account")
    return path if os.path.isdir(path) else None


def _latest_account_folder(account_dir: str) -> str | None:
    """Returns the account sub-folder modified most recently."""
    try:
        folders = [e for e in os.scandir(account_dir) if e.is_dir()]
        if not folders:
            return None
        return max(folders, key=lambda e: e.stat().st_mtime).path
    except OSError:
        return None


# ── Lua parser ────────────────────────────────────────────────────────────────

def _parse_snap_lua(lua_path: str) -> dict:
    """
    Extracts the SnapCurrentCharacter table from a SavedVariables Snap.lua.
    Returns a dict of string → string, or {} on any failure.
    """
    try:
        with open(lua_path, encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return {}

    # Capture everything between the outer braces of SnapCurrentCharacter
    block_m = re.search(
        r'SnapCurrentCharacter\s*=\s*\{([^}]+)\}', content, re.DOTALL
    )
    if not block_m:
        return {}

    result: dict[str, str] = {}
    # Match  ["key"] = "value"  or  ["key"] = 123
    for m in re.finditer(r'\["(\w+)"\]\s*=\s*"?([^",\n\}]+)"?', block_m.group(1)):
        result[m.group(1)] = m.group(2).strip().strip('"')
    return result


# ── Public API ────────────────────────────────────────────────────────────────

def get_player_info(screenshots_folder: str) -> dict:
    """
    Returns a dict like {"name": "Ivokir", "realm": "Hyjal", "class": "EVOKER"}
    by reading the most recently modified WTF account's SavedVariables/Snap.lua.
    Returns {} when the file cannot be found or parsed.
    """
    account_dir = _wtf_account_dir(screenshots_folder)
    if not account_dir:
        return {}

    acct = _latest_account_folder(account_dir)
    if not acct:
        return {}

    lua_path = os.path.join(acct, "SavedVariables", "Snap.lua")
    return _parse_snap_lua(lua_path)


def format_caption(info: dict) -> str:
    """
    Builds the Discord message caption from a player info dict.
    Examples:
      {"name": "Ivokir", "realm": "Hyjal"}  →  "Ivokir — Hyjal"
      {"name": "Ivokir"}                     →  "Ivokir"
      {}                                     →  ""
    """
    name  = info.get("name", "").strip()
    realm = info.get("realm", "").strip()
    if not name:
        return ""
    return f"{name} — {realm}" if realm else name

