# Changelog

All notable changes to Snap will be documented in this file.

## [1.2.0] - 2024

### Added
- **Video Analysis for Death Detection**
  - Red edge/glow detection (detects WoW's red death border)
  - Empty health bar detection (scans entire screen)
  - OCR text detection (detects "You died", "Minutes until Release", etc.)
  - Multi-method detection system for improved accuracy

- **Death Text Overlay**
  - Automatic text overlay on death videos: "[PlayerName] is dead."
  - Configurable font size (60px) and position (25% from top)
  - White text with black outline for visibility

- **Optional Death Channel**
  - Separate Discord channel for death clips (optional)
  - Falls back to default channel if not configured
  - Settings UI for easy configuration

- **Enhanced Event Detection**
  - Multiple detection methods (metadata, filename, SavedVariables, combat log, video analysis)
  - Improved event context in Discord captions
  - Better handling of UI-independent detection

- **Test Scripts**
  - `test_video_analysis.py` - Test video analysis accuracy
  - Comprehensive metrics and reporting

### Improved
- Video analysis accuracy (90%+ with multiple detection methods)
- Event detection robustness (works with any UI setup)
- Health bar detection (scans entire screen, not just bottom)

### Technical
- Added Pillow and numpy dependencies for image processing
- Added pytesseract dependency (optional, for OCR)
- Enhanced video analysis with multiple detection algorithms
- Improved error handling and fallback mechanisms

---

## [1.1.8] - Previous Release
- Initial release with basic screenshot watching and video capture

