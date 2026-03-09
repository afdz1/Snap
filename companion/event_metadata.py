"""
event_metadata.py
Extracts event information from screenshots to determine what triggered the recording.

The WoW addon can communicate event context via multiple methods:
1. Metadata JSON file (screenshot_name.json) - Preferred method
2. Filename encoding (screenshot_name_EVENTTYPE.jpg) - Fallback
3. SavedVariables (Snap.lua) - Event queue
4. Combat log correlation - Last resort fallback
"""

import os
import json
import re
from datetime import datetime
from typing import Optional

# Event types the addon can trigger
EVENT_TYPES = {
    "DEATH": "💀 Death",
    "BOSS_KILL": "⚔ Boss Kill",
    "ACHIEVEMENT": "🏆 Achievement",
    "LEVEL_UP": "⬆ Level Up",
    "PVP_KILL": "⚔ PvP Kill",
    "CHALLENGE_MODE": "🏅 Challenge Mode",
    "LOOT": "💎 Loot",
    "QUEST_COMPLETE": "📜 Quest Complete",
    "CUSTOM": "📸 Custom",
}

# Filename patterns for event encoding
# Format: WoWScrnShot_MMDDYY_HHMMSS_EVENTTYPE.jpg
_FILENAME_EVENT_PATTERN = re.compile(r'_([A-Z_]+)\.(jpg|jpeg|png|tga)$', re.IGNORECASE)


def _parse_metadata_file(screenshot_path: str) -> Optional[dict]:
    """
    Reads event metadata from a JSON file with the same name as the screenshot.
    Expected format: screenshot_name.json
    
    JSON structure:
    {
        "event_type": "DEATH",
        "event_name": "Player Death",
        "details": "Killed by Boss Name",
        "timestamp": 1234567890,
        "player_name": "CharacterName",
        "realm": "RealmName"
    }
    """
    base_name = os.path.splitext(screenshot_path)[0]
    metadata_path = base_name + ".json"
    
    if not os.path.isfile(metadata_path):
        return None
    
    try:
        with open(metadata_path, encoding="utf-8") as f:
            data = json.load(f)
            # Validate required fields
            if "event_type" in data:
                return data
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    
    return None


def _parse_filename_encoding(screenshot_path: str) -> Optional[dict]:
    """
    Extracts event type from filename if encoded.
    Format: WoWScrnShot_MMDDYY_HHMMSS_EVENTTYPE.jpg
    """
    filename = os.path.basename(screenshot_path)
    match = _FILENAME_EVENT_PATTERN.search(filename)
    
    if match:
        event_code = match.group(1)
        # Normalize event codes (handle variations)
        event_code = event_code.upper()
        
        # Map common variations
        event_map = {
            "DEATH": "DEATH",
            "BOSS": "BOSS_KILL",
            "BOSSKILL": "BOSS_KILL",
            "ACHIEVEMENT": "ACHIEVEMENT",
            "ACH": "ACHIEVEMENT",
            "LEVEL": "LEVEL_UP",
            "LEVELUP": "LEVEL_UP",
            "PVP": "PVP_KILL",
            "PVPKILL": "PVP_KILL",
            "M+": "CHALLENGE_MODE",
            "CHALLENGEMODE": "CHALLENGE_MODE",
            "LOOT": "LOOT",
            "QUEST": "QUEST_COMPLETE",
        }
        
        event_type = event_map.get(event_code, event_code)
        
        return {
            "event_type": event_type,
            "event_name": EVENT_TYPES.get(event_type, event_type),
            "source": "filename",
        }
    
    return None


