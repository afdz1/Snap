-- SnapConfig.lua — In-game settings GUI
-- Opened via /snap

local panel   -- main frame reference

-- ── Helpers ─────────────────────────────────────────────────────────────────
local function MakeCheckbox(parent, label, x, y, settingKey)
    local cb = CreateFrame("CheckButton", nil, parent, "InterfaceOptionsCheckButtonTemplate")
    cb:SetPoint("TOPLEFT", x, y)
    cb.Text:SetText(label)
    cb.Text:SetFont(cb.Text:GetFont(), 13)

    -- Load current value
    cb:SetChecked(SnapDB and SnapDB[settingKey] ~= false and (SnapDB[settingKey] or true))

    cb:SetScript("OnClick", function(self)
        SnapDB[settingKey] = self:GetChecked()
    end)

    return cb
end

local function MakeSlider(parent, label, x, y, settingKey, minVal, maxVal, step)
    local bg = parent:CreateTexture(nil, "BACKGROUND")
    bg:SetColorTexture(0, 0, 0, 0.3)
    bg:SetSize(240, 60)
    bg:SetPoint("TOPLEFT", x, y)

    local lbl = parent:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    lbl:SetPoint("TOPLEFT", x + 4, y - 4)
    lbl:SetText(label)

    local slider = CreateFrame("Slider", nil, parent, "OptionsSliderTemplate")
    slider:SetPoint("TOPLEFT", x + 4, y - 22)
    slider:SetSize(220, 20)
    slider:SetMinMaxValues(minVal, maxVal)
    slider:SetValueStep(step)
    slider:SetObeyStepOnDrag(true)
    slider:SetValue(SnapDB and SnapDB[settingKey] or minVal)
    slider.Low:SetText(minVal)
    slider.High:SetText(maxVal)

    local valLbl = parent:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    valLbl:SetPoint("TOP", slider, "BOTTOM", 0, 2)
    valLbl:SetText(tostring(slider:GetValue()))

    slider:SetScript("OnValueChanged", function(self, val)
        val = math.floor(val)
        SnapDB[settingKey] = val
        valLbl:SetText(tostring(val))
    end)

    return slider
end

local function MakeHeader(parent, text, x, y)
    local t = parent:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    t:SetPoint("TOPLEFT", x, y)
    t:SetText(text)
    t:SetTextColor(1, 0.82, 0, 1) -- WoW gold
    return t
end

local function MakeDivider(parent, x, y, width)
    local tex = parent:CreateTexture(nil, "BACKGROUND")
    tex:SetColorTexture(1, 0.82, 0, 0.4)
    tex:SetSize(width or 320, 1)
    tex:SetPoint("TOPLEFT", x, y)
    return tex
end

-- ── Build panel ─────────────────────────────────────────────────────────────
local function BuildPanel()
    if panel then return end

    panel = CreateFrame("Frame", "SnapConfigPanel", UIParent, "BackdropTemplate")
    panel:SetSize(380, 440)
    panel:SetPoint("CENTER")
    panel:SetFrameStrata("HIGH")
    panel:SetMovable(true)
    panel:EnableMouse(true)
    panel:RegisterForDrag("LeftButton")
    panel:SetScript("OnDragStart", panel.StartMoving)
    panel:SetScript("OnDragStop",  panel.StopMovingOrSizing)
    panel:SetBackdrop({
        bgFile   = "Interface/Tooltips/UI-Tooltip-Background",
        edgeFile = "Interface/DialogFrame/UI-DialogBox-Border",
        edgeSize = 24,
        insets   = { left=6, right=6, top=6, bottom=6 },
    })
    panel:SetBackdropColor(0.05, 0.05, 0.08, 0.98)
    panel:SetBackdropBorderColor(1, 0.82, 0, 1)
    panel:Hide()

    -- Title bar
    local title = panel:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    title:SetPoint("TOP", 0, -16)
    title:SetText("|cffffd700⚔  Snap  |r|cffaaaaaa— Settings|r")

    -- Close button
    local closeBtn = CreateFrame("Button", nil, panel, "UIPanelCloseButton")
    closeBtn:SetPoint("TOPRIGHT", -4, -4)
    closeBtn:SetScript("OnClick", function() panel:Hide() end)

    -- ── Section: Events ──────────────────────────────────────────────────────
    MakeHeader(panel, "Events to Screenshot", 20, -50)
    MakeDivider(panel, 18, -66, 344)

    MakeCheckbox(panel, "Player Death",                   20, -78,  "onDeath")
    MakeCheckbox(panel, "Boss Kill",                      20, -108, "onBossKill")
    MakeCheckbox(panel, "Mythic / Dungeon Completed",     20, -138, "onDungeon")
    MakeCheckbox(panel, "Epic Loot",                      20, -168, "onEpicLoot")

    -- ── Section: Loot thresholds ─────────────────────────────────────────────
    MakeHeader(panel, "Loot Thresholds", 20, -210)
    MakeDivider(panel, 18, -226, 344)

    local qualityNote = panel:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    qualityNote:SetPoint("TOPLEFT", 20, -234)
    qualityNote:SetText("|cffaaaaaa4 = Epic  •  5 = Legendary|r")

    MakeSlider(panel, "Min Quality",    20, -258, "epicMinQuality", 3, 5, 1)
    MakeSlider(panel, "Min Item Level", 20, -328, "epicMinIlvl",  200, 700, 5)

    -- ── Footer ───────────────────────────────────────────────────────────────
    local footer = panel:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
    footer:SetPoint("BOTTOM", 0, 14)
    footer:SetText("Settings save instantly  •  /snap to reopen")
end

-- ── Public API ───────────────────────────────────────────────────────────────
function SnapConfig_Open()
    BuildPanel()

    -- Refresh checkbox states in case SnapDB changed since last open
    if SnapDB then
        for _, child in ipairs({ panel:GetChildren() }) do
            if child.GetChecked and child.settingKey then
                child:SetChecked(SnapDB[child.settingKey])
            end
        end
    end

    if panel:IsShown() then
        panel:Hide()
    else
        panel:Show()
    end
end

