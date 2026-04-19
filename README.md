# Pi-Board

Pi-Board is a self-hosted dashboard intended to run on a Raspberry Pi (but it also runs on a normal PC). The long-term goal is a modular wall display with apps like **movie posters**, **todo**, **calendar**, and **news**.

Right now it ships working **Poster** and **News** apps:

### Poster App
- Upload/delete posters
- Start slideshow (shuffle all)
- Start slideshow from a custom selection
- Show a single poster
- Stop slideshow
- Auto-rotates and scales to fit your (possibly rotated) display

### News App
- Fetches headlines from NewsData.io (free tier: 200 credits/day)
- Pre-configured feeds: Technology, Gaming, US News
- Caches results to minimize API calls (default: 30 min)
- **Display Mode**: Full-screen article slideshow for your wall display
- Large, readable titles designed for viewing from a few feet away

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

## Running on the Pi (recommended)

For showing images full-screen, Pi-Board uses an external viewer backend.

### Backend options
- **feh** (recommended if you run a desktop / X11 / Wayland): `sudo apt install feh`
- **fbi** (framebuffer console, no desktop): `sudo apt install fbi`

Select backend via env var:
- `PIBOARD_DISPLAY_BACKEND=feh` (default)
- `PIBOARD_DISPLAY_BACKEND=fbi`

## Configuration

Set these environment variables (or put them in `.env`):

### General
- `PIBOARD_HOST` (default: `0.0.0.0`)
- `PIBOARD_PORT` (default: `5000`)

### Posters / Display
- `PIBOARD_POSTERS_DIR` (default: `./posters`)
- `PIBOARD_DISPLAY_BACKEND` (`feh` | `fbi` | `dummy`)
- `PIBOARD_SLIDESHOW_DELAY_SECONDS` (default: `10`)
- `PIBOARD_ROTATE_DEGREES_CLOCKWISE` (default: `90`)
- `PIBOARD_FIT_MODE` (`stretch` | `cover` | `contain`, default: `stretch`)
- `PIBOARD_SCREEN_WIDTH` / `PIBOARD_SCREEN_HEIGHT` (optional overrides)

### News
- `PIBOARD_NEWSDATA_API_KEY` — Get your free key at https://newsdata.io
- `PIBOARD_NEWS_CACHE_MAX_AGE_SECONDS` (default: `1800` = 30 min)

## Notes

- Do **not** commit copyrighted posters to git. The repo ignores common image extensions by default.
- The `todo` and `calendar` apps are placeholders for now.

## License

MIT
