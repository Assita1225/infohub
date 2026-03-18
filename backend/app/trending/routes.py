"""Trending 模块 API 路由"""
from flask import request

from app.common.auth import login_required
from app.common.response import success, fail
from . import trending_bp
from .services import get_sources, get_trending_list, get_wordcloud_data, refresh_all_sources


@trending_bp.route('/sources', methods=['GET'])
@login_required
def sources():
    """获取支持的热榜来源列表"""
    return success(get_sources())


@trending_bp.route('/list', methods=['GET'])
@login_required
def trending_list():
    """获取热榜数据（可指定来源：?source=github,baidu）"""
    source_param = request.args.get('source', '')
    sources = [s.strip() for s in source_param.split(',') if s.strip()] if source_param else None
    data = get_trending_list(sources)
    return success(data)


@trending_bp.route('/wordcloud', methods=['GET'])
@login_required
def wordcloud():
    """词云数据（聚合所有来源的 tags 词频）"""
    data = get_wordcloud_data()
    return success(data)


@trending_bp.route('/refresh', methods=['POST'])
@login_required
def refresh():
    """手动刷新所有热榜数据"""
    results = refresh_all_sources()
    total = sum(r["count"] for r in results)
    return success(results, f"刷新完成，共获取 {total} 条热榜数据")
