from flask import request

from app.common.auth import login_required
from app.common.response import success, fail, paginated
from . import rss_bp
from .services import (
    list_feeds, get_feed, create_feed, update_feed, delete_feed,
    get_feed_groups, create_group_record, rename_group, delete_group,
    list_articles, get_article, mark_read,
    toggle_favorite, summarize_article, get_rss_stats,
    article_to_note, get_reading_timeline, get_feeds_health,
)
from .tasks import refresh_feed, refresh_all_feeds


# ── 订阅源 ──

@rss_bp.route('/feeds', methods=['GET'])
@login_required
def get_feeds():
    group = request.args.get('group')
    feeds = list_feeds(group)
    return success(feeds)


@rss_bp.route('/feeds', methods=['POST'])
@login_required
def add_feed():
    data = request.get_json(silent=True) or {}
    if not data.get('url'):
        return fail("订阅源 URL 不能为空", errors={"url": "必填"})
    if not data.get('title'):
        return fail("订阅源名称不能为空", errors={"title": "必填"})
    feed = create_feed(data)
    return success(feed, "添加成功")


@rss_bp.route('/feeds/<feed_id>', methods=['PUT'])
@login_required
def edit_feed(feed_id):
    data = request.get_json(silent=True) or {}
    feed = update_feed(feed_id, data)
    if not feed:
        return fail("订阅源不存在", 404)
    return success(feed, "更新成功")


@rss_bp.route('/feeds/<feed_id>', methods=['DELETE'])
@login_required
def remove_feed(feed_id):
    if not delete_feed(feed_id):
        return fail("订阅源不存在", 404)
    return success(None, "删除成功")


@rss_bp.route('/feeds/groups', methods=['GET'])
@login_required
def get_groups():
    return success(get_feed_groups())


@rss_bp.route('/feeds/groups', methods=['POST'])
@login_required
def create_group():
    """创建新分组，持久化到 rss_groups 集合"""
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    if not name:
        return fail("分组名不能为空")
    # 检查是否已存在
    existing = get_feed_groups()
    if any(g['name'] == name for g in existing):
        return fail("分组已存在")
    create_group_record(name)
    return success({"name": name, "count": 0}, "分组创建成功")


@rss_bp.route('/feeds/groups/<path:name>', methods=['PUT'])
@login_required
def update_group(name):
    """重命名分组"""
    data = request.get_json(silent=True) or {}
    new_name = data.get('name', '').strip()
    if not new_name:
        return fail("新分组名不能为空")
    if new_name == name:
        return fail("新旧名称相同")
    count = rename_group(name, new_name)
    return success({"name": new_name, "count": count}, "重命名成功")


@rss_bp.route('/feeds/groups/<path:name>', methods=['DELETE'])
@login_required
def remove_group(name):
    """删除分组，订阅源移到 '未分组'"""
    if name == '未分组':
        return fail("不能删除默认分组")
    count = delete_group(name)
    return success({"moved_count": count}, f"已删除分组，{count} 个订阅源移至未分组")


# ── 刷新 ──

@rss_bp.route('/feeds/<feed_id>/refresh', methods=['POST'])
@login_required
def do_refresh(feed_id):
    new_count, error = refresh_feed(feed_id)
    if error:
        return fail(error)
    return success({"new_count": new_count}, f"刷新完成，新增 {new_count} 篇文章")


@rss_bp.route('/feeds/refresh-all', methods=['POST'])
@login_required
def do_refresh_all():
    results = refresh_all_feeds()
    total_new = sum(r["new_count"] for r in results)
    return success(results, f"刷新完成，共新增 {total_new} 篇文章")


# ── 文章 ──

@rss_bp.route('/feeds/<feed_id>/articles', methods=['GET'])
@login_required
def get_feed_articles(feed_id):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    items, total = list_articles(feed_id, page, page_size)
    return paginated(items, total, page, page_size)


@rss_bp.route('/articles/<article_id>', methods=['GET'])
@login_required
def get_article_detail(article_id):
    article = get_article(article_id)
    if not article:
        return fail("文章不存在", 404)
    return success(article)


@rss_bp.route('/articles/<article_id>/summarize', methods=['POST'])
@login_required
def do_summarize(article_id):
    """按需生成 AI 摘要"""
    summary, status, error = summarize_article(article_id)
    if error and status is None:
        return fail(error, 404)
    if status == "failed":
        return fail(error or "摘要生成失败")
    return success({"summary": summary, "summary_status": status}, "摘要生成成功")


@rss_bp.route('/articles/<article_id>/read', methods=['POST'])
@login_required
def do_mark_read(article_id):
    mark_read(article_id)
    return success(None, "已标记为已读")


@rss_bp.route('/articles/<article_id>/favorite', methods=['POST'])
@login_required
def do_toggle_favorite(article_id):
    new_val = toggle_favorite(article_id)
    if new_val is None:
        return fail("文章不存在", 404)
    msg = "已收藏" if new_val else "已取消收藏"
    return success({"is_favorited": new_val}, msg)


@rss_bp.route('/articles/<article_id>/to-note', methods=['POST'])
@login_required
def to_note(article_id):
    """将 RSS 文章保存到笔记本"""
    note, error = article_to_note(article_id)
    if error:
        return fail(error, 404)
    return success(note, "已保存到笔记本")


# ── 时间线 & 图谱 & 健康 ──

@rss_bp.route('/timeline', methods=['GET'])
@login_required
def timeline():
    days = request.args.get('days', 7, type=int)
    return success(get_reading_timeline(days))


@rss_bp.route('/feeds/health', methods=['GET'])
@login_required
def feeds_health():
    return success(get_feeds_health())


# ── 统计 ──

@rss_bp.route('/stats', methods=['GET'])
@login_required
def stats():
    return success(get_rss_stats())
