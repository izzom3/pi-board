---
name: pi-board
description: Flask-based self-hosted dashboard for a wall-mounted Raspberry Pi. Serves poster slideshows and NewsData.io headlines; controllable over the LAN.
---

# Pi-Board

Self-hosted LAN dashboard. Flask web UI on any device; rendering happens on the Pi via a local image viewer (`feh` on desktop, `fbi` on console). Target hardware: Raspberry Pi 5, Raspberry Pi OS Desktop, portrait-mounted HDMI monitor. Also runs on a normal Linux dev machine.

## Layout

```
src/pi_board/
  config.py              # Settings dataclass, PIBOARD_* env vars
  screen.py              # xrandr / framebuffer size detection
  images.py              # PIL rotate/fit + SHA1-keyed cache in .piboard/rotated/
  posters.py             # list_posters, safe_join_posters_dir, ALLOWED_EXTENSIONS
  news.py                # NewsService, DEFAULT_FEEDS, JSON cache in .piboard/news_cache/
  display/
    backends.py          # DisplayBackend Protocol + Feh/Fbi/Dummy
    manager.py           # DisplayManager: preprocess then delegate to backend
  web/
    __init__.py          # create_app factory, stores services in app.config
    routes/
      __init__.py        # Blueprint "piboard" + imports submodules
      posters_routes.py  # Poster upload/delete/media + display start/stop
      news_routes.py     # News browsing + display mode
      status.py          # GET /api/status
    templates/ static/

tests/
  conftest.py            # app + client fixtures (DummyBackend, tmp_path)
  test_posters.py        # posters + image processing unit tests
  test_news.py           # NewsService cache + API call tests
  test_display.py        # DisplayManager + backend tests
  test_routes.py         # Flask test client smoke tests

deploy/
  pi-board.service       # Systemd unit for auto-start on Pi
```

## Runtime model

- Web layer never renders images itself. `POST /api/display/start` asks `DisplayManager` to preprocess (rotate + fit) and spawn `feh`/`fbi` via `subprocess.Popen`. The PID is stored in `<state_dir>/display.pid`; `stop` kills it + `pkill -x feh|fbi` as belt-and-braces.
- Preprocessed images are cached in `<state_dir>/rotated/` keyed by SHA1 of path + params. Processing is skipped entirely if rotation is 0° and no target size.
- News cache is JSON per `(feed_key, page)` under `<state_dir>/news_cache/`. `get_feed()` falls back to stale cache if the API call fails — you always get something to display.
- `load_dotenv(override=False)` in app factory — real env vars win over `.env`. Don't reorder.

## Services live on app.config

| Key | Type |
|-----|------|
| `PIBOARD_SETTINGS` | `Settings` dataclass |
| `PIBOARD_POSTERS_DIR` | `Path` |
| `PIBOARD_DISPLAY` | `DisplayManager` |
| `PIBOARD_NEWS` | `NewsService` |

Route helpers `_settings()`, `_display()`, `_news()`, `_posters_dir()` read them from `current_app.config`.

## Env vars (all `PIBOARD_*`)

| Var | Default | Notes |
|-----|---------|-------|
| `HOST` | `0.0.0.0` | |
| `PORT` | `5000` | |
| `POSTERS_DIR` | `./posters` | |
| `STATE_DIR` | `./.piboard` | PID + cache root; must match `WorkingDirectory` in systemd unit |
| `DISPLAY_BACKEND` | `feh` | `feh` \| `fbi` \| `dummy` |
| `SLIDESHOW_DELAY_SECONDS` | `10` | |
| `ROTATE_DEGREES_CLOCKWISE` | `90` | Portrait monitor |
| `FIT_MODE` | `stretch` | `stretch` \| `cover` \| `contain` |
| `SCREEN_WIDTH/HEIGHT` | auto | Overrides xrandr detection |
| `NEWSDATA_API_KEY` | (required for news) | Free tier: 200 credits/day |
| `NEWS_CACHE_MAX_AGE_SECONDS` | `1800` | |

## Known footguns

- **`fbi` only works in console** (no X running). On Pi OS Desktop it launches but won't appear — use `feh`.
- **`random` mode pre-shuffles in Python and passes `shuffle=False` to the backend** — so feh does NOT add `-z`. `playlist` mode with `shuffle=True` does use feh's `-z` flag. Don't conflate the two modes.
- **`DummyBackend.start_slideshow` saves `os.getpid()`** — calling `stop()` on it sends SIGTERM to the current process. Tests must not call `stop()` on a running DummyBackend; unlink the PID file directly instead.
- **`DisplayManager._prepare_one` silently falls back** to the unrotated original on any PIL error — this is intentional but it logs a WARNING. If images look wrong, check the log.
- **State dir must match WorkingDirectory** in the systemd unit. `PIBOARD_STATE_DIR` defaults to `.piboard` relative to CWD. The unit sets `WorkingDirectory=/home/mattizzo/projects/pi-board`, so the state lands at `/home/mattizzo/projects/pi-board/.piboard` unless you override the env var.
- **Path traversal guard in `safe_join_posters_dir`** — logic is correct but reads inverted. Don't "simplify" it without a test.

## Endpoints (all on Blueprint `piboard`)

```
GET  /                              Poster gallery
GET  /apps/<todo|calendar>          Placeholder
GET  /media/posters/<filename>      Serve poster image
POST /posters/upload                multipart/form-data
POST /api/posters/delete            {"filename": "..."}
POST /api/display/start             {"mode": "random"|"playlist"|"single", ...}
POST /api/display/stop
GET  /news                          News landing (all feed summaries)
GET  /news/feed/<feed_key>          Paginated feed
GET  /news/article/<article_id>     Single article
GET  /news/display/<feed_key>       Full-screen slideshow (15s auto-advance)
POST /api/news/refresh              {"feed_key": "..."} or {} for all
GET  /api/status                    Display running state + news cache summary
```

## DEFAULT_FEEDS (news.py)

`technology`, `gaming`, `us`, `mlb`, `film`. Each entry copies `q`, `qInTitle`, `category`, `country`, `language`, `prioritydomain` to the API params. Per-feed `prioritydomain` is respected; it defaults to `"medium"` if not set. All feeds set `language=en` and `removeduplicate=1`.

## Dev workflow

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check . && ruff format .
flask --app pi_board.web run --host 0.0.0.0 --port 5000
```

Clear caches: `rm -rf .piboard/rotated/* .piboard/news_cache/*`

## Auto-start (Pi)

```bash
sudo cp deploy/pi-board.service /etc/systemd/system/
sudo systemctl enable pi-board.service
sudo systemctl start pi-board.service
sudo journalctl -u pi-board -f   # follow logs
```

## Conventions

- New display backends: implement `DisplayBackend` Protocol in [backends.py](src/pi_board/display/backends.py), inherit `_BaseBackend` for PID/playlist file handling, add a branch in `create_display_manager`.
- New news feeds: add a key to `DEFAULT_FEEDS` in [news.py](src/pi_board/news.py). Templates iterate `service.feeds` — no template changes needed.
- New apps (todo/calendar): add routes in a new `src/pi_board/web/routes/<app>_routes.py` and import it in [routes/__init__.py](src/pi_board/web/routes/__init__.py). Follow the news module pattern — service class + file-backed state under `<state_dir>/<app>/`.
- Subprocess calls always pass a list (never `shell=True`). User-supplied strings must never reach the command line.
- LAN-only app, no auth. Do not expose to the internet.
