"""
video_analysis.py
Analyzes video frames to detect visual indicators of events (e.g., red death border).

Uses ffmpeg to extract frames and PIL/Pillow for image analysis.
This provides a UI-independent method to detect events by analyzing the actual video content.
"""

import os
import sys
import subprocess
import tempfile
import re
from typing import Optional
from PIL import Image, ImageEnhance
import numpy as np
import imageio_ffmpeg

# OCR is optional - gracefully handle if not available
try:
    import pytesseract
    _OCR_AVAILABLE = True
except ImportError:
    _OCR_AVAILABLE = False
    pytesseract = None

_ffmpeg: str | None = None

# Prevent ffmpeg from spawning a visible console window on Windows
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _get_ffmpeg() -> str:
    global _ffmpeg
    if _ffmpeg is None:
        _ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    return _ffmpeg


def _extract_frames(video_path: str, num_frames: int = 5, start_offset: float = 0.0) -> list[str]:
    """
    Extracts frames from video using ffmpeg.
    
    Args:
        video_path: Path to video file
        num_frames: Number of frames to extract
        start_offset: Start time in seconds (0 = beginning, negative = from end)
    
    Returns:
        List of temporary file paths containing extracted frames
    """
    import re
    ffmpeg = _get_ffmpeg()
    temp_files = []
    
    try:
        # Get video duration using ffprobe (more reliable)
        probe_cmd = [
            ffmpeg, "-i", video_path,
            "-hide_banner",
        ]
        result = subprocess.run(
            probe_cmd,
            capture_output=True,
            text=True,
            creationflags=_NO_WINDOW,
        )
        
        # Parse duration from stderr (ffmpeg outputs info there)
        duration = None
        for line in result.stderr.split('\n'):
            if 'Duration:' in line:
                # Extract duration (format: Duration: HH:MM:SS.mmm)
                match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', line)
                if match:
                    h, m, s, ms = map(int, match.groups())
                    duration = h * 3600 + m * 60 + s + ms / 100
                    break
        
        if duration is None or duration <= 0:
            return []
        
        # Calculate actual start time
        if start_offset < 0:
            actual_start = max(0, duration + start_offset)
        else:
            actual_start = start_offset
        
        # Ensure we don't go past video end
        actual_start = min(actual_start, duration - 0.1)
        
        # Extract frames evenly spaced
        if num_frames <= 1:
            frame_times = [actual_start]
        else:
            end_time = min(duration - 0.1, actual_start + abs(start_offset) if start_offset < 0 else duration - 0.1)
            frame_interval = (end_time - actual_start) / (num_frames - 1) if num_frames > 1 else 0
            frame_times = [actual_start + (i * frame_interval) for i in range(num_frames)]
            frame_times = [t for t in frame_times if t < duration]
        
        for frame_time in frame_times:
            # Create temporary file for frame
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.png',
                delete=False,
                dir=tempfile.gettempdir()
            )
            temp_file.close()
            temp_files.append(temp_file.name)
            
            # Extract single frame
            cmd = [
                ffmpeg, "-y",
                "-ss", str(frame_time),
                "-i", video_path,
                "-vframes", "1",
                "-vf", "scale=-2:1080",  # Scale to 1080p for consistent analysis
                temp_file.name,
            ]
            
            result = subprocess.run(
                cmd,
                check=False,  # Don't fail if frame extraction fails
                capture_output=True,
                creationflags=_NO_WINDOW,
            )
            
            # Check if frame was actually extracted
            if not os.path.exists(temp_file.name) or os.path.getsize(temp_file.name) == 0:
                try:
                    os.unlink(temp_file.name)
                    temp_files.remove(temp_file.name)
                except:
                    pass
    
    except Exception:
        # Clean up on error
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except:
                pass
        return []
    
    return temp_files


