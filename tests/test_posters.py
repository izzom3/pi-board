from pathlib import Path

import pytest

from pi_board.posters import is_allowed_filename, list_posters, safe_join_posters_dir


def test_allowed_extensions():
    assert is_allowed_filename("a.jpg")
    assert is_allowed_filename("a.jpeg")
    assert is_allowed_filename("a.png")
    assert is_allowed_filename("a.webp")
    assert not is_allowed_filename("a.gif")
    assert not is_allowed_filename("noext")


def test_safe_join_blocks_traversal(tmp_path: Path):
    with pytest.raises(ValueError):
        safe_join_posters_dir(tmp_path, "../x.jpg")


def test_list_posters_sorted(tmp_path: Path):
    (tmp_path / "b.jpg").write_bytes(b"x")
    (tmp_path / "A.jpg").write_bytes(b"x")
    (tmp_path / "c.txt").write_bytes(b"x")

    assert list_posters(tmp_path) == ["A.jpg", "b.jpg"]
