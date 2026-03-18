from flask import Blueprint

rss_bp = Blueprint('rss', __name__)

from . import routes  # noqa: E402, F401
