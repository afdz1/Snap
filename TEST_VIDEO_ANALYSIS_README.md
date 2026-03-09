# Video Analysis Accuracy Test

## Overview
The `test_video_analysis.py` script analyzes videos in your clips folder to test the accuracy of the video analysis system (red death border detection).

## Usage

### Basic Usage
```bash
python test_video_analysis.py
```

The script will:
1. Auto-detect your clips folder from config (if available)
2. Or prompt you to enter the folder path
3. Analyze all videos in the folder
4. Generate accuracy metrics

### Specify Clips Folder
```bash
python test_video_analysis.py "C:\Path\To\Clips\Folder"
```

## Verification Modes

### Mode 1: Automatic (Default)
- Analyzes all videos automatically
- No manual verification
- Good for quick testing
- Results show detection counts only

### Mode 2: Interactive
- Prompts for each video: "Did this contain a death?"
- Provides accuracy metrics (precision, recall, F1)
- Best for thorough testing
- Can quit early with 'q'

### Mode 3: Batch
- Analyzes all videos first
- Then prompts for verification in batch
- Good for reviewing many videos
- Shows detection results before asking

## Output

### Console Output
```
============================================================
Video Analysis Accuracy Test
============================================================

📁 Clips folder: C:\...\clips
📹 Found 5 video file(s)

[1/5]
============================================================
Analyzing: video1.webm
============================================================
✅ Event detected: 💀 Death
   Confidence: 85.0%
   Source: video_analysis

...

============================================================
SUMMARY
============================================================

Total videos analyzed: 5
Deaths detected: 3
Videos verified: 5

📊 Accuracy Metrics:
   Accuracy:    80.0%
   Precision:   100.0%
   Recall:      66.7%
   F1 Score:    80.0%

📈 Confusion Matrix:
   True Positives:  2
   False Positives: 0
   False Negatives: 1
   True Negatives:  2

🎯 Average Confidence: 82.5%

💾 Results saved to: .../clips/video_analysis_test_results.json
```

### JSON Results File
Results are saved to `video_analysis_test_results.json` in the clips folder:

```json
{
  "metrics": {
    "total_videos": 5,
    "detected_deaths": 3,
    "verified_videos": 5,
    "true_positives": 2,
    "false_positives": 0,
    "false_negatives": 1,
    "true_negatives": 2,
    "accuracy": 0.8,
    "precision": 1.0,
    "recall": 0.667,
    "f1_score": 0.8,
    "average_confidence": 0.825
  },
  "results": [
    {
      "video_path": "...",
      "video_name": "video1.webm",
      "death_detected": true,
      "confidence": 0.85,
      "event_info": {...},
      "actual_death": true,
      "manual_verification": "yes"
    },
    ...
  ]
}
```

## Metrics Explained

- **Accuracy**: Overall correctness (TP + TN) / Total
- **Precision**: Of detected deaths, how many were correct (TP / (TP + FP))
- **Recall**: Of actual deaths, how many were detected (TP / (TP + FN))
- **F1 Score**: Harmonic mean of precision and recall
- **Confidence**: Average confidence score of detected deaths

## Confusion Matrix

- **True Positives**: Death detected correctly
- **False Positives**: Death detected but not present (false alarm)
- **False Negatives**: Death present but not detected (missed)
- **True Negatives**: No death, correctly identified as no death

## Tips

1. **Test with known data**: Use videos you know contain deaths vs. those that don't
2. **Start small**: Test with 5-10 videos first
3. **Review false positives**: Check why non-death videos triggered detection
4. **Review false negatives**: Check why death videos weren't detected
5. **Adjust thresholds**: If accuracy is low, consider tweaking `red_threshold` in `video_analysis.py`

## Troubleshooting

### Import Errors
```
ERROR: Could not import required modules
```
**Solution**: Install dependencies:
```bash
pip install -r companion/requirements.txt
```

### No Videos Found
```
❌ No video files found
```
**Solution**: Check that the clips folder path is correct and contains video files (.mp4, .webm, etc.)

### Video Analysis Fails
If individual videos fail to analyze:
- Check video file is not corrupted
- Verify video codec is supported by ffmpeg
- Check error messages in output

## Example Workflow

1. **Collect test videos**:
   - 5 videos with deaths (known)
   - 5 videos without deaths (known)

2. **Run test**:
   ```bash
   python test_video_analysis.py
   ```

3. **Choose Mode 2** (Interactive) for accuracy metrics

4. **Review results**:
   - Check accuracy metrics
   - Review confusion matrix
   - Look at confidence scores

5. **Adjust if needed**:
   - If too many false positives → increase `red_threshold`
   - If too many false negatives → decrease `red_threshold`
   - Modify `edge_width` if needed

6. **Re-test** with adjusted parameters

## Integration with CI/CD

You can automate testing by:
1. Creating a test dataset of known videos
2. Running the test script automatically
3. Checking accuracy thresholds in CI

Example:
```bash
python test_video_analysis.py test_videos/
# Check if accuracy > 0.8
```

