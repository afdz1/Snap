"""
addon_installer.py
Compares the bundled Snap addon version against what is installed in WoW.
Installs or updates the addon automatically on every launch.
Works both when running from source and when frozen by PyInstaller.
"""

import os
import shutil
import sys

_ADDON_NAME = "Snap"


# ── Path helpers ──────────────────────────────────────────────────────────────

def _bundled_addon_path() -> str:
    """
    When frozen (exe): addon/ is extracted to sys._MEIPASS/addon/
    When running from source: addon/ lives one level above companion/
    """
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "addon")
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "addon"))


_WOW_FLAVOURS = ("_retail_", "_classic_era_", "_classic_", "_ptr_", "_xptr_")


def _installed_addon_path(screenshots_folder: str, wow_exe: str = "") -> str:
    """
    Derives the WoW AddOns directory.

    Priority:
      1. From screenshots_folder  (…/_retail_/Screenshots → …/_retail_/Interface/AddOns/Snap/)
      2. From wow_exe location    (scan for the first flavour subfolder that exists)
    """
    if screenshots_folder and os.path.isdir(screenshots_folder):
        retail_dir = os.path.normpath(os.path.join(screenshots_folder, ".."))
        return os.path.join(retail_dir, "Interface", "AddOns", _ADDON_NAME)

    if wow_exe and os.path.isfile(wow_exe):
        wow_dir = os.path.dirname(os.path.normpath(wow_exe))
        for flavour in _WOW_FLAVOURS:
            flavour_dir = os.path.join(wow_dir, flavour)
            if os.path.isdir(flavour_dir):
                return os.path.join(flavour_dir, "Interface", "AddOns", _ADDON_NAME)
        # Fallback: use _retail_ even if it doesn't exist yet
        return os.path.join(wow_dir, "_retail_", "Interface", "AddOns", _ADDON_NAME)

    return ""


# ── Version reader ────────────────────────────────────────────────────────────

def _read_toc_version(toc_path: str) -> str:
    """Returns the ## Version: value from a .toc file, or '0.0.0' if absent."""
    try:
        with open(toc_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("## Version:"):
                    return line.split(":", 1)[1].strip()
    except FileNotFoundError:
        pass
    return "0.0.0"


# ── Public API ────────────────────────────────────────────────────────────────

def check_and_install(screenshots_folder: str, wow_exe: str = "") -> str | None:
    """
    Installs or updates the bundled addon into the WoW AddOns folder.

    Returns a human-readable log message when an install/update was performed,
    or None when the installed addon is already up to date.
    Requires at least one of screenshots_folder or wow_exe to be set.
    """
    if not screenshots_folder and not wow_exe:
        return None

    bundled_dir   = _bundled_addon_path()
    installed_dir = _installed_addon_path(screenshots_folder, wow_exe)

    if not installed_dir:
        return None

    bundled_toc   = os.path.join(bundled_dir,   f"{_ADDON_NAME}.toc")
    installed_toc = os.path.join(installed_dir, f"{_ADDON_NAME}.toc")

    bundled_ver   = _read_toc_version(bundled_toc)
    installed_ver = _read_toc_version(installed_toc)

    if bundled_ver == installed_ver and os.path.isdir(installed_dir):
        return None  # already up to date

    action = "Updated" if os.path.isdir(installed_dir) else "Installed"

    # Wipe existing installation before copying fresh files
    if os.path.isdir(installed_dir):
        shutil.rmtree(installed_dir)
    shutil.copytree(bundled_dir, installed_dir)

    return f"Snap addon {action.lower()} → v{bundled_ver}  ({installed_dir})"

