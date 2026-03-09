# Addon Event Metadata Protocol

## Overview
The Snap companion app needs to know **which event triggered a screenshot** so it can create appropriate captions and context for Discord messages. This document describes how the WoW addon should communicate event information to the companion app.

## Problem
When the addon takes a screenshot (e.g., `WoWScrnShot_030626_015421.jpg`), the companion app has no way to know if it was triggered by:
- A player death
- A boss kill
- An achievement unlock
- A level up
- A PvP kill
- etc.

## Solution: Multiple Communication Methods

The companion app supports **4 methods** (in order of preference) for receiving event metadata:

### Method 1: Metadata JSON File (✅ Recommended)
**Best method** - Rich data, reliable, easy to implement.

When the addon takes a screenshot, create a JSON file with the same name:

**Example:**
- Screenshot: `WoWScrnShot_030626_015421.jpg`
- Metadata: `WoWScrnShot_030626_015421.json`

**JSON Format:**
```json
{
    "event_type": "DEATH",
    "event_name": "Player Death",
    "details": "Killed by Ragnaros",
    "timestamp": 1709760000,
    "player_name": "Ivokir",
    "realm": "Hyjal"
}
```

**Fields:**
- `event_type` (required): Event code (see Event Types below)
- `event_name` (optional): Human-readable event name
- `details` (optional): Additional context (boss name, achievement name, etc.)
- `timestamp` (optional): Unix timestamp of event
- `player_name` (optional): Character name
- `realm` (optional): Realm name

**Lua Implementation:**
```lua
local function SaveEventMetadata(screenshotPath, eventType, eventName, details)
    local metadataPath = screenshotPath:gsub("%.[^%.]+$", ".json")
    local metadata = {
        event_type = eventType,
        event_name = eventName or "",
        details = details or "",
        timestamp = time(),
        player_name = UnitName("player"),
        realm = GetRealmName(),
    }
    
    local file = io.open(metadataPath, "w")
    if file then
        file:write("{\n")
        file:write(string.format('    "event_type": "%s",\n', metadata.event_type))
        file:write(string.format('    "event_name": "%s",\n', metadata.event_name))
        file:write(string.format('    "details": "%s",\n', metadata.details))
        file:write(string.format('    "timestamp": %d,\n', metadata.timestamp))
        file:write(string.format('    "player_name": "%s",\n', metadata.player_name))
        file:write(string.format('    "realm": "%s"\n', metadata.realm))
        file:write("}\n")
        file:close()
    end
end

-- Usage example:
Screenshot()
SaveEventMetadata("WoWScrnShot_030626_015421.jpg", "DEATH", "Player Death", "Killed by Boss")
```

---

### Method 2: Filename Encoding (Fallback)
**Simple method** - Encode event type in filename.

**Format:**
`WoWScrnShot_MMDDYY_HHMMSS_EVENTTYPE.jpg`

**Example:**
- `WoWScrnShot_030626_015421_DEATH.jpg`
- `WoWScrnShot_030626_015421_BOSS_KILL.jpg`
- `WoWScrnShot_030626_015421_ACHIEVEMENT.jpg`

**Lua Implementation:**
```lua
local function TakeScreenshotWithEvent(eventType)
    -- WoW's Screenshot() function doesn't let us control the filename
    -- So we need to rename after taking the screenshot
    Screenshot()
    
    -- Wait a moment for file to be created
    C_Timer.After(0.5, function()
        local screenshotsPath = "Screenshots"
        local files = {}
        -- List files and find the newest one
        -- (Implementation depends on your file listing method)
        -- Then rename: add "_" .. eventType before extension
    end)
end
```

**Note:** This method is less reliable because WoW controls screenshot filenames. You may need to monitor the Screenshots folder and rename files after creation.

---

### Method 3: SavedVariables Event Queue (Alternative)
**Persistent method** - Store events in SavedVariables, companion correlates by timestamp.

