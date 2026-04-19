from __future__ import annotations

from flask import Blueprint

bp = Blueprint("piboard", __name__)

# Import submodules to register their routes on bp
from . import news_routes, posters_routes, status  # noqa: E402, F401
