"""
converter.py
Converts a full-length Nvidia Instant Replay video into:
  - A 10-second MP4 clip  → saved in the Nvidia video folder (replaces the original)
  - A WebM (VP9) clip     → saved in the output/clips folder for Discord sharing

The original full-length replay is deleted after the MP4 trim is confirmed.
Uses the bundled ffmpeg binary from imageio-ffmpeg — no system install needed.
"""

import os
import subprocess
import imageio_ffmpeg

_ffmpeg: str | None = None
_MAX_HEIGHT = 1080  # cap at 1080p; smaller sources are left at their native resolution


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
) -> str:
    """
    Pipeline:
      1. Trim last `duration` seconds of `video_path` → temporary MP4 (H.264).
      2. Convert trimmed MP4 → WebM (VP9) at `webm_output`.
      3. Delete the temporary MP4 and the original full-length `video_path`.

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
            check=True, capture_output=True,
        )

        # Step 2 — 1080p VP9 WebM with Opus audio (Discord-compatible)
        subprocess.run(
            [
                ffmpeg, "-y",
                "-i", mp4_temp,
                "-c:v", "libvpx-vp9",
                "-crf", "33", "-b:v", "0",          # constant-quality mode
                "-cpu-used", "4",                    # 0=slowest/best … 8=fastest
                "-deadline", "good",                 # balance quality vs speed
                "-vf", f"fps={fps},scale=-2:'min(ih,{_MAX_HEIGHT})':flags=lanczos",
                "-c:a", "libopus", "-b:a", "128k",  # Opus audio (WebM standard)
                webm_output,
            ],
            check=True, capture_output=True,
        )

    finally:
        # Clean up: delete temp MP4 and the original full-length replay
        for path in (mp4_temp, video_path):
            if os.path.exists(path):
                os.remove(path)

    return webm_output
