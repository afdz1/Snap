"""
combat_log.py
Reads the tail of WoWCombatLog.txt and detects death events near a given time.

WoW combat log line format:
    M/D HH:MM:SS.mmm  EVENT,field1,field2,...

UNIT_DIED example:
    3/6 23:04:47.123  UNIT_DIED,0x0000000000000000,"Shocklates-Hyjal",0x511,0x0,12345,nil
"""

import os
from datetime import datetime

_TAIL_BYTES = 32_768   # 32 KB — plenty for several seconds of log events


def _log_path(screenshots_folder: str) -> str:
    """Find the most recently modified WoWCombatLog*.txt in the Logs folder.

    WoW now names files with a timestamp: WoWCombatLog-030626_015421.txt
    We pick whichever matching file was modified most recently.
    Falls back to the plain 'WoWCombatLog.txt' name for older clients.
    """
    logs_dir = os.path.normpath(os.path.join(screenshots_folder, "..", "Logs"))
    if not os.path.isdir(logs_dir):
        return os.path.join(logs_dir, "WoWCombatLog.txt")  # doesn't exist — caller handles

    candidates = [
        os.path.join(logs_dir, f)
        for f in os.listdir(logs_dir)
        if f.startswith("WoWCombatLog") and f.endswith(".txt")
    ]
    if not candidates:
        return os.path.join(logs_dir, "WoWCombatLog.txt")

    return max(candidates, key=os.path.getmtime)


def _line_timestamp_secs(line: str) -> float | None:
    """Parse the leading timestamp of a combat log line → seconds since midnight.

    Handles both formats:
      Old: "3/6 23:04:47.123  ..."          (no year, no timezone)
      New: "3/6/2026 03:23:55.118-5  ..."   (year + UTC offset)
    """
    try:
        ts_part  = line.split("  ")[0].strip()   # everything before the double-space
        time_str = ts_part.split(" ")[-1]         # last token: "HH:MM:SS.mmm" or "HH:MM:SS.mmm-5"
        time_str = time_str.split("-")[0].split("+")[0]  # strip UTC offset
        t = datetime.strptime(time_str, "%H:%M:%S.%f")
        return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1_000_000
    except Exception:
        return None


def _is_player_guid(guid: str) -> bool:
    """
    New log format includes the dest GUID (field index 5).
    Player GUIDs start with 'Player-'; creature GUIDs start with 'Creature-'.
    """
    return guid.startswith("Player-")


def check_for_deaths(
    screenshots_folder: str,
    window_secs: float = 3.0,
    players_only: bool = True,
) -> list[tuple[str, float]]:
    """
    Read the tail of WoWCombatLog.txt and return a list of (name, age_secs) tuples
    for units that died within the last `window_secs` seconds relative to now.

    Returns [] if the log doesn't exist or combat logging is disabled.
    Each name is stripped of the realm suffix (e.g. "Shocklates-Hyjal" → "Shocklates").
    age_secs is how many seconds ago the death occurred.
    """
    log_path = _log_path(screenshots_folder)
    if not os.path.isfile(log_path):
        return []

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - _TAIL_BYTES))
            lines = fh.read().splitlines()
    except Exception:
        return []

    now = datetime.now()
    now_secs = now.hour * 3600 + now.minute * 60 + now.second + now.microsecond / 1_000_000

    deaths: list[str] = []
    for line in lines:
        if "UNIT_DIED" not in line:
            continue
        ts = _line_timestamp_secs(line)
        if ts is None:
            continue

        # Handle midnight rollover (e.g. event at 23:59, now is 00:00)
        age = now_secs - ts
        if age < 0:
            age += 86_400

        if age > window_secs:
            continue

        # New format: UNIT_DIED,srcGUID,srcName,srcFlags,srcRaidFlags,destGUID,"destName",destFlags,...
        # destGUID = fields[5], destName = fields[6]
        try:
            payload  = line.split("  ", 1)[1]          # drop timestamp
            fields   = payload.split(",")
            dest_guid = fields[5].strip('"')            # e.g. "Player-123-ABC" or "Creature-..."
            raw_name  = fields[6].strip('"')            # e.g. "Shocklates-Hyjal"
            name      = raw_name.split("-")[0]          # strip realm → "Shocklates"
        except Exception:
            continue

        if players_only and not _is_player_guid(dest_guid):
            continue

        if not any(d[0] == name for d in deaths):
            deaths.append((name, age))

    return deaths


def death_caption(deaths: list[tuple[str, float]]) -> str:
    """Format a Discord-ready death notification string."""
    if not deaths:
        return ""
    names = ", ".join(n for n, _ in deaths)
    if len(deaths) == 1:
        return f"💀 **{names} has fallen!**"
    return f"💀 **{names} have fallen!**"