def _detect_red_edges(image_path: str, edge_width: int = 15, red_threshold: float = 0.25) -> bool:
    """
    Detects red edges/borders/glows in an image.
    
    WoW's death screen has a red border or glow around the edges. This function:
    1. Checks edge pixels (top, bottom, left, right borders)
    2. Looks for red color/glow (red dominance, red tinting)
    3. Handles both solid red borders and red glow effects
    
    Args:
        image_path: Path to image file
        edge_width: Width of edge region to check (in pixels) - increased for glow detection
        red_threshold: Minimum ratio of red pixels needed (0.0-1.0) - lowered for glow detection
    
    Returns:
        True if red edges/glow detected, False otherwise
    """
    try:
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Handle different image modes
        if len(img_array.shape) == 2:  # Grayscale
            return False
        if img_array.shape[2] == 4:  # RGBA
            img_array = img_array[:, :, :3]  # Drop alpha
        
        height, width = img_array.shape[:2]
        
        # Define edge regions (wider for glow detection)
        top_edge = img_array[:edge_width, :]
        bottom_edge = img_array[-edge_width:, :]
        left_edge = img_array[:, :edge_width]
        right_edge = img_array[:, -edge_width:]
        
        # Combine all edges
        edges = np.vstack([
            top_edge.reshape(-1, 3),
            bottom_edge.reshape(-1, 3),
            left_edge.reshape(-1, 3),
            right_edge.reshape(-1, 3),
        ])
        
        # Normalize to 0-1 range
        edges = edges.astype(np.float32) / 255.0
        
        # Method 1: Detect solid red pixels (original method)
        # Pure red: R > 0.6, G < 0.3, B < 0.3
        solid_red_mask = (
            (edges[:, 0] > 0.6) &  # High red
            (edges[:, 1] < 0.3) &  # Low green
            (edges[:, 2] < 0.3)    # Low blue
        )
        
        # Method 2: Detect red dominance (for glows/gradients)
        # Red is the dominant color: R > G and R > B
        # And red is significant: R > 0.4 (to avoid dark pixels)
        red_dominant_mask = (
            (edges[:, 0] > edges[:, 1]) &  # Red > Green
            (edges[:, 0] > edges[:, 2]) &  # Red > Blue
            (edges[:, 0] > 0.4)            # Red is significant
        )
        
        # Method 3: Detect red tinting (for semi-transparent overlays)
        # Red channel is elevated relative to average brightness
        # R > (G + B) / 2 + threshold
        avg_gb = (edges[:, 1] + edges[:, 2]) / 2.0
        red_tint_mask = (
            (edges[:, 0] > avg_gb + 0.15) &  # Red significantly higher than G/B average
            (edges[:, 0] > 0.35)             # Red is bright enough
        )
        
        # Combine all detection methods (OR logic)
        red_mask = solid_red_mask | red_dominant_mask | red_tint_mask
        
        red_ratio = np.sum(red_mask) / len(edges) if len(edges) > 0 else 0.0
        
        return red_ratio >= red_threshold
    
    except Exception:
        return False


