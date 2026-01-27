from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


def rotate_image_clockwise(
    input_path: Path,
    *,
    cache_dir: Path,
    degrees: int,
) -> Path:
    """Rotate an image clockwise by `degrees` and return the cached output path.

    The rotated file is written under `cache_dir` and reused based on input file
    metadata (mtime/size) + rotation degrees.
    """

    degrees = int(degrees) % 360
    if degrees == 0:
        return input_path

    cache_dir.mkdir(parents=True, exist_ok=True)

    st = input_path.stat()
    key = f"{input_path.resolve()}|{st.st_mtime_ns}|{st.st_size}|{degrees}".encode()
    digest = hashlib.sha1(key).hexdigest()[:16]

    suffix = input_path.suffix.lower() or ".png"
    output_path = cache_dir / f"{input_path.stem}-{digest}{suffix}"
    if output_path.exists():
        return output_path

    # Write atomically (temp file then rename) to avoid partial files.
    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        # PIL's rotate is counter-clockwise for positive degrees.
        rotated = img.rotate(-degrees, expand=True)

        with tempfile.NamedTemporaryFile(
            mode="wb",
            delete=False,
            dir=cache_dir,
            suffix=suffix,
        ) as tmp:
            tmp_path = Path(tmp.name)

        try:
            rotated.save(tmp_path)
            tmp_path.replace(output_path)
        finally:
            if tmp_path.exists() and tmp_path != output_path:
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    return output_path


def prepare_for_display(
    input_path: Path,
    *,
    cache_dir: Path,
    rotate_degrees_clockwise: int,
    target_size: tuple[int, int] | None,
    fit_mode: str,
) -> Path:
    """Rotate + fit an image for the display.

    fit_mode:
    - stretch: fill the display completely (may distort aspect ratio)
    - cover: fill the display by cropping (keeps aspect ratio)
    - contain: keep aspect ratio with letterboxing
    """

    rotate_degrees_clockwise = int(rotate_degrees_clockwise) % 360
    fit_mode = (fit_mode or "stretch").strip().lower()

    if target_size is not None:
        tw, th = target_size
        if tw <= 0 or th <= 0:
            target_size = None

    if rotate_degrees_clockwise == 0 and target_size is None:
        return input_path

    cache_dir.mkdir(parents=True, exist_ok=True)

    st = input_path.stat()
    key = (
        f"{input_path.resolve()}|{st.st_mtime_ns}|{st.st_size}|{rotate_degrees_clockwise}|"
        f"{target_size}|{fit_mode}"
    ).encode()
    digest = hashlib.sha1(key).hexdigest()[:16]

    suffix = input_path.suffix.lower() or ".png"
    output_path = cache_dir / f"{input_path.stem}-{digest}{suffix}"
    if output_path.exists():
        return output_path

    try:
        resample = Image.Resampling.LANCZOS  # Pillow >= 10
    except AttributeError:  # pragma: no cover
        resample = Image.LANCZOS

    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        if rotate_degrees_clockwise:
            img = img.rotate(-rotate_degrees_clockwise, expand=True)

        if target_size is not None:
            if fit_mode == "contain":
                inner = ImageOps.contain(img, target_size, method=resample)
                canvas = Image.new(inner.mode, target_size, 0)
                x = (target_size[0] - inner.size[0]) // 2
                y = (target_size[1] - inner.size[1]) // 2
                canvas.paste(inner, (x, y))
                img = canvas
            elif fit_mode == "cover":
                img = ImageOps.fit(img, target_size, method=resample, centering=(0.5, 0.5))
            else:
                # stretch
                img = img.resize(target_size, resample=resample)

        with tempfile.NamedTemporaryFile(
            mode="wb",
            delete=False,
            dir=cache_dir,
            suffix=suffix,
        ) as tmp:
            tmp_path = Path(tmp.name)

        try:
            img.save(tmp_path)
            tmp_path.replace(output_path)
        finally:
            if tmp_path.exists() and tmp_path != output_path:
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    return output_path
