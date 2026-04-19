# Pi-Board

Pi-Board is a self-hosted dashboard intended to run on a Raspberry Pi (but it also runs on a normal PC). The long-term goal is a modular wall display with apps like **movie posters**, **todo**, **calendar**, and **news**.

Right now it ships working **Poster** and **News** apps:

### Poster App
- Upload/delete posters (PNG, JPG, JPEG, WEBP)
- Start slideshow — shuffle all, custom playlist, or single poster
- Stop slideshow
- Auto-rotates and scales to fit your (possibly rotated) display

### News App
- Fetches headlines from NewsData.io (free tier: 200 credits/day)
- Pre-configured feeds: Technology, Gaming, US News, MLB, Film & TV
- Caches results to minimize API calls (default: 30 min)
- **Display Mode**: Full-screen article slideshow for your wall display with 15-second auto-advance

## Quickstart (dev)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e '.[dev]'

# Copy env template and add your NewsData.io API key
cp .env.example .env
# Edit .env and set PIBOARD_NEWSDATA_API_KEY

flask --app pi_board.web run --host 0.0.0.0 --port 5000
```

Then open:
- http://localhost:5000
- or from another device on your LAN: `http://<pi-ip>:5000`

## Running on the Pi

For showing images full-screen, Pi-Board uses an external image viewer.

### Display backend options
- **`feh`** — recommended if you run Raspberry Pi OS Desktop (X11). `sudo apt install feh`
- **`fbi`** — framebuffer console only (no desktop). `sudo apt install fbi`

> **Important:** `fbi` will not work if a desktop environment is running. Use `feh` on Pi OS Desktop.

Set backend in `.env`:
```
PIBOARD_DISPLAY_BACKEND=feh
```

### Auto-start with systemd

```bash
sudo cp deploy/pi-board.service /etc/systemd/system/
sudo systemctl enable pi-board.service
sudo systemctl start pi-board.service

# Follow logs
sudo journalctl -u pi-board -f
```

## Configuration

Set in `.env` (copy from `.env.example`):

### General
| Variable | Default | Description |
|----------|---------|-------------|
| `PIBOARD_HOST` | `0.0.0.0` | Bind address |
| `PIBOARD_PORT` | `5000` | |

### Posters / Display
| Variable | Default | Description |
|----------|---------|-------------|
| `PIBOARD_POSTERS_DIR` | `./posters` | Where uploaded posters are stored |
| `PIBOARD_STATE_DIR` | `./.piboard` | PID files, image cache, news cache |
| `PIBOARD_DISPLAY_BACKEND` | `feh` | `feh` \| `fbi` \| `dummy` |
| `PIBOARD_SLIDESHOW_DELAY_SECONDS` | `10` | Seconds between poster transitions |
| `PIBOARD_ROTATE_DEGREES_CLOCKWISE` | `90` | For a physically rotated portrait monitor |
| `PIBOARD_FIT_MODE` | `stretch` | `stretch` \| `cover` \| `contain` |
| `PIBOARD_SCREEN_WIDTH` / `PIBOARD_SCREEN_HEIGHT` | (auto-detected) | Override screen size |

### News
| Variable | Default | Description |
|----------|---------|-------------|
| `PIBOARD_NEWSDATA_API_KEY` | — | Get a free key at https://newsdata.io |
| `PIBOARD_NEWS_CACHE_MAX_AGE_SECONDS` | `1800` | 30 min |

## API

`GET /api/status` — returns current display state and news cache summary. Useful for debugging from a phone without opening the full UI.

```json
{
  "display": {"backend": "feh", "running": true},
  "news": {
    "technology": {"cached": true, "stale": false, "article_count": 10, "age_seconds": 342}
  },
  "settings": {"display_backend": "feh", "rotate_degrees_clockwise": 90, "fit_mode": "stretch", "slideshow_delay_seconds": 10}
}
```

## Development

```bash
pytest                          # run all tests
ruff check . && ruff format .   # lint + format
rm -rf .piboard/rotated/* .piboard/news_cache/*   # clear caches
```

## Notes

- Do **not** commit copyrighted posters to git. The repo ignores common image extensions.
- The `todo` and `calendar` apps are placeholders.
- No authentication — designed for trusted local networks only.

## License

MIT