**SavedVariables Structure:**
```lua
SnapEventQueue = {
    [1] = {
        ["event_type"] = "DEATH",
        ["event_name"] = "Player Death",
        ["timestamp"] = 1709760000,
        ["details"] = "Killed by Ragnaros",
    },
    [2] = {
        ["event_type"] = "BOSS_KILL",
        ["event_name"] = "Boss Kill",
        ["timestamp"] = 1709760100,
        ["details"] = "Ragnaros defeated",
    },
}
```

**Lua Implementation:**
```lua
-- Initialize queue
if not SnapEventQueue then
    SnapEventQueue = {}
end

local function QueueEvent(eventType, eventName, details)
    table.insert(SnapEventQueue, {
        event_type = eventType,
        event_name = eventName or "",
        timestamp = time(),
        details = details or "",
    })
    
    -- Keep queue size manageable (last 10 events)
    if #SnapEventQueue > 10 then
        table.remove(SnapEventQueue, 1)
    end
end

-- When taking screenshot:
Screenshot()
QueueEvent("DEATH", "Player Death", "Killed by Boss")
```

**Companion Behavior:**
- Companion reads `SnapEventQueue` from SavedVariables
- Matches events by timestamp (within 5 second window)
- Uses most recent matching event

---

### Method 4: Combat Log Correlation (Automatic Fallback)
**No addon changes needed** - Companion automatically correlates screenshots with combat log events.

The companion app already reads `WoWCombatLog.txt` and can detect:
- Player deaths (`UNIT_DIED` events)
- Boss encounters (`ENCOUNTER_START`/`ENCOUNTER_END`)
- Other combat events

**Requirements:**
- Combat logging must be enabled in WoW
- Screenshot timestamp must be within 3 seconds of combat log event

**Note:** This is a fallback method. The companion will use this automatically if no other metadata is found.

---

## Event Types

Supported event type codes:

| Code | Display Name | Description |
|------|-------------|-------------|
| `DEATH` | 💀 Death | Player death |
| `BOSS_KILL` | ⚔ Boss Kill | Boss encounter completion |
| `ACHIEVEMENT` | 🏆 Achievement | Achievement unlocked |
| `LEVEL_UP` | ⬆ Level Up | Character leveled up |
| `PVP_KILL` | ⚔ PvP Kill | Player vs player kill |
| `CHALLENGE_MODE` | 🏅 Challenge Mode | Mythic+ completion |
| `LOOT` | 💎 Loot | Rare/epic item obtained |
| `QUEST_COMPLETE` | 📜 Quest Complete | Quest completed |
| `CUSTOM` | 📸 Custom | User-defined event |

---

## Implementation Recommendations

### For Addon Developers:

1. **Primary Method**: Use **Method 1 (Metadata JSON)** - it's the most reliable and flexible
2. **Fallback**: If JSON file creation fails, use **Method 3 (SavedVariables)** as backup
3. **Event Detection**: Use WoW API events:
   ```lua
   -- Death detection
   local frame = CreateFrame("Frame")
   frame:RegisterEvent("UNIT_DIED")
   frame:SetScript("OnEvent", function(self, event, ...)
       if event == "UNIT_DIED" then
           local guid = ...
           if UnitIsUnit(guid, "player") then
               Screenshot()
               SaveEventMetadata(screenshotPath, "DEATH", "Player Death", "Player has fallen")
           end
       end
   end)
   
   -- Achievement detection
   frame:RegisterEvent("ACHIEVEMENT_EARNED")
   frame:SetScript("OnEvent", function(self, event, achievementID)
       if event == "ACHIEVEMENT_EARNED" then
           local achievementName = GetAchievementInfo(achievementID)
           Screenshot()
           SaveEventMetadata(screenshotPath, "ACHIEVEMENT", "Achievement", achievementName)
       end
   end)
   
   -- Boss kill detection
   frame:RegisterEvent("ENCOUNTER_END")
   frame:SetScript("OnEvent", function(self, event, encounterID, encounterName, difficultyID, groupSize)
       if event == "ENCOUNTER_END" and encounterID then
           Screenshot()
           SaveEventMetadata(screenshotPath, "BOSS_KILL", "Boss Kill", encounterName)
       end
   end)
   ```

