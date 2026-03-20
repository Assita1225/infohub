from flask import Blueprint

overview_bp = Blueprint('overview', __name__)

from . import routes  # noqa: E402, F401
