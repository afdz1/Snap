"""
test_video_analysis.py
Test script to analyze videos in the clips folder and measure video analysis accuracy.

Usage:
    python test_video_analysis.py [clips_folder]
    
    If clips_folder not provided, uses default from config or prompts user.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional

# Add companion directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "companion"))

try:
    import event_metadata
    import video_analysis
except ImportError as e:
    print(f"ERROR: Could not import required modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    sys.exit(1)


def find_video_files(folder: str) -> list[str]:
    """Find all video files in the folder."""
    video_extensions = (".mp4", ".mkv", ".avi", ".webm", ".mov")
    videos = []
    
    if not os.path.isdir(folder):
        return videos
    
    for file in os.listdir(folder):
        if file.lower().endswith(video_extensions):
            videos.append(os.path.join(folder, file))
    
    return sorted(videos)


def analyze_video(video_path: str) -> dict:
    """Analyze a single video and return results."""
    print(f"\n{'='*60}")
    print(f"Analyzing: {os.path.basename(video_path)}")
    print(f"{'='*60}")
    
    result = {
        "video_path": video_path,
        "video_name": os.path.basename(video_path),
        "death_detected": False,
        "confidence": 0.0,
        "event_info": None,
        "error": None,
    }
    
    try:
        # Run video analysis
        event_info = video_analysis.analyze_video_for_events(video_path)
        
        if event_info:
            result["death_detected"] = event_info.get("event_type") == "DEATH"
            result["confidence"] = event_info.get("confidence", 0.0)
            result["event_info"] = event_info
            
            print(f"✅ Event detected: {event_info.get('event_name', 'Unknown')}")
            if result["death_detected"]:
                print(f"   Confidence: {result['confidence']:.1%}")
                print(f"   Source: {event_info.get('source', 'unknown')}")
            else:
                print(f"   Event type: {event_info.get('event_type', 'UNKNOWN')}")
        else:
            print("❌ No event detected")
            result["death_detected"] = False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        result["error"] = str(e)
    
    return result


def get_user_feedback(video_path: str) -> Optional[dict]:
    """Prompt user for manual verification."""
    print("\n" + "-"*60)
    print("Manual Verification:")
    print("  Did this video actually contain a death?")
    print("  (y=yes, n=no, s=skip, q=quit)")
    
    response = input("  Your answer: ").strip().lower()
    
    if response == 'q':
        return None  # Signal to quit
    if response == 's':
        return {"manual_verification": "skipped"}
    
    is_death = response == 'y'
    
    return {
        "manual_verification": "yes" if is_death else "no",
        "actual_death": is_death,
    }


def calculate_accuracy(results: list[dict]) -> dict:
    """Calculate accuracy metrics from results."""
    total = len(results)
    if total == 0:
        return {}
    
    # Count detections
    detected = sum(1 for r in results if r.get("death_detected", False))
    verified = sum(1 for r in results if r.get("actual_death") is not None)
    true_positives = sum(
        1 for r in results 
        if r.get("death_detected") and r.get("actual_death") == True
    )
    false_positives = sum(
        1 for r in results 
        if r.get("death_detected") and r.get("actual_death") == False
    )
    false_negatives = sum(
        1 for r in results 
        if not r.get("death_detected") and r.get("actual_death") == True
    )
    true_negatives = sum(
        1 for r in results 
        if not r.get("death_detected") and r.get("actual_death") == False
    )
    
    # Calculate metrics
    accuracy = None
    precision = None
    recall = None
    f1_score = None
    
    if verified > 0:
        correct = true_positives + true_negatives
        accuracy = correct / verified if verified > 0 else 0.0
        
        if (true_positives + false_positives) > 0:
            precision = true_positives / (true_positives + false_positives)
        
        if (true_positives + false_negatives) > 0:
            recall = true_positives / (true_positives + false_negatives)
        
        if precision is not None and recall is not None:
            if (precision + recall) > 0:
                f1_score = 2 * (precision * recall) / (precision + recall)
    
    # Average confidence
    confidences = [r.get("confidence", 0.0) for r in results if r.get("death_detected")]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    return {
        "total_videos": total,
        "detected_deaths": detected,
        "verified_videos": verified,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "average_confidence": avg_confidence,
    }


def print_summary(results: list[dict], metrics: dict):
    """Print summary statistics."""
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    print(f"\nTotal videos analyzed: {metrics.get('total_videos', 0)}")
    print(f"Deaths detected: {metrics.get('detected_deaths', 0)}")
    print(f"Videos verified: {metrics.get('verified_videos', 0)}")
    
    if metrics.get("verified_videos", 0) > 0:
        print(f"\n📊 Accuracy Metrics:")
        print(f"   Accuracy:    {metrics.get('accuracy', 0):.1%}")
        print(f"   Precision:   {metrics.get('precision', 0):.1%}" if metrics.get('precision') else "   Precision:   N/A")
        print(f"   Recall:      {metrics.get('recall', 0):.1%}" if metrics.get('recall') else "   Recall:      N/A")
        print(f"   F1 Score:    {metrics.get('f1_score', 0):.1%}" if metrics.get('f1_score') else "   F1 Score:    N/A")
        
        print(f"\n📈 Confusion Matrix:")
        print(f"   True Positives:  {metrics.get('true_positives', 0)}")
        print(f"   False Positives: {metrics.get('false_positives', 0)}")
        print(f"   False Negatives: {metrics.get('false_negatives', 0)}")
        print(f"   True Negatives:  {metrics.get('true_negatives', 0)}")
    
    if metrics.get("average_confidence", 0) > 0:
        print(f"\n🎯 Average Confidence: {metrics.get('average_confidence', 0):.1%}")
    
    # List videos with issues
    issues = []
    for r in results:
        if r.get("error"):
            issues.append((r["video_name"], f"Error: {r['error']}"))
        elif r.get("actual_death") is not None:
            detected = r.get("death_detected", False)
            actual = r.get("actual_death", False)
            if detected != actual:
                issue_type = "False Positive" if detected else "False Negative"
                issues.append((r["video_name"], issue_type))
    
    if issues:
        print(f"\n⚠️  Issues Found ({len(issues)}):")
        for video_name, issue in issues:
            print(f"   - {video_name}: {issue}")


def save_results(results: list[dict], metrics: dict, output_file: str):
    """Save results to JSON file."""
    output = {
        "metrics": metrics,
        "results": results,
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")


def main():
    """Main test function."""
    print("="*60)
    print("Video Analysis Accuracy Test")
    print("="*60)
    
    # Get clips folder
    clips_folder = None
    if len(sys.argv) > 1:
        clips_folder = sys.argv[1]
    else:
        # Try to get from config
        try:
            import config
            cfg = config.load()
            screenshots_folder = cfg.get("screenshots_folder", "")
            if screenshots_folder:
                clips_folder = os.path.normpath(
                    os.path.join(screenshots_folder, "..", "clips")
                )
        except:
            pass
        
        if not clips_folder or not os.path.isdir(clips_folder):
            clips_folder = input("\nEnter clips folder path: ").strip().strip('"')
    
    if not clips_folder or not os.path.isdir(clips_folder):
        print(f"ERROR: Clips folder not found: {clips_folder}")
        sys.exit(1)
    
    print(f"\n📁 Clips folder: {clips_folder}")
    
    # Find videos
    videos = find_video_files(clips_folder)
    if not videos:
        print(f"\n❌ No video files found in {clips_folder}")
        sys.exit(1)
    
    print(f"📹 Found {len(videos)} video file(s)")
    
    # Ask for verification mode
    print("\n" + "-"*60)
    print("Verification Mode:")
    print("  1. Automatic (no manual verification)")
    print("  2. Interactive (prompt for each video)")
    print("  3. Batch (analyze all, then verify)")
    
    mode = input("Select mode (1/2/3, default=1): ").strip() or "1"
    
    results = []
    verify_later = mode == "3"
    
    # Analyze videos
    for i, video_path in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}]")
        result = analyze_video(video_path)
        results.append(result)
        
        # Interactive verification
        if mode == "2":
            feedback = get_user_feedback(video_path)
            if feedback is None:  # User quit
                break
            result.update(feedback)
        
        # Batch mode - collect for later
        elif verify_later:
            result["manual_verification"] = "pending"
    
    # Batch verification
    if verify_later and results:
        print("\n" + "="*60)
        print("BATCH VERIFICATION")
        print("="*60)
        print("Review each video and mark if it contains a death.")
        print("(y=yes, n=no, s=skip, q=quit)")
        
        for result in results:
            if result.get("error"):
                continue
            
            print(f"\nVideo: {result['video_name']}")
            if result.get("death_detected"):
                print(f"  Detected: Death (confidence: {result.get('confidence', 0):.1%})")
            else:
                print(f"  Detected: No death")
            
            response = input("  Actual death? (y/n/s/q): ").strip().lower()
            
            if response == 'q':
                break
            if response == 's':
                result["manual_verification"] = "skipped"
                continue
            
            result["actual_death"] = response == 'y'
            result["manual_verification"] = "yes" if result["actual_death"] else "no"
    
    # Calculate metrics
    metrics = calculate_accuracy(results)
    
    # Print summary
    print_summary(results, metrics)
    
    # Save results
    output_file = os.path.join(clips_folder, "video_analysis_test_results.json")
    save_results(results, metrics, output_file)
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

