"""新闻抓取任务（同步执行版，后续可迁移到 Celery Beat）"""
import logging
from datetime import datetime, timezone

from bson import ObjectId
from simhash import Simhash

from app.extensions import mongo
from .adapters import get_adapter

logger = logging.getLogger(__name__)


def _compute_simhash(text):
    """计算文本的 SimHash 指纹"""
    if not text:
        return ""
    try:
        return str(Simhash(text).value)
    except Exception:
        return ""


def _extract_tags(text, top_n=5):
    """用 jieba + TF-IDF 提取关键词标签"""
    if not text or len(text.strip()) < 10:
        return []
    try:
        import jieba.analyse
        return jieba.analyse.extract_tags(text, topK=top_n)
    except Exception:
        return []


def fetch_news_source(source_id):
    """
    抓取单个新闻源。
    返回 (new_count, error_message)
    """
    source = mongo.db.news_sources.find_one({"_id": ObjectId(source_id)})
    if not source:
        return 0, "新闻源不存在"

    adapter_type = source.get("adapter_type", "")
    try:
        adapter = get_adapter(adapter_type)
    except ValueError as e:
        return 0, str(e)

    # 构建适配器配置：合并 source 级别和 fetch_config
    config = {
        "url": source.get("url", ""),
        **(source.get("fetch_config") or {}),
    }

    try:
        raw_articles = adapter.fetch(config)
    except Exception as e:
        error_msg = f"抓取失败: {e}"
        mongo.db.news_sources.update_one(
            {"_id": ObjectId(source_id)},
            {"$inc": {"error_count": 1}, "$set": {"last_error": error_msg}},
        )
        return 0, error_msg

    new_count = 0
    for item in raw_articles:
        article_url = item.get("url", "")
        if not article_url:
            continue

        # URL 去重
        if mongo.db.articles.find_one({"url": article_url}):
            continue

        title = item.get("title", "无标题")
        content = item.get("content", "")
        simhash_val = _compute_simhash(title + " " + content)
        tags = _extract_tags(title + " " + content[:2000])

        doc = {
            "news_source_id": ObjectId(source_id),
            "source_type": "news",
            "category": source.get("category", ""),
            "title": title,
            "url": article_url,
            "author": item.get("author", ""),
            "content": content,
            "summary": None,
            "summary_status": "none",
            "tags": tags,
            "simhash": simhash_val,
            "is_read": False,
            "is_read_later": False,
            "published_at": item.get("published_at", datetime.now(timezone.utc).isoformat()),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            mongo.db.articles.insert_one(doc)
            new_count += 1
        except Exception as e:
            logger.debug(f"Insert news article failed: {e}")
            continue

    # 更新源的刷新时间
    mongo.db.news_sources.update_one(
        {"_id": ObjectId(source_id)},
        {
            "$set": {
                "last_fetched_at": datetime.now(timezone.utc).isoformat(),
                "error_count": 0,
                "last_error": None,
            }
        },
    )

    return new_count, None


def fetch_all_news_sources():
    """抓取所有活跃新闻源"""
    sources = mongo.db.news_sources.find({"is_active": True})
    results = []
    for source in sources:
        sid = str(source["_id"])
        new_count, error = fetch_news_source(sid)
        results.append({
            "source_id": sid,
            "name": source.get("name", ""),
            "category": source.get("category", ""),
            "new_count": new_count,
            "error": error,
        })
    return results
