"""RSS 抓取任务（同步执行版，后续可迁移到 Celery）"""
import logging
from datetime import datetime, timezone
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup
from bson import ObjectId
from goose3 import Goose
from simhash import Simhash

from app.common.http_client import http_get, get_goose_config
from app.extensions import mongo

logger = logging.getLogger(__name__)

# Goose 实例复用（自动携带代理配置）
_goose = Goose(get_goose_config())

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


def _refresh_web_monitor(feed):
    """
    网页监控模式：requests + BeautifulSoup 抓取页面链接作为文章列表
    返回 (new_count, error_message)
    """
    feed_id = str(feed["_id"])
    feed_url = feed["url"]
    display_count = feed.get("display_count", 5)
    css_selector = feed.get("css_selector", "").strip()

    try:
        resp = http_get(feed_url, headers=REQUEST_HEADERS, timeout=30)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        error_msg = f"网页抓取失败: {e}"
        mongo.db.rss_feeds.update_one(
            {"_id": ObjectId(feed_id)},
            {"$inc": {"error_count": 1}, "$set": {"last_error": error_msg}},
        )
        return 0, error_msg

    # 用 CSS 选择器定位区域，或回退到整个页面
    if css_selector:
        container = soup.select_one(css_selector)
        if not container:
            container = soup
    else:
        container = soup

    # 提取所有 <a> 标签
    links = container.find_all("a", href=True)

    # 过滤：标题长度 > 10 字符的链接视为文章
    articles = []
    for a in links:
        text = a.get_text(strip=True)
        href = a["href"]
        if len(text) > 10:
            full_url = urljoin(feed_url, href)
            articles.append({"title": text, "url": full_url})

    # 去重（同一页面可能有重复链接）
    seen_urls = set()
    unique_articles = []
    for item in articles:
        if item["url"] not in seen_urls:
            seen_urls.add(item["url"])
            unique_articles.append(item)

    new_count = 0
    for item in unique_articles[:display_count]:
        article_url = item["url"]

        # URL 去重
        if mongo.db.articles.find_one({"url": article_url}):
            continue

        # 提取正文
        content = _extract_content(article_url)

        # SimHash 去重
        simhash_val = _compute_simhash(item["title"] + " " + content)

        # 提取关键词标签
        tag_text = item["title"] + " " + content[:2000]
        tags = _extract_tags(tag_text)

        doc = {
            "feed_id": ObjectId(feed_id),
            "source_type": "rss",
            "title": item["title"],
            "url": article_url,
            "author": "",
            "content": content,
            "summary": None,
            "summary_status": "none",
            "tags": tags,
            "simhash": simhash_val,
            "is_read": False,
            "is_favorited": False,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            mongo.db.articles.insert_one(doc)
            new_count += 1
        except Exception as e:
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


def refresh_feed(feed_id):
    """
    刷新单个订阅源：根据 feed_type 分发到不同的刷新逻辑
    返回 (new_count, error_message)
    """
    feed = mongo.db.rss_feeds.find_one({"_id": ObjectId(feed_id)})
    if not feed:
        return 0, "订阅源不存在"

    # 网页监控模式
    if feed.get("feed_type") == "web_monitor":
        return _refresh_web_monitor(feed)

    feed_url = feed["url"]
    display_count = feed.get("display_count", 5)

    # 1. 先用 requests 获取内容（处理 UA / 压缩等问题），再交给 feedparser 解析
    try:
        resp = http_get(feed_url, headers=REQUEST_HEADERS, timeout=30)
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
