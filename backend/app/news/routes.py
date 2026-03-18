"""News 模块 API 路由"""
from flask import request

from app.common.auth import login_required
from app.common.response import success, fail, paginated
from . import news_bp
from .services import (
    get_categories, list_articles, get_article,
    summarize_article, set_read_later, list_read_later,
    article_to_note,
)
from .tasks import fetch_all_news_sources, fetch_news_source


# ── 分类 ──

@news_bp.route('/categories', methods=['GET'])
@login_required
def categories():
    """获取分类列表（含文章数）"""
    return success(get_categories())


# ── 文章列表 ──

@news_bp.route('/articles', methods=['GET'])
@login_required
def articles():
    """按分类获取新闻文章"""
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    items, total = list_articles(category, page, page_size)
    return paginated(items, total, page, page_size)


@news_bp.route('/articles/read-later', methods=['GET'])
@login_required
def read_later_list():
    """稍后读列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    items, total = list_read_later(page, page_size)
    return paginated(items, total, page, page_size)


# ── 文章详情 ──

@news_bp.route('/articles/<article_id>', methods=['GET'])
@login_required
def article_detail(article_id):
    """获取新闻详情"""
    article = get_article(article_id)
    if not article:
        return fail("文章不存在", 404)
    return success(article)


# ── AI 摘要 ──

@news_bp.route('/articles/<article_id>/summarize', methods=['POST'])
@login_required
def do_summarize(article_id):
    """按需生成 AI 摘要"""
    summary, status, error = summarize_article(article_id)
    if error and status is None:
        return fail(error, 404)
    if status == "failed":
        return fail(error or "摘要生成失败")
    return success({"summary": summary, "summary_status": status}, "摘要生成成功")


# ── 稍后读 ──

@news_bp.route('/articles/<article_id>/read-later', methods=['POST'])
@login_required
def add_read_later(article_id):
    """添加到稍后读"""
    if not set_read_later(article_id, True):
        return fail("文章不存在", 404)
    return success(None, "已添加到稍后读")


@news_bp.route('/articles/<article_id>/read-later', methods=['DELETE'])
@login_required
def remove_read_later(article_id):
    """移出稍后读"""
    if not set_read_later(article_id, False):
        return fail("文章不存在", 404)
    return success(None, "已移出稍后读")


# ── 转笔记 ──

@news_bp.route('/articles/<article_id>/to-note', methods=['POST'])
@login_required
def to_note(article_id):
    """转为笔记初始内容"""
    note, error = article_to_note(article_id)
    if error:
        return fail(error, 404)
    return success(note, "已转为笔记")


# ── 手动刷新 ──

@news_bp.route('/refresh', methods=['POST'])
@login_required
def do_refresh_all():
    """手动刷新所有新闻源"""
    results = fetch_all_news_sources()
    total_new = sum(r["new_count"] for r in results)
    return success(results, f"刷新完成，共新增 {total_new} 篇文章")
