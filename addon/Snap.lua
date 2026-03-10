-- Snap.lua — Core event handling
-- Settings are stored in SnapDB (SavedVariables) and configurable via /snap

Snap = Snap or {}
Snap.lastScreenshot = 0

local SCREENSHOT_COOLDOWN = 2

-- ── Default settings ────────────────────────────────────────────────────────
local DEFAULTS = {
    onDeath        = true,
    onBossKill     = true,
    onDungeon      = true,
    onEpicLoot     = true,
    epicMinQuality = 4,     -- 4 = Epic, 5 = Legendary
    epicMinIlvl    = 245,
}

-- ── Helpers ─────────────────────────────────────────────────────────────────
local function DB()
    return SnapDB
end

local function Setting(key)
    local db = DB()
    if db and db[key] ~= nil then
        return db[key]
    end
    return DEFAULTS[key]
end

local function TryScreenshot()
    local now = GetTime()
    if (now - Snap.lastScreenshot) >= SCREENSHOT_COOLDOWN then
        Screenshot()
        Snap.lastScreenshot = now
    end
end

-- ── Event frame ─────────────────────────────────────────────────────────────
local frame = CreateFrame("Frame", "SnapFrame", UIParent)
frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("PLAYER_DEAD")
frame:RegisterEvent("CHAT_MSG_LOOT")
frame:RegisterEvent("BOSS_KILL")
frame:RegisterEvent("CHALLENGE_MODE_COMPLETED")

frame:SetScript("OnEvent", function(self, event, ...)
    if event == "PLAYER_LOGIN" then
        -- Initialise SavedVariables with defaults on first load
        if not SnapDB then SnapDB = {} end
        for k, v in pairs(DEFAULTS) do
            if SnapDB[k] == nil then SnapDB[k] = v end
        end

        SnapCurrentCharacter = {
            name  = UnitName("player"),
            realm = GetRealmName(),
            class = select(2, UnitClass("player")),
            time  = time(),
        }

        print("|cff00ff00[Snap]|r Ready. Type |cffffff00/snap|r to configure.")

    elseif event == "PLAYER_DEAD" then
        if Setting("onDeath") then
            print("|cff00ff00[Snap]|r Dead — screenshotting.")
            TryScreenshot()
        end

    elseif event == "BOSS_KILL" then
        if Setting("onBossKill") then
            print("|cff00ff00[Snap]|r Boss killed — screenshotting.")
            TryScreenshot()
        end

    elseif event == "CHALLENGE_MODE_COMPLETED" then
        if Setting("onDungeon") then
            print("|cff00ff00[Snap]|r Dungeon completed — screenshotting.")
            TryScreenshot()
        end

    elseif event == "CHAT_MSG_LOOT" then
        if Setting("onEpicLoot") then
            local text = ...
            local itemLink = text and text:match("|Hitem:.-|h.-|h")
            if itemLink then
                local _, _, quality, _, _, _, _, _, _, _, _, _, _, _, itemLevel = GetItemInfo(itemLink)
                local ilvl = itemLevel or 0
                if quality and ilvl > 0
                    and quality >= Setting("epicMinQuality")
                    and ilvl    >= Setting("epicMinIlvl") then
                    print("|cff00ff00[Snap]|r Epic loot detected — screenshotting.")
                    TryScreenshot()
                end
            end
        end
    end
end)

-- ── Slash command ────────────────────────────────────────────────────────────
SLASH_SNAP1 = "/snap"
SlashCmdList["SNAP"] = function()
    SnapConfig_Open()
end
