"""
build_icon.py
─────────────
Run this ONCE before packaging with PyInstaller to generate:
  • addon/icon.png   — used by the WoW addon (## IconTexture)
  • addon/icon.ico   — used by the Windows exe (PyInstaller icon=)

Requires: PyQt6  (already in requirements.txt)
          Pillow (pip install Pillow — only needed at build time)

Usage:
    python build_icon.py
"""

import os
import sys

# Allow importing from companion/ without installing as a package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "companion"))

from PyQt6.QtWidgets import QApplication
from tray import make_icon

# QApplication must exist before any QPixmap operations
app = QApplication(sys.argv)

icon    = make_icon()
pixmap  = icon.pixmap(64, 64)   # WoW addon icons are 64 × 64

os.makedirs("addon", exist_ok=True)
png_path = os.path.join("addon", "icon.png")
ico_path = os.path.join("addon", "icon.ico")

# ── PNG (for WoW addon) ───────────────────────────────────────────────────────
pixmap.save(png_path, "PNG")
print(f"  ✓  {png_path}")

# ── ICO (for Windows exe) ─────────────────────────────────────────────────────
try:
    from PIL import Image
    with Image.open(png_path) as img:
        img.save(
            ico_path,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)],
        )
    print(f"  ✓  {ico_path}")
except ImportError:
    print("  ⚠  Pillow not found — skipping .ico generation.")
    print("     Install it with:  pip install Pillow")
    print("     The exe will fall back to the default Python icon without it.")

