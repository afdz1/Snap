Snap = Snap or {}
Snap.lastScreenshot = 0

local SCREENSHOT_COOLDOWN = 2

local frame = CreateFrame("Frame", "SnapFrame", UIParent)
frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("PLAYER_DEAD")
frame:RegisterEvent("CHAT_MSG_LOOT")
frame:RegisterEvent("BOSS_KILL")
frame:RegisterEvent("CHALLENGE_MODE_COMPLETED")

local function TryScreenshot()
    local now = GetTime()
    if (now - Snap.lastScreenshot) >= SCREENSHOT_COOLDOWN then
        Screenshot()
        Snap.lastScreenshot = now
    end
end

frame:SetScript("OnEvent", function(self, event, ...)
    if event == "PLAYER_LOGIN" then
        print("|cff00ff00[Snap]|r Login.")

        SnapCurrentCharacter = {
            name = UnitName("player"),
            realm = GetRealmName(),
            class = select(2, UnitClass("player")),
            time = time(),
        }

        print("Character saved:", SnapCurrentCharacter.name, SnapCurrentCharacter.realm)

    elseif event == "CHAT_MSG_LOOT" then


        local text = ...


        local itemLink = text and text:match("|Hitem:.-|h.-|h")


        if itemLink then
            local name, link, quality, itemLevel = GetItemInfo(itemLink)


            if quality and itemLevel and quality >= 4 and itemLevel >= 245 then
                print("|cff00ff00[Snap]|r Epic 245+ loot detected.")
                TryScreenshot()
            end
        end

    elseif event == "PLAYER_DEAD" then
        print("|cff00ff00[Snap]|r Dead.")
        TryScreenshot()

    elseif event == "BOSS_KILL" then
        print("|cff00ff00[Snap]|r Boss Kill.")
        TryScreenshot()

    elseif event == "CHALLENGE_MODE_COMPLETED" then
        print("|cff00ff00[Snap]|r Dungeon completed.")
        TryScreenshot()
    end
end)