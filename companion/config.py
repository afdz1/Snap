"""
config.py
Loads and saves companion settings to config.json next to this file.
"""

import json
import os

_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULTS = {
    "screenshots_folder": r"C:\Program Files (x86)\World of Warcraft\_retail_\Screenshots",
    "nvidia_video_folder": os.path.join(os.path.expanduser("~"), "Videos"),
    "hotkey": "alt+f10",
    "post_event_delay": 3,    # seconds to wait before triggering Save Replay
    "clip_duration": 10,      # seconds to extract (tail of saved replay)
    "launch_on_startup": True, # default on; persisted so unchecking is remembered
    # Discord credentials — set via Settings dialog; saved to config.json (gitignored).
    # CI builds override these by baking bot_secrets.py into the exe via GitHub Secrets.
    "discord_bot_token": "",
    "discord_channel_id": "",
}


def load() -> dict:
    if os.path.exists(_CONFIG_FILE):
        with open(_CONFIG_FILE, "r") as f:
            data = json.load(f)
        for key, value in DEFAULTS.items():
            data.setdefault(key, value)
        return data
    return dict(DEFAULTS)


def save(cfg: dict) -> None:
    with open(_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

