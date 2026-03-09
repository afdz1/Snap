# Event Detection Options for WoW Video Recording

## Problem Statement
The WoW addon successfully detects events via API and takes screenshots, but the companion app (Snap.exe) has **no way to know which event triggered each screenshot**. Without this context, all clips get generic captions like "Player — Realm" instead of "💀 Death — Player — Realm" or "⚔ Boss Kill — Ragnaros defeated — Player — Realm".

## Current System
- **Method**: WoW addon detects events → Takes screenshots → Companion watches Screenshots folder → Triggers Nvidia ShadowPlay
- **Problem**: Companion sees screenshot files but doesn't know what event caused them
- **Solution**: ✅ **Implemented** - Multi-method event metadata system (see `companion/event_metadata.py`)

## ✅ Implemented Solution: Event Metadata System

The companion app now supports **4 methods** (in priority order) for receiving event context from the addon:

### Method 1: Metadata JSON File (✅ Recommended)
**Status**: ✅ Implemented in `event_metadata.py`

The addon creates a JSON file alongside each screenshot with event information:
- `WoWScrnShot_030626_015421.jpg` → `WoWScrnShot_030626_015421.json`

**See**: `ADDON_EVENT_PROTOCOL.md` for implementation details.

### Method 2: Filename Encoding
**Status**: ✅ Implemented as fallback

Addon encodes event type in filename: `WoWScrnShot_MMDDYY_HHMMSS_EVENTTYPE.jpg`

### Method 3: SavedVariables Event Queue
**Status**: ✅ Implemented as fallback

Addon stores events in `Snap.lua` SavedVariables, companion correlates by timestamp.

### Method 4: Combat Log Correlation
**Status**: ✅ Implemented as automatic fallback

Companion reads combat log and matches events by timestamp (existing `combat_log.py` functionality).

---

## Alternative Detection Methods (For Reference)

### 1. Combat Log Parsing (✅ Already Implemented)
**File**: `companion/combat_log.py`

**How it works**:
- Monitors `WoWCombatLog.txt` for specific events (e.g., `UNIT_DIED`)
- Parses timestamps and event data
- Works regardless of UI configuration

**Pros**:
- ✅ UI-independent
- ✅ Already partially implemented
- ✅ Reliable event detection
- ✅ Rich event data available

**Cons**:
- Requires combat logging enabled in WoW
- May miss non-combat events
- Parsing complexity increases with more event types

**Implementation**:
```python
# Extend combat_log.py to detect more event types:
# - ENCOUNTER_START/END (boss fights)
# - ACHIEVEMENT_EARNED
# - CHALLENGE_MODE_COMPLETED
# - PLAYER_KILL (PvP)
# - SPELL_CAST_SUCCESS (specific spells)
```

**Events Available**:
- `UNIT_DIED` - Player/NPC deaths
- `ENCOUNTER_START` - Boss encounters begin
- `ENCOUNTER_END` - Boss encounters end
- `ACHIEVEMENT_EARNED` - Achievement unlocks
- `CHALLENGE_MODE_COMPLETED` - M+ completion
- `PLAYER_KILL` - PvP kills
- `SPELL_CAST_SUCCESS` - Ability usage
- `SWING_DAMAGE` / `SPELL_DAMAGE` - Damage events

---

### 2. Log File Monitoring (Recommended Enhancement)
**How it works**:
- Watch multiple WoW log files for changes
- Parse structured log entries
- Trigger on specific patterns

**Pros**:
- ✅ UI-independent
- ✅ Multiple event sources
- ✅ Can combine with combat log
- ✅ Works with any UI setup

**Cons**:
- Requires file system monitoring
- Log format may change with WoW updates
- Need to handle log rotation

**Log Files to Monitor**:
- `WoWCombatLog.txt` / `WoWCombatLog-*.txt` (combat events)
- `ChatLog.txt` (system messages, achievements)
- `WoWCombatLog.txt` (already monitored)

**Implementation Approach**:
```python
# Create a unified log watcher that:
# 1. Monitors multiple log files
# 2. Parses different log formats
# 3. Emits standardized events
# 4. Triggers recording on configurable event patterns
```

---

### 3. Saved Variables Monitoring
**How it works**:
- Monitor WoW's `WTF/Account/*/SavedVariables/` folder
- Detect changes to achievement/stat files
- Trigger on file modification timestamps

**Pros**:
- ✅ Can detect achievement unlocks
- ✅ UI-independent
- ✅ Persistent data

**Cons**:
- Less real-time (file writes may be delayed)
- File structure varies by account
- May miss temporary events

**Files to Watch**:
- `Blizzard_AchievementUI.lua` (achievements)
- `Blizzard_EncounterJournal.lua` (encounters)
- Addon-specific saved variables