def _parse_saved_variables(screenshots_folder: str, screenshot_timestamp: float) -> Optional[dict]:
    """
    Reads event queue from Snap.lua SavedVariables.
    Matches events by timestamp (within 5 second window).
    
    Expected SavedVariables structure:
    SnapEventQueue = {
        [1] = {
            ["event_type"] = "DEATH",
            ["event_name"] = "Player Death",
            ["timestamp"] = 1234567890,
            ["details"] = "Killed by Boss",
        },
        ...
    }
    """
    # Import here to avoid circular dependency
    from character import _wtf_account_dir, _latest_account_folder
    
    account_dir = _wtf_account_dir(screenshots_folder)
    if not account_dir:
        return None
    
    acct = _latest_account_folder(account_dir)
    if not acct:
        return None
    
    lua_path = os.path.join(acct, "SavedVariables", "Snap.lua")
    if not os.path.isfile(lua_path):
        return None
    
    try:
        with open(lua_path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return None
    
    # Parse SnapEventQueue table
    queue_match = re.search(
        r'SnapEventQueue\s*=\s*\{([^}]+)\}', content, re.DOTALL
    )
    if not queue_match:
        return None
    
    # Find events within timestamp window (5 seconds)
    window = 5.0
    for entry_match in re.finditer(
        r'\[(\d+)\]\s*=\s*\{([^}]+)\}',
        queue_match.group(1),
        re.DOTALL
    ):
        entry_content = entry_match.group(2)
        
        # Extract timestamp
        ts_match = re.search(r'\["timestamp"\]\s*=\s*(\d+)', entry_content)
        if not ts_match:
            continue
        
        event_ts = float(ts_match.group(1))
        time_diff = abs(screenshot_timestamp - event_ts)
        
        if time_diff <= window:
            # Extract event data
            event_type_match = re.search(r'\["event_type"\]\s*=\s*"([^"]+)"', entry_content)
            event_name_match = re.search(r'\["event_name"\]\s*=\s*"([^"]+)"', entry_content)
            details_match = re.search(r'\["details"\]\s*=\s*"([^"]*)"', entry_content)
            
            return {
                "event_type": event_type_match.group(1) if event_type_match else "CUSTOM",
                "event_name": event_name_match.group(1) if event_name_match else "",
                "details": details_match.group(1) if details_match else "",
                "source": "saved_variables",
            }
    
    return None


def _correlate_combat_log(screenshots_folder: str, screenshot_timestamp: float) -> Optional[dict]:
    """
    Fallback: Correlate screenshot with combat log events by timestamp.
    Uses existing combat_log.py functionality.
    """
    # Import here to avoid circular dependency
    from combat_log import check_for_deaths
    
    # Check for deaths within 3 seconds
    deaths = check_for_deaths(screenshots_folder, window_secs=3.0, players_only=True)
    
    if deaths:
        # Use the most recent death
        name, age = deaths[0]
        return {
            "event_type": "DEATH",
            "event_name": "Player Death",
            "details": f"{name} has fallen",
            "source": "combat_log",
        }
    
    return None


def get_event_info(screenshot_path: str, screenshots_folder: str) -> dict:
    """
    Extracts event information from a screenshot using multiple methods.
    
    Returns a dict with:
    {
        "event_type": "DEATH",           # Event code
        "event_name": "💀 Death",        # Human-readable name
        "details": "Killed by Boss",    # Additional context
        "source": "metadata_file",       # Detection method used
    }
    
    Falls back through methods in order:
    1. Metadata JSON file
    2. Filename encoding
    3. SavedVariables event queue
    4. Combat log correlation
    """
    screenshot_timestamp = os.path.getmtime(screenshot_path)
    
    # Method 1: Metadata JSON file (preferred)
    metadata = _parse_metadata_file(screenshot_path)
    if metadata:
        event_type = metadata.get("event_type", "CUSTOM")
        return {
            "event_type": event_type,
            "event_name": metadata.get("event_name") or EVENT_TYPES.get(event_type, event_type),
            "details": metadata.get("details", ""),
            "source": "metadata_file",
        }
    
    # Method 2: Filename encoding
    metadata = _parse_filename_encoding(screenshot_path)
    if metadata:
        return metadata
    
    # Method 3: SavedVariables event queue
    metadata = _parse_saved_variables(screenshots_folder, screenshot_timestamp)
    if metadata:
        event_type = metadata.get("event_type", "CUSTOM")
        metadata["event_name"] = metadata.get("event_name") or EVENT_TYPES.get(event_type, event_type)
        return metadata
    
    # Method 4: Combat log correlation (fallback)
    metadata = _correlate_combat_log(screenshots_folder, screenshot_timestamp)
    if metadata:
        return metadata
    
    # No event detected
    return {
        "event_type": "UNKNOWN",
        "event_name": "📸 Screenshot",
        "details": "",
        "source": "none",
    }


def enhance_event_info_with_video(event_info: dict, video_path: str) -> dict:
    """
    Enhances event information by analyzing the video content.
    
    This is called AFTER the video is captured, allowing video analysis
    to confirm or override event detection from other methods.
    
    Args:
        event_info: Existing event info dict
        video_path: Path to video file
    
    Returns:
        Updated event_info dict (may be modified or unchanged)
    """
    # Only analyze video if event is unknown or we want to confirm
    if event_info.get("event_type") == "UNKNOWN" or event_info.get("source") == "none":
        try:
            from video_analysis import analyze_video_for_events
            video_event = analyze_video_for_events(video_path)
            
            if video_event:
                # Video analysis found an event - use it
                return video_event
        except ImportError:
            # video_analysis module not available (optional dependency)
            pass
        except Exception:
            # Video analysis failed - keep original event info
            pass
    
    # If event already detected, optionally verify with video analysis
    # (This can be enabled for higher confidence)
    if event_info.get("event_type") == "DEATH":
        try:
            from video_analysis import detect_death_in_video
            video_death = detect_death_in_video(video_path)
            
            if video_death:
                # Video confirms death - enhance with confidence score
                event_info["video_confirmed"] = True
                event_info["confidence"] = video_death.get("confidence", 1.0)
        except (ImportError, Exception):
            pass
    
    return event_info


def format_event_caption(event_info: dict, player_info: dict) -> str:
    """
    Formats a Discord-ready caption combining event info and player info.
    
    Examples:
    - "💀" (death - only emoji)
    - "⚔ Boss Kill — Ragnaros defeated — Ivokir — Hyjal"
    - "🏆 Achievement — Loremaster — Ivokir — Hyjal"
    """
    event_type = event_info.get("event_type", "UNKNOWN")
    
    # For death events, only show the skull emoji
    if event_type == "DEATH":
        return "💀"
    
    # For other events, show full caption
    event_name = event_info.get("event_name", "📸 Screenshot")
    details = event_info.get("details", "").strip()
    
    # Build player string
    player_name = player_info.get("name", "").strip()
    realm = player_info.get("realm", "").strip()
    player_str = f"{player_name} — {realm}" if (player_name and realm) else (player_name or "")
    
    # Combine parts
    parts = [event_name]
    if details:
        parts.append(details)
    if player_str:
        parts.append(player_str)
    
    return " — ".join(parts)

