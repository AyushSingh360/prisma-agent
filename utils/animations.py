"""
Prisma Animations — Spinner, streaming cursor, and live display management.

Manages all time-based animations via Rich.Live at ~10 FPS.
"""

import time
import threading
from typing import Optional

from rich.live import Live
from rich.text import Text

from utils.theme import (
    SPINNER_FRAMES, THINKING_STATUSES, STYLES, ICONS,
    REFRESH_RATE, CURSOR_BLINK_MS,
)


# ──────────────────────────────────────────────────────────────
# Thinking Spinner
# ──────────────────────────────────────────────────────────────

class ThinkingSpinner:
    """
    Animated braille-dot spinner with contextual status text.

    Usage:
        spinner = ThinkingSpinner()
        spinner.start("Thinking...")
        # ... do work ...
        spinner.update_status("Searching project...")
        # ... do more work ...
        spinner.stop()
    """

    def __init__(self):
        self._frame_index = 0
        self._status_text = "Thinking..."
        self._running = False
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, status: str = "Thinking..."):
        """Start the spinner animation."""
        with self._lock:
            self._running = True
            self._frame_index = 0
            self._status_text = status

    def stop(self):
        """Stop the spinner animation."""
        with self._lock:
            self._running = False

    def update_status(self, status: str):
        """Change the status text while spinning."""
        with self._lock:
            self._status_text = status

    def tick(self) -> Optional[Text]:
        """
        Advance one frame. Returns a renderable Text, or None if stopped.
        Called by the main refresh loop.
        """
        with self._lock:
            if not self._running:
                return None
            frame = SPINNER_FRAMES[self._frame_index % len(SPINNER_FRAMES)]
            self._frame_index += 1
            line = Text()
            line.append(f" {frame} ", style=STYLES["spinner"])
            line.append(self._status_text, style=STYLES["spinner_text"])
            return line


# ──────────────────────────────────────────────────────────────
# Streaming Cursor
# ──────────────────────────────────────────────────────────────

class StreamingCursor:
    """
    Manages a blinking cursor appended to streaming output.

    The cursor character (▋) toggles visibility every CURSOR_BLINK_MS.
    """

    def __init__(self):
        self._visible = True
        self._last_toggle = time.time()
        self._active = False

    def start(self):
        """Activate the blinking cursor."""
        self._active = True
        self._visible = True
        self._last_toggle = time.time()

    def stop(self):
        """Deactivate the cursor."""
        self._active = False
        self._visible = False

    @property
    def is_active(self) -> bool:
        return self._active

    def should_show(self) -> bool:
        """Returns whether the cursor should be visible right now."""
        if not self._active:
            return False
        now = time.time()
        if (now - self._last_toggle) * 1000 >= CURSOR_BLINK_MS:
            self._visible = not self._visible
            self._last_toggle = now
        return self._visible


# ──────────────────────────────────────────────────────────────
# Live Display Manager
# ──────────────────────────────────────────────────────────────

class LiveManager:
    """
    Singleton-style manager that owns the Rich Live context.

    The Live context handles the smooth refresh loop at REFRESH_RATE FPS.
    This is used for animated spinners during graph.invoke() calls.
    """

    def __init__(self, console):
        self._console = console
        self._live: Optional[Live] = None
        self._spinner = ThinkingSpinner()
        self._cursor = StreamingCursor()

    @property
    def spinner(self) -> ThinkingSpinner:
        return self._spinner

    @property
    def cursor(self) -> StreamingCursor:
        return self._cursor

    def start_live(self, renderable=None):
        """Start the Live display context."""
        if self._live is not None:
            return
        self._live = Live(
            renderable or Text(" "),
            console=self._console,
            refresh_per_second=REFRESH_RATE,
            transient=True,
        )
        self._live.start()

    def update(self, renderable):
        """Push a new renderable to the Live display."""
        if self._live is not None:
            self._live.update(renderable)

    def stop_live(self):
        """Stop the Live display context."""
        if self._live is not None:
            self._live.stop()
            self._live = None

    def is_live(self) -> bool:
        """Check if Live is currently active."""
        return self._live is not None

    def run_with_spinner(self, func, status: str = "Thinking...", *args, **kwargs):
        """
        Run a function while showing a spinner animation.
        The spinner runs in the Live display until the function completes.

        Usage:
            result = live_mgr.run_with_spinner(graph.invoke, "Thinking...", state)
        """
        import concurrent.futures

        self._spinner.start(status)
        self.start_live(self._spinner.tick())

        result = None
        error = None

        def _run():
            nonlocal result, error
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                error = e

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        try:
            while thread.is_alive():
                frame = self._spinner.tick()
                if frame:
                    self.update(frame)
                time.sleep(1.0 / REFRESH_RATE)
        finally:
            self._spinner.stop()
            self.stop_live()

        if error:
            raise error
        return result
