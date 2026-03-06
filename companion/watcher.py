"""
watcher.py
Watches the WoW Screenshots folder for new image files and fires a callback.
"""

import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

_SCREENSHOT_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tga")


class _ScreenshotHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self._callback = callback
        self._seen = set()

    def on_created(self, event):
        if event.is_directory:
            return
        path = event.src_path
        if path.lower().endswith(_SCREENSHOT_EXTENSIONS) and path not in self._seen:
            self._seen.add(path)
            self._callback(path)


class ScreenshotWatcher:
    def __init__(self, folder: str, callback):
        self._folder = folder
        self._callback = callback
        self._observer: Observer | None = None

    def start(self) -> None:
        self._observer = Observer()
        self._observer.schedule(
            _ScreenshotHandler(self._callback),
            self._folder,
            recursive=False,
        )
        self._observer.start()

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def update_folder(self, folder: str) -> None:
        """Stop the current observer and restart watching a new folder."""
        self.stop()
        self._folder = folder
        self.start()

