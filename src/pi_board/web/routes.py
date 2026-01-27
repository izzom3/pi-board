from __future__ import annotations

import secrets
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from pi_board.posters import list_posters, safe_join_posters_dir

bp = Blueprint("piboard", __name__)


def _posters_dir() -> Path:
    return current_app.config["PIBOARD_POSTERS_DIR"]


def _display():
    return current_app.config["PIBOARD_DISPLAY"]


@bp.get("/")
def home() -> str:
    posters = list_posters(_posters_dir())
    return render_template("posters.html", posters=posters)


@bp.get("/apps/<app_name>")
def placeholder_app(app_name: str):
    if app_name not in {"todo", "calendar", "news"}:
        return redirect(url_for("piboard.home"))
    return render_template("placeholder.html", app_name=app_name)


@bp.get("/media/posters/<path:filename>")
def media_poster(filename: str):
    # send_from_directory protects against traversal, but we also keep allowed-extension constraints
    safe_join_posters_dir(_posters_dir(), filename)
    return send_from_directory(_posters_dir(), filename)


@bp.post("/posters/upload")
def posters_upload():
    if "file" not in request.files:
        return redirect(url_for("piboard.home"))

    file = request.files["file"]
    if not file or not file.filename:
        return redirect(url_for("piboard.home"))

    filename = Path(file.filename).name
    try:
        target = safe_join_posters_dir(_posters_dir(), filename)
    except ValueError:
        return redirect(url_for("piboard.home"))

    # avoid overwriting by default
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        filename = f"{stem}-{secrets.token_hex(3)}{suffix}"
        target = safe_join_posters_dir(_posters_dir(), filename)

    file.save(target)
    return redirect(url_for("piboard.home"))


@bp.post("/api/posters/delete")
def api_delete_poster():
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename is required"}), 400

    try:
        path = safe_join_posters_dir(_posters_dir(), filename)
    except ValueError:
        return jsonify({"error": "invalid filename"}), 400

    if path.exists():
        path.unlink()
    return jsonify({"status": "deleted", "filename": filename})


@bp.post("/api/display/stop")
def api_display_stop():
    _display().stop()
    return jsonify({"status": "stopped"})


@bp.post("/api/display/start")
def api_display_start():
    data = request.get_json(silent=True) or {}

    mode = (data.get("mode") or "random").strip().lower()
    delay = data.get("delay_seconds")
    shuffle = bool(data.get("shuffle", True))

    settings = current_app.config["PIBOARD_SETTINGS"]
    delay_seconds = (
        int(delay)
        if isinstance(delay, (int, float, str)) and str(delay).isdigit()
        else settings.slideshow_delay_seconds
    )

    posters = list_posters(_posters_dir())
    poster_paths = [(_posters_dir() / p) for p in posters]

    if mode == "random":
        import random

        random.shuffle(poster_paths)
        _display().start_slideshow(paths=poster_paths, delay_seconds=delay_seconds, shuffle=True)
        return jsonify({"status": "started", "mode": "random", "count": len(poster_paths)})

    if mode == "playlist":
        selected = data.get("posters") or []
        if not isinstance(selected, list) or not selected:
            return jsonify({"error": "posters list required"}), 400
        paths: list[Path] = []
        for name in selected:
            try:
                p = safe_join_posters_dir(_posters_dir(), str(name))
            except ValueError:
                continue
            if p.exists():
                paths.append(p)
        if not paths:
            return jsonify({"error": "no valid posters"}), 400
        _display().start_slideshow(paths=paths, delay_seconds=delay_seconds, shuffle=shuffle)
        return jsonify(
            {
                "status": "started",
                "mode": "playlist",
                "count": len(paths),
                "shuffle": shuffle,
            }
        )

    if mode == "single":
        filename = data.get("poster")
        if not filename:
            return jsonify({"error": "poster is required"}), 400
        try:
            path = safe_join_posters_dir(_posters_dir(), str(filename))
        except ValueError:
            return jsonify({"error": "invalid poster"}), 400
        if not path.exists():
            return jsonify({"error": "poster not found"}), 404
        _display().show_single(path)
        return jsonify({"status": "started", "mode": "single", "poster": path.name})

    return jsonify({"error": "invalid mode"}), 400
