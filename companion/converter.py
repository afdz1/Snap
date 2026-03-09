"""
converter.py
Converts a full-length Nvidia Instant Replay video into:
  - A 10-second MP4 clip  → saved in the Nvidia video folder (replaces the original)
  - A WebM (VP9) clip     → saved in the output/clips folder for Discord sharing

The original full-length replay is deleted after the MP4 trim is confirmed.
Uses the bundled ffmpeg binary from imageio-ffmpeg — no system install needed.
"""

import os
import sys
import subprocess
import imageio_ffmpeg

_ffmpeg: str | None = None
_MAX_HEIGHT = 1080  # cap at 1080p; smaller sources are left at their native resolution

# Prevent ffmpeg from spawning a visible console window on Windows
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def _get_ffmpeg() -> str:
    global _ffmpeg
    if _ffmpeg is None:
        _ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    return _ffmpeg


def make_webm(
    video_path: str,
    webm_output: str,
    duration: int = 10,
    fps: int = 30,
    overlay_text: str | None = None,
    overlay_duration: float = 2.0,
) -> str:
    """
    Pipeline:
      1. Trim last `duration` seconds of `video_path` → temporary MP4 (H.264).
      2. Convert trimmed MP4 → WebM (VP9) at `webm_output`.
      3. Delete the temporary MP4 and the original full-length `video_path`.
    
    If `overlay_text` is provided, adds a text overlay at the beginning of the video
    for `overlay_duration` seconds.

    Returns webm_output_path.
    Raises subprocess.CalledProcessError on ffmpeg failure.
    """
    ffmpeg = _get_ffmpeg()
    os.makedirs(os.path.dirname(os.path.abspath(webm_output)), exist_ok=True)

    # Temporary MP4 for the conversion pipeline (deleted after WebM is created)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    mp4_temp = os.path.join(os.path.dirname(video_path), base_name + "_temp.mp4")

    try:
        # Step 1 — trim last N seconds to 1080p MP4 (H.264 video + AAC audio)
        subprocess.run(
            [
                ffmpeg, "-y",
                "-sseof", str(-duration),
                "-i", video_path,
                "-t", str(duration),
                "-c:v", "libx264", "-crf", "23", "-preset", "fast",
                "-vf", f"scale=-2:'min(ih,{_MAX_HEIGHT})':flags=lanczos",
                "-c:a", "aac", "-b:a", "192k",      # preserve audio (game/mic/discord)
                mp4_temp,
            ],
            check=True, capture_output=True, creationflags=_NO_WINDOW,
        )

        # Step 2 — 1080p VP9 WebM with Opus audio (Discord-compatible)
        # Build video filter chain
        vf_parts = [
            f"scale=-2:'min(ih,{_MAX_HEIGHT})':flags=lanczos",
            f"fps={fps}",
        ]
        
        # Add text overlay if provided
        if overlay_text:
            # Escape special characters for ffmpeg drawtext filter
            # Replace single quotes with escaped version, escape colons and backslashes
            escaped_text = overlay_text.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")
            
            # Text overlay: centered horizontally, raised vertically, large font, white text with black outline
            # Shows for overlay_duration seconds at the start
            text_filter = (
                f"drawtext=text='{escaped_text}'"
                f":fontsize=60"
                f":fontcolor=white"
                f":borderw=3"
                f":bordercolor=black"
                f":x=(w-text_w)/2"
                f":y=h*0.25"
                f":enable='between(t,0,{overlay_duration})'"
            )
            vf_parts.append(text_filter)
        
        vf_chain = ",".join(vf_parts)
        
        subprocess.run(
            [
                ffmpeg, "-y",
                "-i", mp4_temp,
                "-c:v", "libvpx-vp9",
                "-crf", "33", "-b:v", "0",          # constant-quality mode
                "-cpu-used", "4",                    # 0=slowest/best … 8=fastest
                "-deadline", "good",                 # balance quality vs speed
                "-vf", vf_chain,
                "-c:a", "libopus", "-b:a", "128k",  # Opus audio (WebM standard)
                webm_output,
            ],
            check=True, capture_output=True, creationflags=_NO_WINDOW,
        )

    finally:
        # Clean up: delete temp MP4 and the original full-length replay
        for path in (mp4_temp, video_path):
            if os.path.exists(path):
                os.remove(path)

    return webm_output
