from flask import Blueprint

recommend_bp = Blueprint('recommend', __name__)

from . import routes  # noqa: E402, F401
