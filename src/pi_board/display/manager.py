from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .backends import DisplayBackend, DummyBackend, FbiBackend, FehBackend

BackendName = Literal["feh", "fbi", "dummy"]


@dataclass
class DisplayManager:
    backend: DisplayBackend

    def stop(self) -> None:
        self.backend.stop()

    def show_single(self, path: Path) -> None:
        self.backend.show_single(path)

    def start_slideshow(self, *, paths: list[Path], delay_seconds: int, shuffle: bool) -> None:
        self.backend.start_slideshow(paths=paths, delay_seconds=delay_seconds, shuffle=shuffle)


def create_display_manager(backend_name: str, *, state_dir: Path) -> DisplayManager:
    name = (backend_name or "").strip().lower()
    if name == "feh":
        backend = FehBackend(state_dir=state_dir)
    elif name == "fbi":
        backend = FbiBackend(state_dir=state_dir)
    elif name == "dummy":
        backend = DummyBackend(state_dir=state_dir)
    else:
        backend = FehBackend(state_dir=state_dir)
    return DisplayManager(backend=backend)
