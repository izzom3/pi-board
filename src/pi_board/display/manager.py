from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pi_board.images import prepare_for_display

from .backends import DisplayBackend, DummyBackend, FbiBackend, FehBackend

BackendName = Literal["feh", "fbi", "dummy"]


@dataclass
class DisplayManager:
    backend: DisplayBackend
    rotate_degrees_clockwise: int
    rotated_cache_dir: Path
    target_size: tuple[int, int] | None
    fit_mode: str

    def stop(self) -> None:
        self.backend.stop()

    def show_single(self, path: Path) -> None:
        prepared = self._prepare_one(path)
        self.backend.show_single(prepared)

    def start_slideshow(self, *, paths: list[Path], delay_seconds: int, shuffle: bool) -> None:
        prepared = self._prepare_many(paths)
        self.backend.start_slideshow(paths=prepared, delay_seconds=delay_seconds, shuffle=shuffle)

    def _prepare_one(self, path: Path) -> Path:
        try:
            return prepare_for_display(
                path,
                cache_dir=self.rotated_cache_dir,
                rotate_degrees_clockwise=self.rotate_degrees_clockwise,
                target_size=self.target_size,
                fit_mode=self.fit_mode,
            )
        except Exception:
            return path

    def _prepare_many(self, paths: list[Path]) -> list[Path]:
        if int(self.rotate_degrees_clockwise) % 360 == 0 and self.target_size is None:
            return paths
        prepared: list[Path] = []
        for p in paths:
            prepared.append(self._prepare_one(p))
        return prepared


def create_display_manager(
    backend_name: str,
    *,
    state_dir: Path,
    rotate_degrees_clockwise: int,
    screen_width: int | None,
    screen_height: int | None,
    fit_mode: str,
) -> DisplayManager:
    name = (backend_name or "").strip().lower()
    if name == "feh":
        backend = FehBackend(state_dir=state_dir)
    elif name == "fbi":
        backend = FbiBackend(state_dir=state_dir)
    elif name == "dummy":
        backend = DummyBackend(state_dir=state_dir)
    else:
        backend = FehBackend(state_dir=state_dir)

    rotated_cache_dir = state_dir / "rotated"
    return DisplayManager(
        backend=backend,
        rotate_degrees_clockwise=int(rotate_degrees_clockwise),
        rotated_cache_dir=rotated_cache_dir,
        target_size=(int(screen_width), int(screen_height))
        if screen_width is not None and screen_height is not None
        else None,
        fit_mode=(fit_mode or "stretch").strip().lower(),
    )