---

### 4. Audio Pattern Detection
**How it works**:
- Capture system audio or WoW's audio output
- Detect specific sound effects (achievement fanfare, death sounds, etc.)
- Use audio fingerprinting or ML models

**Pros**:
- ✅ Works regardless of UI
- ✅ Can detect audio-only cues
- ✅ Real-time detection

**Cons**:
- Complex implementation
- Requires audio capture setup
- May have false positives
- Performance overhead

**Use Cases**:
- Achievement fanfare sound
- Level-up sound
- Death sound
- Boss encounter music changes

---

### 5. Manual Hotkey Trigger
**How it works**:
- User presses a configurable hotkey
- Immediately triggers video save
- Simple and reliable

**Pros**:
- ✅ 100% reliable
- ✅ User has full control
- ✅ Simple implementation
- ✅ No false positives

**Cons**:
- Requires user action
- May miss events if user forgets
- Not fully automated

**Implementation**:
```python
# Add to config.py:
"manual_hotkey": "ctrl+shift+s",  # Separate from Nvidia hotkey

# Add to main.py:
# Register global hotkey listener
# When pressed, trigger replay save immediately
```

---

### 6. Continuous Recording with Smart Trimming
**How it works**:
- Always record (or record during gameplay sessions)
- Detect events retroactively
- Trim clips based on event timestamps

**Pros**:
- ✅ Never miss events
- ✅ Can analyze after the fact
- ✅ Works with any detection method

**Cons**:
- High storage requirements
- Processing overhead
- May need to manage disk space

**Implementation**:
- Use Nvidia ShadowPlay's continuous recording
- Periodically scan for events
- Extract relevant clips based on timestamps

---

### 7. Hybrid Approach (Recommended)
**Combine multiple methods for robustness**:

1. **Primary**: Combat log monitoring (already implemented)
   - Detect combat-related events
   - Real-time, reliable

2. **Secondary**: Log file monitoring
   - Catch system messages, achievements
   - Backup for combat log

3. **Fallback**: Manual hotkey
   - User can always trigger manually
   - Catches edge cases

4. **Optional**: Saved variables monitoring
   - For achievement tracking
   - Less time-sensitive events

**Implementation Strategy**:
```python
class EventDetector:
    def __init__(self):
        self.combat_log_watcher = CombatLogWatcher()
        self.chat_log_watcher = ChatLogWatcher()
        self.saved_vars_watcher = SavedVarsWatcher()
        self.manual_hotkey = ManualHotkeyHandler()
    
    def start(self):
        # Start all watchers
        # Any can trigger recording
        # Deduplicate events within time window
```

---

## Recommended Implementation Plan

### Phase 1: Enhance Combat Log Detection
- [ ] Extend `combat_log.py` to detect more event types
- [ ] Add configurable event filters
- [ ] Improve timestamp accuracy

### Phase 2: Add Log File Monitoring
- [ ] Create `log_watcher.py` for multiple log files
- [ ] Parse ChatLog.txt for system messages
- [ ] Combine with combat log events

### Phase 3: Add Manual Hotkey Option
- [ ] Add manual trigger hotkey to config
- [ ] Implement global hotkey listener
- [ ] Allow users to trigger saves manually

### Phase 4: Hybrid System
- [ ] Create unified event detection system
- [ ] Combine all detection methods
- [ ] Add event deduplication
- [ ] Configurable method priority

---

## Configuration Options

Add to `config.py`:
```python
DEFAULTS = {
    # ... existing config ...
    
    # Event detection methods
    "detection_methods": {
        "combat_log": True,
        "chat_log": True,
        "saved_vars": False,
        "manual_hotkey": True,
    },
    
    # Events to detect
    "detect_events": {
        "player_death": True,
        "boss_encounter": True,
        "achievement": True,
        "pvp_kill": True,
        "challenge_mode": True,
    },
    
    # Manual trigger hotkey
    "manual_trigger_hotkey": "ctrl+shift+s",
    
    # Event deduplication window (seconds)
    "event_dedup_window": 5.0,
}
```

---

## Testing Considerations

1. **UI Independence**: Test with different UI addons (ElvUI, WeakAuras, etc.)
2. **Event Coverage**: Verify all target events are detected
3. **False Positives**: Minimize accidental triggers
4. **Performance**: Ensure detection doesn't impact gameplay
5. **Reliability**: Test with combat logging enabled/disabled

---

## Notes

- Combat logging must be enabled in WoW for combat log methods to work
- Some methods may require additional permissions (audio capture, file monitoring)
- Consider user privacy when monitoring log files
- Balance between detection accuracy and system performance