def _detect_empty_health_bar(image_path: str) -> bool:
    """
    Detects if the player health bar is empty/depleted by scanning the entire screen.
    
    WoW's health bar can be positioned anywhere depending on UI addons:
    - Green when full/healthy
    - Red/yellow when low
    - Empty/black when dead
    - Can be anywhere on screen (top, bottom, sides, center)
    
    This function:
    1. Scans the entire screen for green health bar colors
    2. Looks for regions that should have health bars but are empty
    3. Uses multiple detection strategies to find health bars regardless of position
    
    Args:
        image_path: Path to image file
    
    Returns:
        True if health bar appears empty, False otherwise
    """
    try:
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # Handle different image modes
        if len(img_array.shape) == 2:  # Grayscale
            return False
        if img_array.shape[2] == 4:  # RGBA
            img_array = img_array[:, :, :3]  # Drop alpha
        
        height, width = img_array.shape[:2]
        
        # Scan entire screen for health bar indicators
        all_pixels = img_array.reshape(-1, 3).astype(np.float32) / 255.0
        
        # Method 1: Detect green health bar color (when alive)
        # WoW health bars are typically bright green: RGB ~(0, 255, 0) or similar
        # Look for pixels where green is dominant and bright
        green_health_mask = (
            (all_pixels[:, 1] > 0.4) &  # Green channel is significant
            (all_pixels[:, 1] > all_pixels[:, 0] * 1.3) &  # Green > Red (green dominant)
            (all_pixels[:, 1] > all_pixels[:, 2] * 1.3) &  # Green > Blue (green dominant)
            (all_pixels[:, 0] < 0.4) &  # Red is low (not red health bar)
            (all_pixels[:, 2] < 0.4)     # Blue is low (pure green)
        )
        
        green_ratio = np.sum(green_health_mask) / len(all_pixels) if len(all_pixels) > 0 else 0.0
        
        # Method 2: Detect red/yellow health bars (low health, but not dead)
        # Red health bars: high red, low green
        # Yellow health bars: high red and green, low blue
        red_yellow_health_mask = (
            (
                # Red health bar
                ((all_pixels[:, 0] > 0.5) & (all_pixels[:, 1] < 0.3) & (all_pixels[:, 2] < 0.3)) |
                # Yellow health bar
                ((all_pixels[:, 0] > 0.4) & (all_pixels[:, 1] > 0.4) & (all_pixels[:, 2] < 0.3))
            ) &
            # Must be bright enough to be a health bar (not just dark red)
            ((all_pixels[:, 0] + all_pixels[:, 1]) > 0.6)
        )
        
        red_yellow_ratio = np.sum(red_yellow_health_mask) / len(all_pixels) if len(all_pixels) > 0 else 0.0
        
        # Method 3: Detect health bar frame/border (even when empty)
        # Health bars often have a border/frame that's visible even when empty
        # Look for rectangular regions with borders (typically darker edges)
        # This is more complex and may have false positives, so we use it as supporting evidence
        
        # Method 4: Check for absence of health bar colors
        # If we see very little green/red/yellow health bar colors across the screen,
        # AND the screen has normal brightness (not just a black screen),
        # it might indicate empty health bars
        
        # Calculate overall brightness (to avoid false positives on completely dark screens)
        avg_brightness = np.mean(all_pixels)
        
        # Health bar color threshold - if we see very few health bar colors,
        # and the screen is reasonably bright, health bars might be empty
        total_health_colors = green_ratio + red_yellow_ratio
        health_color_threshold = 0.01  # Less than 1% of screen has health bar colors
        
        # Method 5: Look for health bar regions that are dark/empty
        # Scan in grid pattern to find potential health bar locations
        # Check if those regions are dark (empty) but surrounded by UI elements
        
        # Divide screen into regions and check each
        grid_size = 8  # 8x8 grid
        region_height = height // grid_size
        region_width = width // grid_size
        
        empty_regions = 0
        total_regions = 0
        
        for i in range(grid_size):
            for j in range(grid_size):
                y_start = i * region_height
                y_end = min((i + 1) * region_height, height)
                x_start = j * region_width
                x_end = min((j + 1) * region_width, width)
                
                region = img_array[y_start:y_end, x_start:x_end]
                region_pixels = region.reshape(-1, 3).astype(np.float32) / 255.0
                
                if len(region_pixels) == 0:
                    continue
                
                total_regions += 1
                
                # Check if region has health bar colors
                region_green = np.sum(
                    (region_pixels[:, 1] > 0.4) &
                    (region_pixels[:, 1] > region_pixels[:, 0] * 1.3) &
                    (region_pixels[:, 1] > region_pixels[:, 2] * 1.3)
                ) / len(region_pixels)
                
                region_red_yellow = np.sum(
                    (
                        ((region_pixels[:, 0] > 0.5) & (region_pixels[:, 1] < 0.3)) |
                        ((region_pixels[:, 0] > 0.4) & (region_pixels[:, 1] > 0.4) & (region_pixels[:, 2] < 0.3))
                    ) & ((region_pixels[:, 0] + region_pixels[:, 1]) > 0.6)
                ) / len(region_pixels)
                
                region_health_colors = region_green + region_red_yellow
                
                # If region has very few health colors but isn't completely dark,
                # it might be an empty health bar region
                region_avg_brightness = np.mean(region_pixels)
                if region_health_colors < 0.02 and region_avg_brightness > 0.1:
                    empty_regions += 1
        
        # Calculate ratio of potentially empty health bar regions
        empty_region_ratio = empty_regions / total_regions if total_regions > 0 else 0.0
        
        # Health bar is likely empty if:
        # 1. Very few health bar colors across entire screen (<1%)
        # 2. Screen has normal brightness (not completely black)
        # 3. Multiple regions appear to have empty health bars
        
        is_empty = (
            total_health_colors < health_color_threshold and  # Very few health bar colors
            avg_brightness > 0.15 and  # Screen is reasonably bright (not black screen)
            empty_region_ratio > 0.2  # At least 20% of regions appear empty
        )
        
        return is_empty
    
    except Exception:
        return False