---

## Example: Complete Addon Implementation

```lua
-- Snap.lua
local addonName = "Snap"

-- Event handler frame
local eventFrame = CreateFrame("Frame")
eventFrame:RegisterEvent("ADDON_LOADED")
eventFrame:RegisterEvent("UNIT_DIED")
eventFrame:RegisterEvent("ACHIEVEMENT_EARNED")
eventFrame:RegisterEvent("ENCOUNTER_END")
eventFrame:RegisterEvent("PLAYER_LEVEL_UP")

local function GetScreenshotPath()
    -- WoW stores screenshots in Screenshots folder
    -- Filename format: WoWScrnShot_MMDDYY_HHMMSS.jpg
    -- We need to get the most recent screenshot
    -- (This is a simplified version - you may need to list files)
    return "Screenshots/WoWScrnShot_" .. date("%m%d%y_%H%M%S") .. ".jpg"
end

local function SaveEventMetadata(eventType, eventName, details)
    local screenshotPath = GetScreenshotPath()
    local metadataPath = screenshotPath:gsub("%.[^%.]+$", ".json")
    
    local metadata = {
        event_type = eventType,
        event_name = eventName or "",
        details = details or "",
        timestamp = time(),
        player_name = UnitName("player"),
        realm = GetRealmName(),
    }
    
    -- Write JSON file (simplified - you may want to use a JSON library)
    local file = io.open(metadataPath, "w")
    if file then
        file:write(string.format('{\n  "event_type": "%s",\n', metadata.event_type))
        file:write(string.format('  "event_name": "%s",\n', metadata.event_name))
        file:write(string.format('  "details": "%s",\n', metadata.details))
        file:write(string.format('  "timestamp": %d,\n', metadata.timestamp))
        file:write(string.format('  "player_name": "%s",\n', metadata.player_name))
        file:write(string.format('  "realm": "%s"\n', metadata.realm))
        file:write('}\n')
        file:close()
    end
end

eventFrame:SetScript("OnEvent", function(self, event, ...)
    if event == "ADDON_LOADED" and ... == addonName then
        -- Addon loaded
    elseif event == "UNIT_DIED" then
        local guid = ...
        if UnitIsUnit(guid, "player") then
            Screenshot()
            C_Timer.After(0.5, function()
                SaveEventMetadata("DEATH", "Player Death", "Player has fallen")
            end)
        end
    elseif event == "ACHIEVEMENT_EARNED" then
        local achievementID = ...
        local achievementName = GetAchievementInfo(achievementID)
        Screenshot()
        C_Timer.After(0.5, function()
            SaveEventMetadata("ACHIEVEMENT", "Achievement", achievementName)
        end)
    elseif event == "ENCOUNTER_END" then
        local encounterID, encounterName = ...
        if encounterID and encounterName then
            Screenshot()
            C_Timer.After(0.5, function()
                SaveEventMetadata("BOSS_KILL", "Boss Kill", encounterName)
            end)
        end
    elseif event == "PLAYER_LEVEL_UP" then
        local newLevel = ...
        Screenshot()
        C_Timer.After(0.5, function()
            SaveEventMetadata("LEVEL_UP", "Level Up", "Level " .. newLevel)
        end)
    end
end)
```

---

## Testing

To test event metadata:

1. Enable the addon in WoW
2. Trigger an event (die, kill a boss, etc.)
3. Check the Screenshots folder for:
   - Screenshot file (`.jpg`)
   - Metadata file (`.json`) - if using Method 1
4. Check companion app logs for event detection confirmation

---

## Notes

- **File Timing**: Screenshot files may take a moment to appear. Use `C_Timer.After()` to delay metadata file creation if needed.
- **File Permissions**: Ensure the addon has write permissions to the Screenshots folder.
- **Multiple Events**: If multiple events occur simultaneously, the companion uses the most recent one.
- **Backward Compatibility**: The companion still works without metadata (falls back to generic captions).

