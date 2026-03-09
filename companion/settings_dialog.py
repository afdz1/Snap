"""
settings_dialog.py
WoW-themed settings dialog. Opened from the main window's Settings button.
"""

import os
import keyboard
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QFrame, QCheckBox,
)
from PyQt6.QtCore import Qt
import config
import startup
import theme

# Subfolders checked (in priority order) when deriving paths from WoW exe
_WOW_FLAVOURS = ("_retail_", "_classic_era_", "_classic_", "_ptr_", "_xptr_")


def _divider() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background-color: {theme.BORDER};")
    return line


class SettingsDialog(QDialog):
    def __init__(self, cfg: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Snap — Settings")
        self.setMinimumWidth(560)
        self.cfg = dict(cfg)
        self._fields: dict[str, QLineEdit] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("⚙   Settings")
        title.setStyleSheet(f"color: {theme.GOLD_BR}; font-size: 16px;")
        layout.addWidget(title)
        layout.addWidget(_divider())

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # ── WoW Executable (top of form — auto-fills screenshots folder) ──
        wow_exe_edit = QLineEdit(str(self.cfg.get("wow_exe", "")))
        wow_exe_edit.setPlaceholderText(r"e.g. D:\World of Warcraft\Wow.exe")
        self._fields["wow_exe"] = wow_exe_edit
        wow_browse = QPushButton("…")
        wow_browse.setFixedWidth(34)
        wow_browse.clicked.connect(self._browse_wow_exe)
        wow_row = QHBoxLayout()
        wow_row.setSpacing(6)
        wow_row.addWidget(wow_exe_edit)
        wow_row.addWidget(wow_browse)
        wow_lbl = QLabel("WoW Executable")
        wow_lbl.setStyleSheet(f"color: {theme.GOLD};")
        form.addRow(wow_lbl, wow_row)

        path_fields = [
            ("Screenshots Folder",         "screenshots_folder"),
            ("Nvidia Video Output Folder", "nvidia_video_folder"),
        ]
        text_fields = [
            ("Save Replay Hotkey",         "hotkey"),
            ("Post-Event Delay (sec)",     "post_event_delay"),
            ("Clip Duration (sec)",        "clip_duration"),
        ]

        for label, key in path_fields:
            edit = QLineEdit(str(self.cfg.get(key, "")))
            self._fields[key] = edit
            browse = QPushButton("…")
            browse.setFixedWidth(34)
            browse.clicked.connect(lambda _, k=key: self._browse(k))
            row = QHBoxLayout()
            row.setSpacing(6)
            row.addWidget(edit)
            row.addWidget(browse)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {theme.GOLD};")
            form.addRow(lbl, row)

        layout.addLayout(form)

        form2 = QFormLayout()
        form2.setSpacing(10)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        for label, key in text_fields:
            edit = QLineEdit(str(self.cfg.get(key, "")))
            self._fields[key] = edit
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {theme.GOLD};")
            form2.addRow(lbl, edit)

        layout.addLayout(form2)
        layout.addWidget(_divider())

        self._startup_cb = QCheckBox("Launch Snap automatically on Windows startup")
        self._startup_cb.setStyleSheet(f"color: {theme.GOLD};")
        self._startup_cb.setChecked(self.cfg.get("launch_on_startup", True))
        layout.addWidget(self._startup_cb)

        layout.addWidget(_divider())

        # Discord credentials
        discord_lbl = QLabel("Discord")
        discord_lbl.setStyleSheet(f"color: {theme.GOLD_BR}; font-size: 13px;")
        layout.addWidget(discord_lbl)

        form3 = QFormLayout()
        form3.setSpacing(10)
        form3.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        token_edit = QLineEdit(str(self.cfg.get("discord_bot_token", "")))
        token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        token_edit.setPlaceholderText("Bot token from discord.com/developers/applications")
        self._fields["discord_bot_token"] = token_edit
        token_lbl = QLabel("Bot Token")
        token_lbl.setStyleSheet(f"color: {theme.GOLD};")
        form3.addRow(token_lbl, token_edit)

        channel_edit = QLineEdit(str(self.cfg.get("discord_channel_id", "")))
        channel_edit.setPlaceholderText("Channel ID (right-click channel → Copy ID)")
        self._fields["discord_channel_id"] = channel_edit
        channel_lbl = QLabel("Channel ID")
        channel_lbl.setStyleSheet(f"color: {theme.GOLD};")
        form3.addRow(channel_lbl, channel_edit)

        death_channel_edit = QLineEdit(str(self.cfg.get("discord_death_channel_id", "")))
        death_channel_edit.setPlaceholderText("Optional: Death channel ID (leave empty to use default)")
        self._fields["discord_death_channel_id"] = death_channel_edit
        death_channel_lbl = QLabel("Death Channel ID")
        death_channel_lbl.setStyleSheet(f"color: {theme.GOLD};")
        form3.addRow(death_channel_lbl, death_channel_edit)

        layout.addLayout(form3)
        layout.addWidget(_divider())

        nvidia_lbl = QLabel("Nvidia")
        nvidia_lbl.setStyleSheet(f"color: {theme.GOLD_BR}; font-size: 13px;")
        layout.addWidget(nvidia_lbl)

        nvidia_row = QHBoxLayout()
        nvidia_info = QLabel("Enable microphone capture in the GeForce Experience overlay.")
        nvidia_info.setStyleSheet(f"color: {theme.DIM}; font-size: 9pt;")
        nvidia_row.addWidget(nvidia_info)
        nvidia_row.addStretch()
        nvidia_btn = QPushButton("⚙   Open Nvidia Audio Settings")
        nvidia_btn.clicked.connect(self._open_nvidia_audio)
        nvidia_row.addWidget(nvidia_btn)
        layout.addLayout(nvidia_row)

        layout.addWidget(_divider())

        save_btn = QPushButton("Save Settings")
        save_btn.setMinimumWidth(140)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _browse_wow_exe(self) -> None:
        """Let the user pick Wow.exe and auto-fill the screenshots folder."""
        exe, _ = QFileDialog.getOpenFileName(
            self, "Select WoW Executable", "", "Executables (*.exe)"
        )
        if not exe:
            return
        exe = os.path.normpath(exe)
        self._fields["wow_exe"].setText(exe)

        # Auto-derive screenshots folder from the exe location
        wow_dir = os.path.dirname(exe)
        for flavour in _WOW_FLAVOURS:
            shots = os.path.join(wow_dir, flavour, "Screenshots")
            if os.path.isdir(shots):
                self._fields["screenshots_folder"].setText(os.path.normpath(shots))
                return

        # Screenshots folder doesn't exist yet — pre-fill the retail path anyway
        # so the user at least has a sensible default once they launch WoW once.
        fallback = os.path.join(wow_dir, "_retail_", "Screenshots")
        self._fields["screenshots_folder"].setText(os.path.normpath(fallback))

    def _open_nvidia_audio(self) -> None:
        """Triggers the GeForce Experience overlay (Alt+Z) so the user can
        navigate to Audio settings and enable microphone capture."""
        keyboard.press_and_release("alt+z")

    def _browse(self, key: str) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self._fields[key].setText(folder)

    def _save(self) -> None:
        int_keys = {"post_event_delay", "clip_duration"}
        for key, edit in self._fields.items():
            raw = edit.text().strip()
            self.cfg[key] = int(raw) if key in int_keys and raw.isdigit() else raw
        self.cfg["launch_on_startup"] = self._startup_cb.isChecked()
        config.save(self.cfg)
        startup.enable() if self._startup_cb.isChecked() else startup.disable()
        self.accept()

    def get_config(self) -> dict:
        return self.cfg

