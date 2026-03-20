from flask import request

from app.common.auth import login_required
from app.common.response import success, fail
from . import finance_bp
from .models import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from .services import (
    create_record, list_records, update_record, delete_record,
    get_summary, get_trend,
)


@finance_bp.route('/categories', methods=['GET'])
@login_required
def categories():
    return success({
        "expense": EXPENSE_CATEGORIES,
        "income": INCOME_CATEGORIES,
    })


@finance_bp.route('/summary', methods=['GET'])
@login_required
def summary():
    month = request.args.get('month')
    if not month:
        return fail("month 参数必填")
    return success(get_summary(month))


@finance_bp.route('/trend', methods=['GET'])
@login_required
def trend():
    year = request.args.get('year', type=int)
    if not year:
        return fail("year 参数必填")
    return success(get_trend(year))


@finance_bp.route('/records', methods=['GET'])
@login_required
def index():
    month = request.args.get('month')
    record_type = request.args.get('type')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    return success(list_records(month, record_type, page, page_size))


@finance_bp.route('/records', methods=['POST'])
@login_required
def create():
    data = request.get_json(silent=True) or {}
    if not data.get('amount'):
        return fail("金额不能为空")
    if data.get('type') not in ('income', 'expense'):
        return fail("类型必须是 income 或 expense")
    record = create_record(data)
    return success(record, "添加成功")


@finance_bp.route('/records/<record_id>', methods=['PUT'])
@login_required
def update(record_id):
    data = request.get_json(silent=True) or {}
    record = update_record(record_id, data)
    if not record:
        return fail("记录不存在", 404)
    return success(record, "更新成功")


@finance_bp.route('/records/<record_id>', methods=['DELETE'])
@login_required
def delete(record_id):
    if not delete_record(record_id):
        return fail("记录不存在", 404)
    return success(None, "已删除")
