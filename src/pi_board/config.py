from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pi_board.screen import detect_screen_size


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
    state_dir: Path
    display_backend: str
    slideshow_delay_seconds: int
    rotate_degrees_clockwise: int
    screen_width: int | None
    screen_height: int | None
    fit_mode: str
    newsdata_api_key: str
    news_cache_max_age_seconds: int


def load_settings() -> Settings:
    import os

    host = os.getenv("PIBOARD_HOST", "0.0.0.0")
    port = _env_int("PIBOARD_PORT", 5000)
    posters_dir = Path(os.getenv("PIBOARD_POSTERS_DIR", "./posters")).expanduser().resolve()
    state_dir = Path(os.getenv("PIBOARD_STATE_DIR", ".piboard")).expanduser().resolve()
    display_backend = os.getenv("PIBOARD_DISPLAY_BACKEND", "feh").strip().lower()
    slideshow_delay_seconds = _env_int("PIBOARD_SLIDESHOW_DELAY_SECONDS", 10)
    rotate_degrees_clockwise = _env_int("PIBOARD_ROTATE_DEGREES_CLOCKWISE", 90)

    screen_width = _env_int("PIBOARD_SCREEN_WIDTH", 0) or None
    screen_height = _env_int("PIBOARD_SCREEN_HEIGHT", 0) or None

    if screen_width is None or screen_height is None:
        detected = detect_screen_size()
        if detected:
            screen_width, screen_height = detected

    fit_mode = os.getenv("PIBOARD_FIT_MODE", "stretch").strip().lower()

    newsdata_api_key = os.getenv("PIBOARD_NEWSDATA_API_KEY", "").strip()
    news_cache_max_age_seconds = _env_int("PIBOARD_NEWS_CACHE_MAX_AGE_SECONDS", 1800)

    return Settings(
        host=host,
        port=port,
        posters_dir=posters_dir,
        state_dir=state_dir,
        display_backend=display_backend,
        slideshow_delay_seconds=slideshow_delay_seconds,
        rotate_degrees_clockwise=rotate_degrees_clockwise,
        screen_width=screen_width,
        screen_height=screen_height,
        fit_mode=fit_mode,
        newsdata_api_key=newsdata_api_key,
        news_cache_max_age_seconds=news_cache_max_age_seconds,
    )
