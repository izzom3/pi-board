from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


def _try_detect_framebuffer_size() -> tuple[int, int] | None:
    # Typical format: "800,480" or "1920,1080"
    fb0 = Path("/sys/class/graphics/fb0/virtual_size")
    try:
        raw = fb0.read_text(encoding="utf-8").strip()
    except OSError:
        return None

    m = re.match(r"^(\d+),(\d+)$", raw)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def _try_detect_xrandr_size() -> tuple[int, int] | None:
    # Requires X11/Wayland session + xrandr in PATH. We parse the current mode marked with '*'.
    if not os.getenv("DISPLAY"):
        return None

    try:
        out = subprocess.check_output(["xrandr", "--current"], stderr=subprocess.DEVNULL, text=True)
    except Exception:
        return None

    for line in out.splitlines():
        if "*" not in line:
            continue
        m = re.search(r"(\d+)x(\d+)\s+\d+\.\d+\*", line)
        if m:
            return int(m.group(1)), int(m.group(2))
        m = re.search(r"(\d+)x(\d+)\s*\*", line)
        if m:
            return int(m.group(1)), int(m.group(2))

    return None


def detect_screen_size() -> tuple[int, int] | None:
    # Prefer X (desktop), fall back to framebuffer.
    return _try_detect_xrandr_size() or _try_detect_framebuffer_size()
