from __future__ import annotations

from pathlib import Path

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def is_allowed_filename(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def list_posters(posters_dir: Path) -> list[str]:
    if not posters_dir.exists():
        return []
    posters: list[str] = []
    for p in posters_dir.iterdir():
        if p.is_file() and is_allowed_filename(p.name):
            posters.append(p.name)
    posters.sort(key=lambda s: s.lower())
    return posters


def safe_join_posters_dir(posters_dir: Path, filename: str) -> Path:
    if not is_allowed_filename(filename):
        raise ValueError("Unsupported file extension")

    # Prevent path traversal
    candidate = (posters_dir / filename).resolve()
    posters_dir_resolved = posters_dir.resolve()
    if posters_dir_resolved not in candidate.parents and candidate != posters_dir_resolved:
        raise ValueError("Invalid filename")
    return candidate
