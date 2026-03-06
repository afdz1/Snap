"""
main.py
Snap Companion — WoW-themed PyQt6 main window.
Watches the WoW Screenshots folder; each new screenshot triggers Nvidia
Instant Replay, trims the clip to the event window, and converts to GIF.
"""

import os
import sys
import ctypes
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QPlainTextEdit, QFrame, QSizePolicy,
    QSystemTrayIcon,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QTextCursor

import config
import theme
import watcher
import replay
import converter
import discord_sender
import updater
import addon_installer
import character
from tray import SnapTray, make_icon
from settings_dialog import SettingsDialog
from version import __version__

# Discord credentials come from bot_secrets.py (bundled in exe, never in config)
try:
    import bot_secrets as _bs
    _BOT_TOKEN  = _bs.BOT_TOKEN
    _CHANNEL_ID = str(_bs.CHANNEL_ID)
except ImportError:
    _BOT_TOKEN  = ""
    _CHANNEL_ID = ""


def _divider() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background-color: {theme.BORDER};")
    return line


class SnapWindow(QMainWindow):
    # Signal for thread-safe log updates (emitted from watcher/converter threads)
    _log_sig = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Snap  v{__version__}")
        self.setMinimumSize(660, 500)
        self.cfg = config.load()
        self._watcher: watcher.ScreenshotWatcher | None = None
        self._running = False

        self._log_sig.connect(self._append_log)
        self._build_ui()
        self.setWindowIcon(make_icon())
        self._tray = SnapTray(self)

        # Nvidia status: check immediately, then every 5 s
        QTimer.singleShot(0, self._check_nvidia)

        # Auto-start watching on launch
        QTimer.singleShot(500, self._start)
        self._nvidia_timer = QTimer(self)
        self._nvidia_timer.timeout.connect(self._check_nvidia)
        self._nvidia_timer.start(5_000)

        # Install/update bundled addon on every launch
        QTimer.singleShot(200, self._check_addon)

        # Silently check for app updates in the background (after 3 s)
        QTimer.singleShot(3_000, lambda: updater.check_and_download(self._log))

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        # Header
        hdr = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(2)
        title = QLabel("⚔   SNAP")
        title.setStyleSheet(f"color: {theme.GOLD_BR}; font-size: 24px;")
        sub = QLabel("World of Warcraft Event Companion")
        sub.setStyleSheet(f"color: {theme.DIM}; font-size: 10px;")
        col.addWidget(title)
        col.addWidget(sub)
        hdr.addLayout(col)
        hdr.addStretch()
        settings_btn = QPushButton("⚙   Settings")
        settings_btn.clicked.connect(self._open_settings)
        hdr.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignTop)
        lay.addLayout(hdr)
        lay.addWidget(_divider())

        # Status row
        sr = QHBoxLayout()
        self._nvidia_lbl = QLabel("⬤   Nvidia: checking…")
        self._nvidia_lbl.setStyleSheet(f"color: {theme.DIM};")
        self._watcher_lbl = QLabel("⬤   Watcher: Stopped")
        self._watcher_lbl.setStyleSheet(f"color: {theme.DIM};")
        sr.addWidget(self._nvidia_lbl)
        sr.addStretch()
        sr.addWidget(self._watcher_lbl)
        lay.addLayout(sr)
        lay.addWidget(_divider())

        # Log
        log_title = QLabel("Activity Log")
        log_title.setStyleSheet(f"color: {theme.GOLD_BR}; font-size: 12px;")
        lay.addWidget(log_title)
        self._log_box = QPlainTextEdit()
        self._log_box.setReadOnly(True)
        self._log_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        lay.addWidget(self._log_box)

        # Controls
        lay.addWidget(_divider())
        ctrl = QHBoxLayout()
        self._toggle_btn = QPushButton("▶   Start Watching")
        self._toggle_btn.setMinimumWidth(170)
        self._toggle_btn.clicked.connect(self._toggle)
        ctrl.addStretch()
        ctrl.addWidget(self._toggle_btn)
        lay.addLayout(ctrl)

    # ── Settings ──────────────────────────────────────────────────────────────

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self.cfg, parent=self)
        if dlg.exec():
            self.cfg = dlg.get_config()
            self._log("Settings saved.")
            if self._running:
                self._stop()
            self._start()

    # ── Watcher ───────────────────────────────────────────────────────────────

    def _toggle(self) -> None:
        self._stop() if self._running else self._start()

    def closeEvent(self, event) -> None:
        """Minimise to tray instead of quitting."""
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "Snap", "Still running in the background.",
            QSystemTrayIcon.MessageIcon.Information, 2000,
        )

    def _quit(self) -> None:
        """Full exit from the tray menu."""
        self._stop()
        updater.apply_on_exit()   # no-op unless an update was downloaded
        QApplication.instance().quit()

    def _check_addon(self) -> None:
        """Install or update the bundled WoW addon silently."""
        msg = addon_installer.check_and_install(self.cfg.get("screenshots_folder", ""))
        if msg:
            self._log(f"Addon: {msg}")

    def _start(self) -> None:
        folder = self.cfg["screenshots_folder"]
        if not os.path.isdir(folder):
            self._log(f"ERROR: folder not found — {folder}")
            return
        self._watcher = watcher.ScreenshotWatcher(folder, self._on_screenshot)
        self._watcher.start()
        self._running = True
        self._toggle_btn.setText("■   Stop Watching")
        self._watcher_lbl.setText("⬤   Watcher: Active")
        self._watcher_lbl.setStyleSheet(f"color: {theme.GREEN};")
        self._tray.set_watching(True)
        self._log(f"Watching: {folder}")

    def _stop(self) -> None:
        if self._watcher:
            self._watcher.stop()
            self._watcher = None
        self._running = False
        self._toggle_btn.setText("▶   Start Watching")
        self._watcher_lbl.setText("⬤   Watcher: Stopped")
        self._watcher_lbl.setStyleSheet(f"color: {theme.DIM};")
        self._tray.set_watching(False)
        self._log("Stopped.")

    # ── Nvidia status ─────────────────────────────────────────────────────────

    def _check_nvidia(self) -> None:
        active = replay.is_instant_replay_active()
        if active:
            self._nvidia_lbl.setText("⬤   Nvidia: Active")
            self._nvidia_lbl.setStyleSheet(f"color: {theme.GREEN};")
        else:
            self._nvidia_lbl.setText("⬤   Nvidia: Not detected")
            self._nvidia_lbl.setStyleSheet(f"color: {theme.RED};")
            if self._running:
                self._log("WARNING: Nvidia Instant Replay not detected.")

    # ── Screenshot → GIF pipeline ─────────────────────────────────────────────

    def _on_screenshot(self, screenshot_path: str) -> None:
        name = os.path.splitext(os.path.basename(screenshot_path))[0]
        self._log(f"Screenshot: {name}")

        # Clips folder is always World of Warcraft/_retail_/clips (one level up from Screenshots)
        clips_folder = os.path.normpath(
            os.path.join(self.cfg["screenshots_folder"], "..", "clips")
        )
        webm_path = os.path.join(clips_folder, name + ".webm")

        def on_video_ready(video_path: str) -> None:
            self._log(f"Replay captured: {os.path.basename(video_path)}")
            try:
                webm_out = converter.make_webm(
                    video_path, webm_path,
                    duration=int(self.cfg["clip_duration"]),
                )
                self._log(f"WebM ready:  {os.path.basename(webm_out)}")
                info    = character.get_player_info(self.cfg["screenshots_folder"])
                caption = character.format_caption(info)
                if caption:
                    self._log(f"Player: {caption}")
                ok, msg = discord_sender.send(
                    _BOT_TOKEN,
                    _CHANNEL_ID,
                    webm_out,
                    caption=caption,
                )
                self._log(msg)
            except Exception as exc:
                self._log(f"ERROR (convert): {exc}")

        def on_timeout() -> None:
            self._log("ERROR: timed out — is Instant Replay enabled?")

        replay.trigger_and_wait(
            nvidia_folder=self.cfg["nvidia_video_folder"],
            hotkey=self.cfg["hotkey"],
            delay=int(self.cfg["post_event_delay"]),
            on_video_ready=on_video_ready,
            on_timeout=on_timeout,
        )

    # ── Thread-safe log ───────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_sig.emit(f"[{ts}]   {msg}")

    def _append_log(self, line: str) -> None:
        self._log_box.appendPlainText(line)
        self._log_box.moveCursor(QTextCursor.MoveOperation.End)


if __name__ == "__main__":
    # Tell Windows this is its own app so the taskbar shows our icon, not python.exe
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("snap.companion")

    app = QApplication(sys.argv)
    theme.apply(app)
    app.setWindowIcon(make_icon())   # applies to taskbar + all windows
    window = SnapWindow()
    window.show()
    sys.exit(app.exec())
