"""RSS 抓取任务（同步执行版，后续可迁移到 Celery）"""
import logging
from datetime import datetime, timezone

import feedparser
import requests
from bson import ObjectId
from goose3 import Goose
from simhash import Simhash

from app.extensions import mongo

logger = logging.getLogger(__name__)

# Goose 实例复用
_goose = Goose({"browser_user_agent": "InfoHub/1.0 RSS Reader"})

# 自定义 UA 防止 429
REQUEST_HEADERS = {
    "User-Agent": "InfoHub/1.0 RSS Reader (personal project; +https://github.com/infohub)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def _extract_tags(text, top_n=5):
    """用 jieba + TF-IDF 提取关键词标签"""
    if not text or len(text.strip()) < 10:
        return []
    try:
        import jieba.analyse
        tags = jieba.analyse.extract_tags(text, topK=top_n)
        return tags
    except Exception:
        return []


def _compute_simhash(text):
    """计算文本的 SimHash 指纹"""
    if not text:
        return ""
    try:
        return str(Simhash(text).value)
    except Exception:
        return ""


def _extract_content(url):
    """用 Goose3 提取正文"""
    try:
        article = _goose.extract(url=url)
        return article.cleaned_text or ""
    except Exception as e:
        logger.debug(f"Goose extract failed for {url}: {e}")
        return ""


def _parse_published(entry):
    """从 feedparser entry 中解析发布时间"""
    for attr in ("published_parsed", "updated_parsed"):
        tp = getattr(entry, attr, None)
        if tp:
            try:
                from time import mktime
                return datetime.fromtimestamp(mktime(tp), tz=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def refresh_feed(feed_id):
    """
    刷新单个订阅源：feedparser 解析 → goose3 正文提取 → simhash 去重 → 存入 articles
    返回 (new_count, error_message)
    """
    feed = mongo.db.rss_feeds.find_one({"_id": ObjectId(feed_id)})
    if not feed:
        return 0, "订阅源不存在"

    feed_url = feed["url"]
    display_count = feed.get("display_count", 5)

    # 1. 先用 requests 获取内容（处理 UA / 压缩等问题），再交给 feedparser 解析
    try:
        resp = requests.get(feed_url, headers=REQUEST_HEADERS, timeout=30)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
        if parsed.bozo and not parsed.entries:
            raise Exception(str(parsed.bozo_exception))
    except Exception as e:
        error_msg = f"解析失败: {e}"
        mongo.db.rss_feeds.update_one(
            {"_id": ObjectId(feed_id)},
            {"$inc": {"error_count": 1}, "$set": {"last_error": error_msg}},
        )
        return 0, error_msg

    # 更新源站 URL
    site_url = getattr(parsed.feed, "link", "") or ""
    if site_url and not feed.get("site_url"):
        mongo.db.rss_feeds.update_one(
            {"_id": ObjectId(feed_id)},
            {"$set": {"site_url": site_url}},
        )

    entries = parsed.entries[:display_count]
    new_count = 0

    for entry in entries:
        article_url = getattr(entry, "link", "") or ""
        if not article_url:
            continue

        # 2. 去重：URL 唯一
        if mongo.db.articles.find_one({"url": article_url}):
            continue

        # 3. 提取正文（Goose3 → fallback 到 RSS entry 自带 summary/content）
        content = _extract_content(article_url)
        if not content:
            # fallback: feedparser entry 中的 summary 或 content
            content = entry.get("summary", "")
            if hasattr(entry, "content") and entry.content:
                content = entry.content[0].get("value", content)

        # 4. SimHash 去重
        simhash_val = _compute_simhash(entry.get("title", "") + " " + content)

        # 5. 提取关键词标签
        tag_text = entry.get("title", "") + " " + content[:2000]
        tags = _extract_tags(tag_text)

        # 6. 构建文章文档
        doc = {
            "feed_id": ObjectId(feed_id),
            "source_type": "rss",
            "title": entry.get("title", "无标题"),
            "url": article_url,
            "author": entry.get("author", ""),
            "content": content,
            "summary": None,
            "summary_status": "none",
            "tags": tags,
            "simhash": simhash_val,
            "is_read": False,
            "is_favorited": False,
            "published_at": _parse_published(entry),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            mongo.db.articles.insert_one(doc)
            new_count += 1
        except Exception as e:
            # 可能是 URL 唯一索引冲突
            logger.debug(f"Insert article failed: {e}")
            continue

    # 更新源的刷新时间和错误状态
    mongo.db.rss_feeds.update_one(
        {"_id": ObjectId(feed_id)},
        {
            "$set": {
                "last_fetched_at": datetime.now(timezone.utc).isoformat(),
                "error_count": 0,
                "last_error": None,
            }
        },
    )

    return new_count, None


def refresh_all_feeds():
    """刷新所有活跃的订阅源"""
    feeds = mongo.db.rss_feeds.find({"is_active": True})
    results = []
    for feed in feeds:
        fid = str(feed["_id"])
        new_count, error = refresh_feed(fid)
        results.append({
            "feed_id": fid,
            "title": feed.get("title", ""),
            "new_count": new_count,
            "error": error,
        })
    return results
