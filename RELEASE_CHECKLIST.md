# Release Checklist for v1.2.0

## Pre-Release Checklist

### Code Updates
- [x] Version updated to 1.2.0 in `companion/version.py`
- [x] CHANGELOG.md created with release notes
- [x] All new features implemented and tested
- [x] Dependencies updated in `companion/requirements.txt`

### Testing
- [ ] Test video analysis with sample videos
- [ ] Test death detection (red edges, health bar, OCR)
- [ ] Test death channel routing
- [ ] Test text overlay on death videos
- [ ] Test fallback to default channel when death channel not set
- [ ] Verify all detection methods work correctly

### Documentation
- [x] CHANGELOG.md created
- [x] Technical documentation updated (VIDEO_ANALYSIS.md, etc.)
- [ ] README.md updated (if exists)

### Build Verification
- [ ] Local build test (pyinstaller snap.spec)
- [ ] Verify exe runs correctly
- [ ] Test all features in built exe

## Release Steps

### 1. Final Commit
```bash
git add .
git commit -m "Release v1.2.0: Video analysis, death detection, and optional death channel"
```

### 2. Create Git Tag
```bash
git tag v1.2.0
git push origin main
git push origin v1.2.0
```

### 3. GitHub Actions
- GitHub Actions will automatically:
  - Build the Windows exe
  - Create a GitHub Release
  - Upload Snap.exe to the release
  - Post notification to Discord

### 4. Verify Release
- [ ] Check GitHub Releases page for v1.2.0
- [ ] Verify Snap.exe is attached
- [ ] Check release notes are correct
- [ ] Verify Discord notification was sent

## Post-Release

### Monitor
- [ ] Check for any user-reported issues
- [ ] Monitor error logs if available
- [ ] Verify update mechanism works (users can update from 1.1.8)

## New Features in v1.2.0

### Major Features
1. **Video Analysis System**
   - Red edge/glow detection
   - Empty health bar detection
   - OCR text detection (optional)

2. **Death Text Overlay**
   - Automatic "[PlayerName] is dead." overlay
   - Configurable appearance

3. **Optional Death Channel**
   - Separate Discord channel for deaths
   - Falls back to default if not configured

4. **Enhanced Event Detection**
   - Multiple detection methods
   - Better accuracy and reliability

### Dependencies Added
- Pillow>=10.0.0
- numpy>=1.24.0
- pytesseract>=0.3.10 (optional)

### Breaking Changes
None - fully backward compatible

### Migration Notes
- Existing users: No action required
- OCR is optional - app works without Tesseract
- Death channel is optional - leave empty to use default

