from app.common.auth import login_required
from app.common.response import success
from . import overview_bp
from .services import get_overview_stats


@overview_bp.route('/stats', methods=['GET'])
@login_required
def stats():
    return success(get_overview_stats())