def detect_death_in_video(video_path: str, analyze_last_seconds: float = 5.0) -> Optional[dict]:
    """
    Analyzes video to detect death events by looking for red edges.
    
    Args:
        video_path: Path to video file
        analyze_last_seconds: How many seconds from the end to analyze
    
    Returns:
        Dict with event info if death detected, None otherwise:
        {
            "event_type": "DEATH",
            "event_name": "💀 Death",
            "details": "Detected via video analysis",
            "source": "video_analysis",
            "confidence": 0.85,  # 0.0-1.0
        }
    """
    if not os.path.isfile(video_path):
        return None
    
    # Extract more frames for better detection (especially for glows that may vary)
    temp_frames = _extract_frames(
        video_path,
        num_frames=15,  # Increased from 10 for better glow detection
        start_offset=-analyze_last_seconds  # Negative = from end
    )
    
    if not temp_frames:
        return None
    
    try:
        # Analyze each frame for red edges/glows
        death_frames = 0
        total_frames = len(temp_frames)
        frame_confidences = []
        
        for frame_path in temp_frames:
            # Try with default parameters
            if _detect_red_edges(frame_path):
                death_frames += 1
                frame_confidences.append(1.0)
            else:
                # Try with more sensitive parameters for subtle glows
                if _detect_red_edges(frame_path, edge_width=20, red_threshold=0.15):
                    death_frames += 1
                    frame_confidences.append(0.7)  # Lower confidence for subtle detection
                else:
                    frame_confidences.append(0.0)
        
        # Calculate confidence (weighted by frame detection strength)
        if total_frames > 0:
            confidence = sum(frame_confidences) / total_frames
        else:
            confidence = 0.0
        
        # Require at least 20% of frames to show red edges/glows (lowered for glow detection)
        # OR if we have strong detections in multiple frames
        strong_detections = sum(1 for c in frame_confidences if c >= 0.7)
        
        if confidence >= 0.2 or strong_detections >= 3:
            return {
                "event_type": "DEATH",
                "event_name": "💀 Death",
                "details": "Detected via video analysis",
                "source": "video_analysis",
                "confidence": confidence,
            }
    
    finally:
        # Clean up temporary frame files
        for frame_path in temp_frames:
            try:
                os.unlink(frame_path)
            except:
                pass
    
    return None


def _preprocess_image_for_ocr(image_path: str) -> Image.Image:
    """
    Preprocesses an image to improve OCR accuracy.
    - Converts to grayscale
    - Enhances contrast
    - Resizes if needed (OCR works better on larger text)
    """
    img = Image.open(image_path)
    
    # Convert to grayscale for better OCR
    if img.mode != 'L':
        img = img.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)  # Increase contrast
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.5)
    
    return img


def _detect_death_text(image_path: str) -> tuple[bool, float]:
    """
    Uses OCR to detect death-related text in an image.
    
    Looks for:
    - "You died"
    - "Minutes until Release"
    - "Release" (with numbers)
    - "Resurrect"
    - Other death-related phrases
    
    Returns:
        (detected, confidence) tuple
    
    Note: OCR requires Tesseract OCR engine to be installed separately.
    This function gracefully returns (False, 0.0) if OCR is not available.
    """
    if not _OCR_AVAILABLE:
        return False, 0.0
    
    # Check if Tesseract is actually available (pytesseract may be installed but Tesseract binary missing)
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        # Tesseract binary not found - OCR unavailable
        return False, 0.0
    
    try:
        # Preprocess image for OCR
        img = _preprocess_image_for_ocr(image_path)
        
        # Run OCR with custom config for better text detection
        # --psm 6: Assume uniform block of text
        # --oem 3: Default OCR engine mode
        custom_config = r'--oem 3 --psm 6'
        
        # Extract text
        text = pytesseract.image_to_string(img, config=custom_config)
        text = text.lower().strip()
        
        if not text:
            return False, 0.0
        
        # Death-related phrases to look for
        death_phrases = [
            r'you\s+died',
            r'minutes?\s+until\s+release',
            r'minutes?\s+until\s+resurrect',
            r'release\s+in',
            r'resurrect\s+in',
            r'\d+\s+minutes?\s+until',
            r'release',
            r'resurrect',
            r'you\s+have\s+died',
            r'death',
        ]
        
        # Check for death-related text
        matches = []
        for phrase in death_phrases:
            if re.search(phrase, text, re.IGNORECASE):
                matches.append(phrase)
        
        if matches:
            # Calculate confidence based on number and type of matches
            # Strong matches (exact phrases) get higher confidence
            strong_matches = [
                r'you\s+died',
                r'minutes?\s+until\s+release',
                r'you\s+have\s+died',
            ]
            
            has_strong_match = any(re.search(phrase, text, re.IGNORECASE) for phrase in strong_matches)
            confidence = 0.9 if has_strong_match else 0.7
            
            return True, confidence
        
        return False, 0.0
    
    except Exception:
        # OCR failed - return no detection
        return False, 0.0


