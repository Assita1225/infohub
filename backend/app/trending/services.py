"""Trending 模块业务逻辑"""
import json
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.extensions import mongo, redis_ext
from .adapters import TRENDING_SOURCES

logger = logging.getLogger(__name__)

CACHE_PREFIX = "trending:"
CACHE_TTL = 900  # 15 分钟


def get_sources():
    """获取支持的热榜来源列表"""
    return TRENDING_SOURCES


def get_trending_list(sources: list[str] | None = None):
    """
    获取热榜数据。优先从 Redis 缓存读取，miss 则查 MongoDB。
    """
    from .adapters import get_all_sources

    if not sources:
        sources = get_all_sources()

    result = {}
    for source in sources:
        cache_key = f"{CACHE_PREFIX}list:{source}"

        # 尝试 Redis 缓存
        cached = None
        try:
            cached = redis_ext.client.get(cache_key)
        except Exception:
            pass

        if cached:
            result[source] = json.loads(cached)
            continue

        # 从 MongoDB 查询最新一批数据
        items = list(
            mongo.db.trending_items.find(
                {"source": source},
                {"_id": 0, "title": 1, "url": 1, "hot_score": 1, "rank": 1,
                 "tags": 1, "fetched_at": 1},
            )
            .sort("rank", 1)
            .limit(50)
        )

        result[source] = items

        # 写入缓存
        if items:
            try:
                redis_ext.client.setex(cache_key, CACHE_TTL, json.dumps(items, default=str))
            except Exception:
                pass

    return result


def get_wordcloud_data():
    """聚合所有来源的 tags 词频，生成词云数据"""
    cache_key = f"{CACHE_PREFIX}wordcloud"

    cached = None
    try:
        cached = redis_ext.client.get(cache_key)
    except Exception:
        pass
    if cached:
        return json.loads(cached)

    # 从 MongoDB 聚合最近 24h 的 tags
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    pipeline = [
        {"$match": {"fetched_at": {"$gte": since}}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 100},
    ]
    agg_result = list(mongo.db.trending_items.aggregate(pipeline))
    wordcloud = [{"name": item["_id"], "value": item["count"]} for item in agg_result]

    if wordcloud:
        try:
            redis_ext.client.setex(cache_key, CACHE_TTL, json.dumps(wordcloud))
        except Exception:
            pass

    return wordcloud


def refresh_source(source: str):
    """刷新单个来源的热榜数据"""
    from .adapters import get_adapter

    adapter = get_adapter(source)
    raw_items = adapter.fetch()

    if not raw_items:
        return 0

    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=24)

    # 提取关键词
    import jieba.analyse

    docs = []
    for item in raw_items:
        tags = []
        try:
            tags = jieba.analyse.extract_tags(item["title"], topK=5)
        except Exception:
            pass

        docs.append({
            "source": source,
            "title": item["title"],
            "url": item["url"],
            "hot_score": item.get("hot_score", 0),
            "rank": item.get("rank", 0),
            "tags": tags,
            "fetched_at": now.isoformat(),
            "expires_at": expires,
        })

    # 删除该来源的旧数据，插入新数据
    mongo.db.trending_items.delete_many({"source": source})
    if docs:
        mongo.db.trending_items.insert_many(docs)

    # 清除该来源的缓存
    try:
        redis_ext.client.delete(f"{CACHE_PREFIX}list:{source}")
        redis_ext.client.delete(f"{CACHE_PREFIX}wordcloud")
    except Exception:
        pass

    return len(docs)


def refresh_all_sources():
    """刷新所有来源，某个源失败不影响其他源"""
    from .adapters import get_all_sources

    results = []
    for source in get_all_sources():
        try:
            count = refresh_source(source)
            results.append({"source": source, "count": count, "error": None})
        except Exception as e:
            logger.error(f"刷新热榜来源 {source} 失败: {e}")
            results.append({"source": source, "count": 0, "error": str(e)})
    return results
