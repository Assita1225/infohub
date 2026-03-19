from flask import request

from app.common.auth import login_required
from app.common.response import success, fail
from . import dashboard_bp
from .services import (
    get_widget_layout, save_widget_layout,
    get_weather_city, save_weather_city,
    list_todos, create_todo, update_todo, delete_todo,
    get_active_widgets, save_active_widgets,
    list_countdowns, create_countdown, delete_countdown,
)


# ── 微件布局 ──

@dashboard_bp.route('/widgets', methods=['GET'])
@login_required
def get_widgets():
    layout = get_widget_layout()
    return success(layout)


@dashboard_bp.route('/widgets', methods=['PUT'])
@login_required
def put_widgets():
    data = request.get_json(silent=True)
    if not isinstance(data, list):
        return fail("布局数据必须是数组")
    save_widget_layout(data)
    return success(data, "布局已保存")


# ── 城市设置 ──

@dashboard_bp.route('/weather-city', methods=['GET'])
@login_required
def get_city():
    return success({"city": get_weather_city()})


@dashboard_bp.route('/weather-city', methods=['PUT'])
@login_required
def put_city():
    data = request.get_json(silent=True) or {}
    city = data.get('city', '').strip()
    if not city:
        return fail("城市名不能为空")
    save_weather_city(city)
    return success({"city": city}, "城市已更新")


# ── 待办事项 CRUD ──

@dashboard_bp.route('/todos', methods=['GET'])
@login_required
def get_todos():
    return success(list_todos())


@dashboard_bp.route('/todos', methods=['POST'])
@login_required
def add_todo():
    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()
    if not title:
        return fail("待办事项标题不能为空")
    todo = create_todo(title)
    return success(todo, "创建成功")


@dashboard_bp.route('/todos/<todo_id>', methods=['PUT'])
@login_required
def edit_todo(todo_id):
    data = request.get_json(silent=True) or {}
    todo = update_todo(todo_id, data)
    if not todo:
        return fail("待办事项不存在", 404)
    return success(todo, "更新成功")


@dashboard_bp.route('/todos/<todo_id>', methods=['DELETE'])
@login_required
def remove_todo(todo_id):
    if not delete_todo(todo_id):
        return fail("待办事项不存在", 404)
    return success(None, "删除成功")


# ── 活跃微件列表 ──

@dashboard_bp.route('/active-widgets', methods=['GET'])
@login_required
def get_active():
    return success(get_active_widgets())


@dashboard_bp.route('/active-widgets', methods=['PUT'])
@login_required
def put_active():
    data = request.get_json(silent=True)
    if not isinstance(data, list):
        return fail("数据必须是数组")
    save_active_widgets(data)
    return success(data, "已保存")


# ── 倒计时 CRUD ──

@dashboard_bp.route('/countdowns', methods=['GET'])
@login_required
def get_countdowns():
    return success(list_countdowns())


@dashboard_bp.route('/countdowns', methods=['POST'])
@login_required
def add_countdown():
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    target_date = data.get('target_date', '').strip()
    if not name:
        return fail("事件名称不能为空")
    if not target_date:
        return fail("目标日期不能为空")
    countdown = create_countdown(name, target_date)
    return success(countdown, "创建成功")


@dashboard_bp.route('/countdowns/<countdown_id>', methods=['DELETE'])
@login_required
def remove_countdown(countdown_id):
    if not delete_countdown(countdown_id):
        return fail("倒计时不存在", 404)
    return success(None, "删除成功")
