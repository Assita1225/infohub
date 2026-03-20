from flask import Blueprint

habits_bp = Blueprint('habits', __name__)

from . import routes  # noqa: E402, F401
