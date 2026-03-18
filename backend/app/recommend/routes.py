"""Recommend 模块 API 路由"""
from flask import request

from app.common.auth import login_required
from app.common.response import success, fail
from . import recommend_bp
from .services import get_tags, update_selected_tags, add_custom_tag, delete_custom_tag, get_feed


@recommend_bp.route('/tags', methods=['GET'])
@login_required
def tags_get():
    """获取预设标签 + 用户已选标签 + 自定义标签"""
    return success(get_tags())


@recommend_bp.route('/tags', methods=['PUT'])
@login_required
def tags_update():
    """更新用户选中的标签"""
    data = request.get_json(silent=True) or {}
    selected = data.get("selected_tags")
    if selected is None:
        return fail("缺少 selected_tags 字段", 400)
    if not isinstance(selected, list):
        return fail("selected_tags 必须是数组", 400)
    update_selected_tags(selected)
    return success(None, "标签已更新")


@recommend_bp.route('/tags/custom', methods=['POST'])
@login_required
def tag_add_custom():
    """添加自定义标签"""
    data = request.get_json(silent=True) or {}
    tag = data.get("tag", "").strip()
    if not tag:
        return fail("标签不能为空", 400)
    ok, error = add_custom_tag(tag)
    if not ok:
        return fail(error, 400)
    return success(None, "自定义标签已添加")


@recommend_bp.route('/tags/<tag>', methods=['DELETE'])
@login_required
def tag_delete(tag):
    """删除自定义标签"""
    delete_custom_tag(tag)
    return success(None, "标签已删除")


@recommend_bp.route('/feed', methods=['GET'])
@login_required
def feed():
    """获取推荐内容（?tags=人工智能,前端）"""
    tags_param = request.args.get('tags', '')
    tags = [t.strip() for t in tags_param.split(',') if t.strip()]
    limit = request.args.get('limit', 20, type=int)
    data = get_feed(tags, limit)
    return success(data)
