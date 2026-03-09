# Event Metadata Implementation Summary

## Problem Solved
The companion app (Snap.exe) couldn't tell which event triggered each screenshot. All clips had generic captions like "Player — Realm" instead of contextual captions like "💀 Death — Player — Realm" or "⚔ Boss Kill — Ragnaros defeated — Player — Realm".

## Solution Implemented

### 1. New Module: `companion/event_metadata.py`
A robust event detection system that tries multiple methods (in order):
1. **Metadata JSON file** - Addon creates `screenshot_name.json` with event info
2. **Filename encoding** - Event type encoded in filename (`_DEATH`, `_BOSS_KILL`, etc.)
3. **SavedVariables queue** - Events stored in `Snap.lua`, correlated by timestamp
4. **Combat log correlation** - Automatic fallback using existing `combat_log.py`

### 2. Updated: `companion/main.py`
- Imports `event_metadata` module
- Extracts event info when screenshots are detected
- Uses `event_metadata.format_event_caption()` for rich captions
- Logs event type and detection method for debugging

### 3. Documentation Created
- **`ADDON_EVENT_PROTOCOL.md`** - Complete guide for addon developers
- **`EVENT_DETECTION_OPTIONS.md`** - Updated with implementation details
- **`IMPLEMENTATION_SUMMARY.md`** - This file

## How It Works

### Companion App Flow:
```
1. Screenshot detected → companion/watcher.py
2. Extract event metadata → companion/event_metadata.py
   ├─ Try: Metadata JSON file
   ├─ Try: Filename encoding
   ├─ Try: SavedVariables queue
   └─ Fallback: Combat log correlation
3. Build caption → event_metadata.format_event_caption()
4. Trigger video recording → companion/replay.py
5. Upload to Discord with contextual caption
```

### Addon Requirements:
The addon needs to communicate event information using one of these methods:

**Recommended: Metadata JSON File**
```lua
-- When taking screenshot:
Screenshot()
SaveEventMetadata("WoWScrnShot_030626_015421.jpg", "DEATH", "Player Death", "Killed by Boss")
```

See `ADDON_EVENT_PROTOCOL.md` for complete implementation guide.

## Supported Event Types

| Code | Display | Example Caption |
|------|---------|-----------------|
| `DEATH` | 💀 Death | "💀 Death — Player — Realm" |
| `BOSS_KILL` | ⚔ Boss Kill | "⚔ Boss Kill — Ragnaros defeated — Player — Realm" |
| `ACHIEVEMENT` | 🏆 Achievement | "🏆 Achievement — Loremaster — Player — Realm" |
| `LEVEL_UP` | ⬆ Level Up | "⬆ Level Up — Level 60 — Player — Realm" |
| `PVP_KILL` | ⚔ PvP Kill | "⚔ PvP Kill — EnemyName — Player — Realm" |
| `CHALLENGE_MODE` | 🏅 Challenge Mode | "🏅 Challenge Mode — +15 completed — Player — Realm" |
| `LOOT` | 💎 Loot | "💎 Loot — Item Name — Player — Realm" |
| `QUEST_COMPLETE` | 📜 Quest Complete | "📜 Quest Complete — Quest Name — Player — Realm" |
| `CUSTOM` | 📸 Custom | "📸 Custom — Details — Player — Realm" |
| `UNKNOWN` | 📸 Screenshot | "📸 Screenshot — Player — Realm" (fallback) |

## Backward Compatibility

✅ **Fully backward compatible** - The companion app still works without event metadata:
- Falls back to generic captions if no event detected
- Uses combat log correlation for deaths (if combat logging enabled)
- No breaking changes to existing functionality

## Next Steps for Addon Developer

1. **Read**: `ADDON_EVENT_PROTOCOL.md` for implementation details
2. **Implement**: Method 1 (Metadata JSON file) - recommended approach
3. **Test**: Take screenshots with events and verify JSON files are created
4. **Verify**: Check companion app logs for event detection confirmation

## Files Changed

### New Files:
- `companion/event_metadata.py` - Event detection and caption formatting
- `ADDON_EVENT_PROTOCOL.md` - Addon developer guide
- `IMPLEMENTATION_SUMMARY.md` - This file

### Modified Files:
- `companion/main.py` - Uses event metadata for captions
- `EVENT_DETECTION_OPTIONS.md` - Updated with implementation details

## Testing

To test the implementation:

1. **Without addon changes** (fallback mode):
   - Take a screenshot manually
   - Companion should detect it and use generic caption
   - If combat logging enabled and player dies, should detect death via combat log

2. **With addon changes** (full functionality):
   - Implement metadata JSON file creation in addon
   - Trigger an event (death, boss kill, etc.)
   - Verify JSON file is created alongside screenshot
   - Check companion logs for event detection
   - Verify Discord caption includes event context

## Example Output

**Before:**
```
Discord Caption: "Ivokir — Hyjal"
```

**After (with event metadata):**
```
Discord Caption: "💀 Death — Killed by Ragnaros — Ivokir — Hyjal"
```

Or:
```
Discord Caption: "⚔ Boss Kill — Ragnaros defeated — Ivokir — Hyjal"
```

## Notes

- Event detection is **non-blocking** - if metadata isn't available, companion continues with generic captions
- Multiple detection methods ensure robustness across different setups
- Combat log correlation works automatically (no addon changes needed) but requires combat logging enabled
- All methods are tried in order until one succeeds

