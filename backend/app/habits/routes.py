from flask import request

from app.common.auth import login_required
from app.common.response import success, fail
from . import habits_bp
from .services import (
    create_habit, list_habits, update_habit, delete_habit,
    check_in, cancel_check_in, get_history, get_stats, get_today_checkins,
)


# ── 统计（静态路径，必须在 /<id> 之前）──

@habits_bp.route('/stats', methods=['GET'])
@login_required
def stats():
    return success(get_stats())


# ── 列表 & 创建 ──

@habits_bp.route('/', methods=['GET'])
@login_required
def index():
    habits = list_habits()
    today_set = get_today_checkins()
    for h in habits:
        h["checked_today"] = h["_id"] in today_set
    return success(habits)


@habits_bp.route('/', methods=['POST'])
@login_required
def create():
    data = request.get_json(silent=True) or {}
    if not data.get('name', '').strip():
        return fail("名称不能为空")
    habit = create_habit(data)
    return success(habit, "创建成功")


# ── 单条操作 ──

@habits_bp.route('/<habit_id>', methods=['PUT'])
@login_required
def update(habit_id):
    data = request.get_json(silent=True) or {}
    habit = update_habit(habit_id, data)
    if not habit:
        return fail("习惯不存在", 404)
    return success(habit, "更新成功")


@habits_bp.route('/<habit_id>', methods=['DELETE'])
@login_required
def delete(habit_id):
    if not delete_habit(habit_id):
        return fail("习惯不存在", 404)
    return success(None, "已删除")


# ── 打卡 ──

@habits_bp.route('/<habit_id>/check-in', methods=['POST'])
@login_required
def do_check_in(habit_id):
    result = check_in(habit_id)
    if result is None:
        return fail("习惯不存在", 404)
    return success(result, "打卡成功")


@habits_bp.route('/<habit_id>/check-in', methods=['DELETE'])
@login_required
def undo_check_in(habit_id):
    if not cancel_check_in(habit_id):
        return fail("今日未打卡", 400)
    return success(None, "已取消打卡")


# ── 历史记录 ──

@habits_bp.route('/<habit_id>/history', methods=['GET'])
@login_required
def history(habit_id):
    year = request.args.get('year', 2026, type=int)
    dates = get_history(habit_id, year)
    return success(dates)
