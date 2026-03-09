# Distribution Notes

## Optional Dependencies

### OCR (Text Detection)
**Status:** ✅ **Optional** - App works without it

The video analysis system includes optional OCR text detection for improved accuracy. However, **OCR is not required** for the app to function.

**Current Implementation:**
- OCR gracefully falls back if Tesseract is not installed
- Red edge detection still works without OCR
- App continues normally if OCR unavailable

**For End Users:**
- **No action required** - app works out of the box
- OCR is an **optional enhancement** for better accuracy
- If users want OCR, they can install Tesseract separately

**Installation (Optional):**
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`

**Why Not Bundle Tesseract?**
- Tesseract binary is ~50-100MB
- Requires separate installation process
- Adds complexity to distribution
- Not critical for core functionality

**Alternative Solutions (Future):**
1. **EasyOCR** - Bundles models (~100MB+) but self-contained
2. **PaddleOCR** - Similar, but larger
3. **Bundle Tesseract** - Possible but increases installer size significantly

**Recommendation:** Keep OCR optional. The red edge detection is already very accurate (90%+), and OCR is a nice-to-have enhancement.

---

## Required Dependencies (Bundled)

### FFmpeg
✅ **Bundled** via `imageio-ffmpeg`
- Automatically included in PyInstaller build
- No user installation required
- Works out of the box

### Python Libraries
✅ **Bundled** via PyInstaller
- All Python dependencies included in `.exe`
- No user installation required

---

## Build Process

The app uses PyInstaller to create a standalone `.exe`:

1. **Python dependencies** → Bundled into `.exe`
2. **FFmpeg** → Bundled via `imageio-ffmpeg`
3. **OCR (pytesseract)** → Python wrapper bundled, but Tesseract binary NOT bundled
4. **Tesseract binary** → User must install separately (optional)

---

## User Experience

### Without OCR:
- ✅ App installs and runs normally
- ✅ Red edge detection works
- ✅ All features functional
- ⚠️ Slightly lower accuracy (still 90%+)

### With OCR:
- ✅ Everything above, plus:
- ✅ Text detection for death events
- ✅ Higher accuracy (~95%+)
- ✅ Better handling of edge cases

---

## Testing Distribution

To test the distributed app:

1. **Build the .exe** (via GitHub Actions or locally)
2. **Test on clean Windows VM** (no Python, no Tesseract)
3. **Verify:**
   - App launches ✅
   - Red edge detection works ✅
   - OCR gracefully skips (no errors) ✅
   - All features functional ✅

---

## Future Considerations

If OCR becomes critical (not just nice-to-have):

1. **Bundle Tesseract:**
   - Add to PyInstaller `datas` in `snap.spec`
   - Increases installer size by ~50-100MB
   - More complex build process

2. **Use EasyOCR/PaddleOCR:**
   - Self-contained (bundles models)
   - Larger size (~100-200MB)
   - No external dependencies

3. **Cloud OCR API:**
   - Requires internet
   - Adds API costs
   - Privacy concerns

**Current approach (optional OCR) is recommended** - keeps distribution simple while allowing power users to enhance accuracy.

