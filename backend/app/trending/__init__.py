from flask import Blueprint

trending_bp = Blueprint('trending', __name__)

from . import routes  # noqa: E402, F401
