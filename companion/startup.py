"""
startup.py
Manages the Windows registry entry that launches Snap on user login.
Uses HKEY_CURRENT_USER — no administrator rights required.
"""

import os
import sys
import winreg

_APP_NAME = "SnapCompanion"
_REG_PATH  = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _launch_cmd() -> str:
    """
    Returns the command string to register.
    Supports both running as a .py script and as a compiled .exe.
    """
    if getattr(sys, "frozen", False):
        # Compiled with PyInstaller / cx_Freeze
        return f'"{sys.executable}"'
    else:
        script = os.path.abspath(os.path.join(os.path.dirname(__file__), "main.py"))
        return f'"{sys.executable}" "{script}"'


def enable() -> None:
    """Adds the registry key so Snap starts on login."""
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE
    )
    winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, _launch_cmd())
    winreg.CloseKey(key)


def disable() -> None:
    """Removes the registry key."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, _APP_NAME)
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass  # already absent


def is_enabled() -> bool:
    """Returns True if the startup registry key exists."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ
        )
        winreg.QueryValueEx(key, _APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

