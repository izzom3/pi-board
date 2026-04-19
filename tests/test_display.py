from __future__ import annotations

from pathlib import Path

from PIL import Image

from pi_board.display.manager import DisplayManager, create_display_manager


def _dummy_manager(tmp_path: Path, rotate: int = 0) -> DisplayManager:
    state_dir = tmp_path / ".piboard"
    return create_display_manager(
        "dummy",
        state_dir=state_dir,
        rotate_degrees_clockwise=rotate,
        screen_width=None,
        screen_height=None,
        fit_mode="stretch",
    )


def _make_image(tmp_path: Path, name: str = "test.png") -> Path:
    p = tmp_path / name
    Image.new("RGB", (100, 200)).save(p)
    return p


def test_dummy_backend_stop_noop(tmp_path: Path):
    mgr = _dummy_manager(tmp_path)
    mgr.stop()  # no PID file, should not raise


def test_dummy_backend_show_single(tmp_path: Path):
    img = _make_image(tmp_path)
    mgr = _dummy_manager(tmp_path)
    mgr.show_single(img)
    # DummyBackend saves os.getpid(); the current process is alive → is_running() True
    assert mgr.is_running()
    mgr.backend.pid_file.unlink(missing_ok=True)


def test_dummy_backend_start_slideshow(tmp_path: Path):
    imgs = [_make_image(tmp_path, f"img{i}.png") for i in range(3)]
    mgr = _dummy_manager(tmp_path)
    mgr.start_slideshow(paths=imgs, delay_seconds=5, shuffle=False)
    # DummyBackend saves os.getpid() — the current process is running so is_running() is True
    assert mgr.is_running()
    # Clear the PID file directly to simulate stop without sending SIGTERM to ourselves
    mgr.backend.pid_file.unlink(missing_ok=True)
    assert not mgr.is_running()


def test_backend_label(tmp_path: Path):
    mgr = _dummy_manager(tmp_path)
    assert mgr.backend_label() == "dummy"


def test_prepare_one_returns_original_on_bad_file(tmp_path: Path, caplog):
    """Broken image falls back to original path and emits a warning."""
    import logging

    mgr = _dummy_manager(tmp_path, rotate=90)
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")

    with caplog.at_level(logging.WARNING, logger="pi_board.display.manager"):
        result = mgr._prepare_one(bad)

    assert result == bad
    assert any("Failed to preprocess" in r.message for r in caplog.records)


def test_prepare_many_skips_processing_when_no_rotation_no_target(tmp_path: Path):
    """With 0° rotation and no target size, images are returned as-is."""
    imgs = [_make_image(tmp_path, f"img{i}.png") for i in range(2)]
    mgr = _dummy_manager(tmp_path, rotate=0)
    result = mgr._prepare_many(imgs)
    assert result == imgs


def test_feh_shuffle_flag_added(tmp_path: Path):
    """FehBackend builds command with -z when shuffle=True."""
    from pi_board.display.backends import FehBackend

    backend = FehBackend(state_dir=tmp_path)
    img = _make_image(tmp_path)

    captured_cmd = []


    def fake_popen(cmd, **_kwargs):
        captured_cmd.extend(cmd)
        m = type("P", (), {"pid": 9999})()
        return m

    import unittest.mock as mock

    with mock.patch("pi_board.display.backends.subprocess.Popen", side_effect=fake_popen):
        with mock.patch("pi_board.display.backends.subprocess.run"):
            backend.start_slideshow(paths=[img], delay_seconds=5, shuffle=True)

    assert "-z" in captured_cmd


def test_feh_no_shuffle_flag_omitted(tmp_path: Path):
    """FehBackend omits -z when shuffle=False."""
    from pi_board.display.backends import FehBackend

    backend = FehBackend(state_dir=tmp_path)
    img = _make_image(tmp_path)
    captured_cmd = []

    import unittest.mock as mock

    def fake_popen(cmd, **_kwargs):
        captured_cmd.extend(cmd)
        return type("P", (), {"pid": 9999})()

    with mock.patch("pi_board.display.backends.subprocess.Popen", side_effect=fake_popen):
        with mock.patch("pi_board.display.backends.subprocess.run"):
            backend.start_slideshow(paths=[img], delay_seconds=5, shuffle=False)

    assert "-z" not in captured_cmd
