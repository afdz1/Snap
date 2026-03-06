"""
theme.py
WoW-inspired dark/gold theme for the Snap companion app.
Uses the Cinzel font (free, SIL Open Font License) — downloaded from
Google Fonts on first run and cached in assets/fonts/.
"""

import os
import urllib.request
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtWidgets import QApplication

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "assets", "fonts")

_FONT_URLS = {
    "Cinzel-Regular.ttf": (
        "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/Cinzel-Regular.ttf"
    ),
    "Cinzel-Bold.ttf": (
        "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/Cinzel-Bold.ttf"
    ),
}

# ── Palette ──────────────────────────────────────────────────────────────────
GOLD      = "#c8a84b"
GOLD_BR   = "#ffd700"
BG        = "#0d0a06"
PANEL     = "#160f04"
BORDER    = "#4a3a14"
TEXT      = "#e8d48c"
DIM       = "#7a6a3a"
GREEN     = "#44cc66"
RED       = "#cc3322"

STYLESHEET = f"""
QMainWindow, QWidget, QDialog {{
    background-color: {BG};
    color: {GOLD};
}}

QLabel {{
    color: {GOLD};
    background: transparent;
}}

QPushButton {{
    background-color: {PANEL};
    border: 1px solid {GOLD};
    color: {GOLD_BR};
    padding: 6px 18px;
    font-size: 12px;
}}
QPushButton:hover {{
    background-color: #2a1f0a;
    border-color: {GOLD_BR};
    color: #ffffff;
}}
QPushButton:pressed {{
    background-color: #0a0603;
}}

QPlainTextEdit {{
    background-color: #06050302;
    border: 1px solid {BORDER};
    color: {TEXT};
    font-family: "Consolas", monospace;
    font-size: 9pt;
}}

QLineEdit {{
    background-color: {PANEL};
    border: 1px solid {BORDER};
    color: {TEXT};
    padding: 4px 6px;
    font-size: 10pt;
}}
QLineEdit:focus {{
    border-color: {GOLD};
}}

QScrollBar:vertical {{
    background: {BG};
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


def _ensure_fonts() -> str | None:
    """Downloads Cinzel fonts if not present. Returns family name or None."""
    os.makedirs(_FONTS_DIR, exist_ok=True)
    for filename, url in _FONT_URLS.items():
        dest = os.path.join(_FONTS_DIR, filename)
        if not os.path.exists(dest):
            try:
                urllib.request.urlretrieve(url, dest)
            except Exception:
                return None
    return "Cinzel"


def apply(app: QApplication) -> None:
    """Load fonts and apply the WoW stylesheet to the application."""
    family = _ensure_fonts()
    if family:
        for filename in _FONT_URLS:
            QFontDatabase.addApplicationFont(os.path.join(_FONTS_DIR, filename))
        app.setFont(QFont(family, 10))
    app.setStyleSheet(STYLESHEET)

