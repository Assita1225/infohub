from datetime import datetime, timezone, timedelta
from collections import Counter

from app.extensions import mongo


def get_overview_stats():
    """聚合所有模块的核心数据，返回全景仪表盘所需数据"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    # ── 总览数字 ──
    total_articles = mongo.db.articles.count_documents({})
    total_notes = mongo.db.notes.count_documents({})
    total_feeds = mongo.db.rss_feeds.count_documents({"is_active": True})
    total_read = mongo.db.articles.count_documents({"is_read": True})
    read_rate = round(total_read / max(total_articles, 1), 2)

    # ── 今日数据 ──
    today_new_articles = mongo.db.articles.count_documents({
        "published_at": {"$gte": today_start},
    })
    today_read = mongo.db.articles.count_documents({
        "is_read": True,
        "published_at": {"$gte": today_start},
    })
    today_notes = mongo.db.notes.count_documents({
        "created_at": {"$gte": today_start},
    })

    # ── 近7天每日阅读量 ──
    daily_reads = _daily_count(
        "articles",
        {"is_read": True},
        "published_at",
        7,
    )

    # ── 近7天每日新增文章量 ──
    daily_articles = _daily_count(
        "articles",
        {},
        "published_at",
        7,
    )

    # ── 订阅源分布（按分组） ──
    feeds_by_group_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$group", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    feeds_by_group = [
        {"group": r["_id"] or "未分组", "count": r["count"]}
        for r in mongo.db.rss_feeds.aggregate(feeds_by_group_pipeline)
    ]

    # ── 文章来源占比 ──
    source_pipeline = [
        {"$group": {"_id": "$source_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    source_labels = {"rss": "RSS", "news": "新闻", "web_monitor": "网页监控"}
    articles_by_source = [
        {"source": source_labels.get(r["_id"], r["_id"] or "其他"), "count": r["count"]}
        for r in mongo.db.articles.aggregate(source_pipeline)
    ]

    # ── 热门标签 Top10 ──
    tag_pipeline = [
        {"$match": {"tags": {"$exists": True, "$ne": []}}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    top_tags = [
        {"tag": r["_id"], "count": r["count"]}
        for r in mongo.db.articles.aggregate(tag_pipeline)
    ]

    # ── 订阅源健康状况 ──
    feeds_all = list(mongo.db.rss_feeds.find(
        {"is_active": True},
        {"title": 1, "error_count": 1, "last_error": 1, "last_fetched_at": 1},
    ))
    healthy = 0
    warning = 0
    error = 0
    error_feeds = []
    for f in feeds_all:
        ec = f.get("error_count", 0)
        if ec >= 5:
            error += 1
            error_feeds.append({
                "name": f.get("title", ""),
                "last_error": f.get("last_error", ""),
            })
        elif ec > 0:
            warning += 1
        else:
            healthy += 1

    feeds_health = {
        "healthy": healthy,
        "warning": warning,
        "error": error,
        "error_feeds": error_feeds,
    }

    # ── 最近活跃的5个订阅源 ──
    active_feeds_cursor = mongo.db.rss_feeds.find(
        {"is_active": True, "last_fetched_at": {"$ne": None}},
        {"title": 1, "last_fetched_at": 1},
    ).sort("last_fetched_at", -1).limit(5)

    active_feeds = []
    for f in active_feeds_cursor:
        article_count = mongo.db.articles.count_documents({"feed_id": f["_id"]})
        active_feeds.append({
            "name": f.get("title", ""),
            "last_fetched": f.get("last_fetched_at"),
            "article_count": article_count,
        })

    return {
        "total_articles": total_articles,
        "total_notes": total_notes,
        "total_feeds": total_feeds,
        "total_read": total_read,
        "read_rate": read_rate,
        "today_new_articles": today_new_articles,
        "today_read": today_read,
        "today_notes": today_notes,
        "daily_reads": daily_reads,
        "daily_articles": daily_articles,
        "feeds_by_group": feeds_by_group,
        "articles_by_source": articles_by_source,
        "top_tags": top_tags,
        "feeds_health": feeds_health,
        "active_feeds": active_feeds,
    }


def _daily_count(collection_name, base_match, date_field, days):
    """统计近 N 天每日文档数"""
    now = datetime.now(timezone.utc)
    result = []
    for i in range(days - 1, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        day_end = (day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()
        query = {**base_match, date_field: {"$gte": day_start, "$lt": day_end}}
        count = mongo.db[collection_name].count_documents(query)
        result.append({
            "date": day.strftime("%m-%d"),
            "count": count,
        })
    return result
