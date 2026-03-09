# Video Analysis for Event Detection

## Overview
The companion app can now analyze video content to detect events visually, independent of game APIs or addons. This is particularly useful for detecting the **red death border** that appears when a player dies in WoW.

## How It Works

### Multi-Method Death Detection

The system uses **two complementary methods** to detect deaths:

#### Method 1: Red Edge/Glow Detection
When a player dies in WoW, the screen edges turn red or have a red glow. The system:

1. **Extracts frames** from the video using ffmpeg
2. **Analyzes edge pixels** (top, bottom, left, right borders)
3. **Detects red color** using multiple algorithms:
   - Solid red pixels
   - Red dominance (R > G and R > B)
   - Red tinting (red elevated relative to green/blue)
4. **Calculates confidence** based on percentage of red pixels

#### Method 2: OCR Text Detection
The system also uses OCR to detect death-related text:

1. **Extracts frames** from the video
2. **Preprocesses images** (grayscale, contrast enhancement)
3. **Runs OCR** to extract text
4. **Searches for death phrases**:
   - "You died"
   - "Minutes until Release"
   - "Release in X minutes"
   - "Resurrect"
   - Other death-related text

**Combined Detection:**
- Either method can trigger detection
- OCR detection boosts confidence significantly
- Both methods together provide very high accuracy

### Technical Details

**Frame Extraction:**
- Extracts 10 frames from the last 5 seconds of video
- Uses ffmpeg to extract frames at evenly spaced intervals
- Scales frames to 1080p for consistent analysis

**Red Detection Algorithm:**
```python
# Red pixels are detected when:
R > 0.6  (high red channel)
G < 0.3  (low green)
B < 0.3  (low blue)

# Edge regions checked:
- Top edge: first 10 pixels
- Bottom edge: last 10 pixels  
- Left edge: first 10 pixels
- Right edge: last 10 pixels
```

**Confidence Calculation:**
- Counts red pixels in edge regions
- Calculates ratio: `red_pixels / total_edge_pixels`
- Requires ≥30% red pixels to confirm death (avoids false positives)

## Integration

Video analysis is integrated into the event detection pipeline:

1. **Screenshot detected** → Extract event info from metadata/logs
2. **Video captured** → Analyze video content
3. **Enhance event info** → Video analysis confirms/overrides detection
4. **Final caption** → Uses best available event information

### Detection Priority:
1. Metadata JSON file (from addon)
2. Filename encoding
3. SavedVariables queue
4. Combat log correlation
5. **Video analysis** (new!)

## Usage

Video analysis runs automatically when:
- Event type is `UNKNOWN` (no other detection method found)
- Event type is `DEATH` (confirms via video analysis)

**Example Flow:**
```
Screenshot detected → No metadata found → Event: UNKNOWN
Video captured → Analyze frames → Red edges detected → Event: DEATH ✅
```

## Configuration

Video analysis is **enabled by default** but can be disabled by removing Pillow/numpy dependencies.

**Parameters (in `video_analysis.py`):**
- `edge_width`: Width of edge region to check (default: 10 pixels)
- `red_threshold`: Minimum red pixel ratio (default: 0.7)
- `analyze_last_seconds`: How many seconds to analyze (default: 5.0)
- `num_frames`: Number of frames to extract (default: 10)

## Performance

**Processing Time:**
- Frame extraction: ~1-2 seconds (depends on video length)
- Image analysis: ~0.1-0.5 seconds per frame
- Total: ~2-5 seconds per video

**Resource Usage:**
- CPU: Moderate (frame extraction + image processing)
- Memory: Low (temporary frame files)
- Disk: Temporary (frames deleted after analysis)

## Limitations

1. **Resolution Dependent**: Works best with 1080p+ videos
2. **UI Variations**: May miss red borders if UI addons modify screen edges
3. **False Positives**: Red UI elements near edges might trigger detection (rare)
4. **Processing Time**: Adds 2-5 seconds to video processing pipeline
5. **OCR Requirements**: Requires Tesseract OCR engine installed separately
6. **OCR Accuracy**: Depends on text clarity, font, and video quality
7. **Language**: OCR currently optimized for English text

## Future Enhancements

Potential improvements:

1. **Achievement Detection**: Detect achievement popup frames
2. **Level Up Detection**: Detect level up notification graphics
3. **Boss Kill Detection**: Detect boss kill screen/animations
4. **Machine Learning**: Train ML model for more accurate detection
5. **Configurable Thresholds**: Allow users to adjust sensitivity

## Dependencies

Required packages (added to `requirements.txt`):
- `Pillow>=10.0.0` - Image processing
- `numpy>=1.24.0` - Array operations
- `pytesseract>=0.3.10` - OCR wrapper (optional, but recommended)

**OCR Setup:**
`pytesseract` requires the Tesseract OCR engine to be installed separately:

**Windows:**
1. Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install Tesseract (default location: `C:\Program Files\Tesseract-OCR`)
3. Add to PATH or set `TESSDATA_PREFIX` environment variable

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Note:** OCR is optional - the system works without it, but text detection significantly improves accuracy.

Uses existing:
- `imageio-ffmpeg` - ffmpeg binary access
- `subprocess` - Frame extraction

## Testing

To test video analysis:

1. Record a video where player dies (red border appears)
2. Save video to Nvidia folder
3. Trigger screenshot (or manually process video)
4. Check logs for: `"Video analysis: 💀 Death"`
5. Verify confidence score in logs

**Expected Output:**
```
[12:34:56]   Screenshot: WoWScrnShot_030626_015421
[12:34:56]   Event: 📸 Screenshot (detected via none)
[12:34:58]   Replay captured: video.mp4
[12:35:00]   Video analysis: 💀 Death
[12:35:00]   Confidence: 85%
[12:35:02]   WebM ready: video.webm
```

## Code Structure

**Files:**
- `companion/video_analysis.py` - Core analysis functions
- `companion/event_metadata.py` - Integration with event detection
- `companion/main.py` - Calls video analysis when video ready

**Key Functions:**
- `detect_death_in_video()` - Main death detection function
- `_extract_frames()` - Extracts frames using ffmpeg
- `_detect_red_edges()` - Analyzes single frame for red edges
- `enhance_event_info_with_video()` - Integrates with event system

## Notes

- Video analysis is **optional** - system works without it
- Falls back gracefully if Pillow/numpy not available
- Temporary frame files are cleaned up automatically
- Analysis happens **after** video capture (non-blocking)

