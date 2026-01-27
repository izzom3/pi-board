from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    import os

    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    posters_dir: Path
    display_backend: str
    slideshow_delay_seconds: int


def load_settings() -> Settings:
    import os

    host = os.getenv("PIBOARD_HOST", "0.0.0.0")
    port = _env_int("PIBOARD_PORT", 5000)
    posters_dir = Path(os.getenv("PIBOARD_POSTERS_DIR", "./posters")).expanduser().resolve()
    display_backend = os.getenv("PIBOARD_DISPLAY_BACKEND", "feh").strip().lower()
    slideshow_delay_seconds = _env_int("PIBOARD_SLIDESHOW_DELAY_SECONDS", 10)

    return Settings(
        host=host,
        port=port,
        posters_dir=posters_dir,
        display_backend=display_backend,
        slideshow_delay_seconds=slideshow_delay_seconds,
    )
