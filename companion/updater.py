"""
updater.py
Silently checks GitHub Releases for a newer version on startup.
Downloads the update in a background thread and applies it via a
batch script on the next app exit — no user interaction required.
"""

import json
import os
import sys
import threading
import urllib.request
from version import __version__

# ── Config ────────────────────────────────────────────────────────────────────
GITHUB_REPO = "afdz1/snap"   # TODO: update before first release
_API_URL    = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# State
_update_pending  = False
_new_exe_path: str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_version(tag: str) -> tuple[int, ...]:
    return tuple(int(x) for x in tag.lstrip("v").split("."))


def _current_exe() -> str | None:
    """Returns the path to the running exe, or None if running as a script."""
    return sys.executable if getattr(sys, "frozen", False) else None


# ── Public API ────────────────────────────────────────────────────────────────

def check_and_download(on_update_ready=None) -> None:
    """
    Spawns a daemon thread that:
      1. Queries the GitHub Releases API.
      2. Compares the latest tag against the current version.
      3. Downloads the new exe if a newer version is available.
      4. Calls on_update_ready(message) when the download completes.
    """
    def _run():
        global _update_pending, _new_exe_path
        if _update_pending:
            return  # already downloaded — nothing to do until next restart
        try:
            req = urllib.request.Request(_API_URL, headers={"User-Agent": "Snap-Updater"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            latest_tag = data.get("tag_name", "")
            if not latest_tag:
                return
            if _parse_version(latest_tag) <= _parse_version(__version__):
                return

            # Find the exe asset in the release
            assets   = data.get("assets", [])
            exe_url  = next(
                (a["browser_download_url"] for a in assets if a["name"].endswith(".exe")),
                None,
            )
            if not exe_url:
                return

            # Download next to the current exe
            exe_dir  = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else sys.argv[0])
            dest     = os.path.join(exe_dir, "Snap_update.exe")
            urllib.request.urlretrieve(exe_url, dest)

            _update_pending = True
            _new_exe_path   = dest
            if on_update_ready:
                on_update_ready(f"Update {latest_tag} downloaded — will apply on next restart.")

        except Exception:
            pass  # silently skip if offline or API unavailable

    threading.Thread(target=_run, daemon=True).start()


def apply_on_exit() -> None:
    """
    Call this just before the app quits. If an update was downloaded,
    writes a batch script that replaces the exe and restarts the app.
    Only has any effect when running as a frozen exe.
    """
    if not _update_pending or not _new_exe_path:
        return
    current = _current_exe()
    if not current:
        return

    bat = os.path.join(os.path.dirname(current), "_snap_update.bat")
    with open(bat, "w") as f:
        f.write(
            f"@echo off\n"
            f"timeout /t 2 /nobreak > nul\n"
            f'move /y "{_new_exe_path}" "{current}"\n'
            f'start "" "{current}"\n'
            f'del "%~f0"\n'
        )
    os.startfile(bat)


def is_pending() -> bool:
    return _update_pending

