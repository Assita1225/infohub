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
    """获取推荐内容（?tags=人工智能:0.8,前端开发:0.6）
    支持带权重的标签格式 tag:weight，不带权重则默认 0.5
    """
    tags_param = request.args.get('tags', '')
    limit = request.args.get('limit', 20, type=int)

    tags_with_weights = []
    for part in tags_param.split(','):
        part = part.strip()
        if not part:
            continue
        if ':' in part:
            name, w = part.rsplit(':', 1)
            try:
                weight = float(w)
            except ValueError:
                weight = 0.5
            tags_with_weights.append({"name": name.strip(), "weight": weight})
        else:
            tags_with_weights.append({"name": part, "weight": 0.5})

    data = get_feed(tags_with_weights, limit)
    return success(data)
