"""
replay.py
Waits post_event_delay seconds, simulates the Nvidia Save Replay hotkey,
then watches the Nvidia video folder for the newly saved clip.
"""

import os
import time
import threading
import keyboard
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Processes that must be running for Instant Replay to capture footage
_NVIDIA_SHARE_PROCS = {"nvidia share.exe", "nvsphelper64.exe"}


def is_instant_replay_active() -> bool:
    """Returns True if the Nvidia ShadowPlay overlay process is running."""
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"].lower() in _NVIDIA_SHARE_PROCS:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

_VIDEO_EXTENSIONS = (".mp4", ".mkv", ".avi")
_VIDEO_WAIT_TIMEOUT = 30  # seconds to wait for Nvidia to create the file


class _VideoHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self._callback = callback

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(_VIDEO_EXTENSIONS):
            self._callback(event.src_path)


def _wait_until_written(
    path: str,
    poll_interval: float = 0.5,
    stable_checks: int = 3,
    timeout: float = 60.0,
) -> bool:
    """
    Polls file size every `poll_interval` seconds. Once the size has been
    stable for `stable_checks` consecutive checks the file is considered
    fully written by Nvidia. Returns False if `timeout` is exceeded.
    """
    deadline = time.time() + timeout
    last_size = -1
    stable = 0

    while time.time() < deadline:
        try:
            size = os.path.getsize(path)
        except OSError:
            time.sleep(poll_interval)
            continue

        if size == last_size and size > 0:
            stable += 1
            if stable >= stable_checks:
                return True
        else:
            stable = 0
            last_size = size

        time.sleep(poll_interval)

    return False


def trigger_and_wait(
    nvidia_folder: str,
    hotkey: str,
    delay: int,
    on_video_ready,
    on_timeout=None,
) -> None:
    """
    Non-blocking. Spawns a daemon thread that:
      1. Waits `delay` seconds (to capture post-event footage in the buffer).
      2. Presses the Save Replay hotkey.
      3. Watches `nvidia_folder` (recursively) for a new video file.
      4. Calls on_video_ready(path) once the file is settled, or on_timeout().
    """
    def _run():
        time.sleep(delay)

        new_videos = []
        found_event = threading.Event()

        def _video_found(path):
            new_videos.append(path)
            found_event.set()

        observer = Observer()
        observer.schedule(_VideoHandler(_video_found), nvidia_folder, recursive=True)
        observer.start()

        keyboard.press_and_release(hotkey)

        found = found_event.wait(timeout=_VIDEO_WAIT_TIMEOUT)
        observer.stop()
        observer.join()

        if found and new_videos:
            path = new_videos[0]
            if _wait_until_written(path):
                on_video_ready(path)
            elif on_timeout:
                on_timeout()
        elif on_timeout:
            on_timeout()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