def detect_death_in_video(video_path: str, analyze_last_seconds: float = 5.0) -> Optional[dict]:
    """
    Analyzes video to detect death events by looking for red edges/glows and OCR text.
    
    Args:
        video_path: Path to video file
        analyze_last_seconds: How many seconds from the end to analyze
    
    Returns:
        Dict with event info if death detected, None otherwise:
        {
            "event_type": "DEATH",
            "event_name": "💀 Death",
            "details": "Detected via video analysis",
            "source": "video_analysis",
            "confidence": 0.85,  # 0.0-1.0
        }
    """
    if not os.path.isfile(video_path):
        return None
    
    # Extract more frames for better detection (especially for glows that may vary)
    temp_frames = _extract_frames(
        video_path,
        num_frames=15,  # Increased from 10 for better glow detection
        start_offset=-analyze_last_seconds  # Negative = from end
    )
    
    if not temp_frames:
        return None
    
    try:
        # Analyze each frame for red edges/glows AND OCR text
        death_frames = 0
        total_frames = len(temp_frames)
        frame_confidences = []
        ocr_detections = 0
        ocr_confidences = []
        
        for frame_path in temp_frames:
            frame_confidence = 0.0
            
            # Method 1: Red edge detection
            if _detect_red_edges(frame_path):
                frame_confidence = max(frame_confidence, 1.0)
            elif _detect_red_edges(frame_path, edge_width=20, red_threshold=0.15):
                frame_confidence = max(frame_confidence, 0.7)
            
            # Method 2: Empty health bar detection
            if _detect_empty_health_bar(frame_path):
                # Health bar detection is very reliable
                frame_confidence = max(frame_confidence, 0.9)
            
            # Method 3: OCR text detection
            ocr_detected, ocr_confidence = _detect_death_text(frame_path)
            if ocr_detected:
                ocr_detections += 1
                ocr_confidences.append(ocr_confidence)
                # OCR detection adds to confidence (can boost or confirm)
                frame_confidence = max(frame_confidence, ocr_confidence)
            
            if frame_confidence > 0:
                death_frames += 1
            
            frame_confidences.append(frame_confidence)
        
        # Calculate overall confidence
        if total_frames > 0:
            confidence = sum(frame_confidences) / total_frames
        else:
            confidence = 0.0
        
        # Boost confidence if OCR detected death text
        if ocr_detections > 0:
            avg_ocr_confidence = sum(ocr_confidences) / len(ocr_confidences)
            # OCR detection is very reliable - boost confidence
            confidence = max(confidence, avg_ocr_confidence * 0.9)
        
        # Detection criteria:
        # 1. Red edges/glows detected (20%+ frames OR 3+ strong detections)
        # 2. OR Empty health bar detected (very reliable)
        # 3. OR OCR text detected in any frame (very reliable)
        strong_detections = sum(1 for c in frame_confidences if c >= 0.7)
        has_red_edges = confidence >= 0.2 or strong_detections >= 3
        
        # Count health bar detections
        health_bar_detections = sum(1 for c in frame_confidences if c >= 0.85)  # Health bar gives 0.9 confidence
        has_empty_health_bar = health_bar_detections >= 2  # Need at least 2 frames with empty health bar
        
        has_ocr_text = ocr_detections > 0
        
        if has_red_edges or has_empty_health_bar or has_ocr_text:
            # Determine detection method for details
            detection_methods = []
            if has_red_edges:
                detection_methods.append("red edges")
            if has_empty_health_bar:
                detection_methods.append("empty health bar")
            if has_ocr_text:
                detection_methods.append("OCR text")
            
            details = f"Detected via {' + '.join(detection_methods)}"
            
            return {
                "event_type": "DEATH",
                "event_name": "💀 Death",
                "details": details,
                "source": "video_analysis",
                "confidence": min(confidence, 1.0),  # Cap at 1.0
            }
    
    finally:
        # Clean up temporary frame files
        for frame_path in temp_frames:
            try:
                os.unlink(frame_path)
            except:
                pass
    
    return None


def analyze_video_for_events(video_path: str) -> Optional[dict]:
    """
    General video analysis function that checks for various visual event indicators.
    
    Currently supports:
    - Death detection (red edges)
    
    Future additions could detect:
    - Achievement popups
    - Level up notifications
    - Boss kill screens
    - etc.
    
    Returns:
        Event info dict if detected, None otherwise
    """
    # Check for death first (most common)
    death_event = detect_death_in_video(video_path)
    if death_event:
        return death_event
    
    # Add more event detection methods here
    
    return None

