"""
tray.py
System tray icon for the Snap companion app.
Double-click or use the context menu to show/hide the main window.
The icon is rendered programmatically — no image file needed.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt
import theme


def make_icon() -> QIcon:
    """Draws a gold-bordered circle with a sword ⚔ glyph as the tray icon."""
    px = QPixmap(32, 32)
    px.fill(Qt.GlobalColor.transparent)

    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Dark filled circle with gold border
    p.setPen(QColor(theme.GOLD))
    p.setBrush(QColor(theme.PANEL))
    p.drawEllipse(1, 1, 30, 30)

    # Gold sword glyph centred inside
    p.setPen(QColor(theme.GOLD_BR))
    font = QFont()
    font.setPixelSize(18)
    p.setFont(font)
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "⚔")

    p.end()
    return QIcon(px)


class SnapTray(QSystemTrayIcon):
    def __init__(self, window) -> None:
        super().__init__(make_icon(), window)
        self._window = window
        self.setToolTip("Snap — WoW Companion")

        menu = QMenu()

        self._vis_action = menu.addAction("Hide Snap")
        self._vis_action.triggered.connect(self._toggle_visibility)

        self._watch_action = menu.addAction("▶   Start Watching")
        self._watch_action.triggered.connect(window._toggle)

        menu.addSeparator()

        quit_action = menu.addAction("✕   Quit")
        quit_action.triggered.connect(window._quit)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)
        self.show()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_visibility()

    def _toggle_visibility(self) -> None:
        if self._window.isVisible():
            self._window.hide()
            self._vis_action.setText("Show Snap")
        else:
            self._window.show()
            self._window.raise_()
            self._window.activateWindow()
            self._vis_action.setText("Hide Snap")

    def set_watching(self, running: bool) -> None:
        self._watch_action.setText(
            "■   Stop Watching" if running else "▶   Start Watching"
        )

