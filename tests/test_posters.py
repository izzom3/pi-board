from pathlib import Path

import pytest

from pi_board.images import prepare_for_display, rotate_image_clockwise
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


def test_rotate_image_clockwise_creates_cached_file(tmp_path: Path):
    from PIL import Image

    input_path = tmp_path / "in.png"
    out_dir = tmp_path / "cache"

    Image.new("RGB", (10, 20), color=(255, 0, 0)).save(input_path)

    rotated = rotate_image_clockwise(input_path, cache_dir=out_dir, degrees=90)
    assert rotated.exists()

    with Image.open(rotated) as img:
        assert img.size == (20, 10)


def test_prepare_for_display_stretch_to_target(tmp_path: Path):
    from PIL import Image

    input_path = tmp_path / "in.png"
    out_dir = tmp_path / "cache"

    Image.new("RGB", (10, 20), color=(255, 0, 0)).save(input_path)

    prepared = prepare_for_display(
        input_path,
        cache_dir=out_dir,
        rotate_degrees_clockwise=90,
        target_size=(300, 500),
        fit_mode="stretch",
    )

    with Image.open(prepared) as img:
        assert img.size == (300, 500)
