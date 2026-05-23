#!/usr/bin/env python3
"""restify-cli – tiny break‑reminder utility.

Features:
  • Configurable interval (minutes) via ``--interval``
  • Custom message via ``--message``
  • Optional desktop notification (macOS/Linux/Windows)
  • ``--no-notify`` to silence OS notifications

The script is deliberately small (< 150 LOC) and has no external runtime
dependencies except the optional ``win10toast`` package on Windows.
"""

import argparse
import sys
import time
import platform
from datetime import datetime

# ---------------------------------------------------------------------------
# Notification helpers – keep optional to avoid heavyweight deps
# ---------------------------------------------------------------------------

def _notify_linux(title: str, body: str) -> None:
    """Send a desktop notification on Linux using ``notify-send``.
    ``notify-send`` is part of libnotify and is typically available on most
    desktop environments. If it is missing, we silently ignore the error.
    """
    import subprocess
    try:
        subprocess.run(["notify-send", title, body], check=False)
    except Exception:
        pass


def _notify_macos(title: str, body: str) -> None:
    """Send a notification on macOS via AppleScript."""
    import subprocess
    script = f'''display notification "{body}" with title "{title}"'''
    try:
        subprocess.run(["osascript", "-e", script], check=False)
    except Exception:
        pass


def _notify_windows(title: str, body: str) -> None:
    """Send a toast on Windows using ``win10toast`` if installed.
    The import is done lazily to keep the dependency optional.
    """
    try:
        from win10toast import ToastNotifier
        ToastNotifier().show_toast(title, body, duration=5, threaded=True)
    except Exception:
        pass


def send_notification(title: str, body: str, enable: bool) -> None:
    if not enable:
        return
    system = platform.system()
    if system == "Linux":
        _notify_linux(title, body)
    elif system == "Darwin":
        _notify_macos(title, body)
    elif system == "Windows":
        _notify_windows(title, body)
    # Fallback: just print – handled by caller

# ---------------------------------------------------------------------------
# Core loop
# ---------------------------------------------------------------------------

def run(interval_min: int, message: str, notify: bool) -> None:
    interval_sec = interval_min * 60
    next_time = time.time() + interval_sec
    try:
        while True:
            now = time.time()
            if now >= next_time:
                timestamp = datetime.now().strftime("%H:%M:%S")
                line = f"[{timestamp}] Break time! {message}"
                print(line, flush=True)
                send_notification("Restify", message, notify)
                next_time = now + interval_sec
            # Sleep a short while to keep CPU usage low but stay responsive to Ctrl‑C
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nRestify stopped. Stay healthy!")
        sys.exit(0)

# ---------------------------------------------------------------------------
# Argument parsing entry‑point
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="restify",
        description="Tiny break reminder – prompts you every N minutes to take a 30‑second rest.",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=60,
        help="Interval between reminders, in minutes (default: 60).",
    )
    parser.add_argument(
        "-m",
        "--message",
        default="Take a 30‑second break!",
        help="Custom reminder text.",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="Suppress OS desktop notifications (console output only).",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()
    run(args.interval, args.message, not args.no_notify)


if __name__ == "__main__":
    main()
