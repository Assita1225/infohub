"""Google News RSS 适配器"""
import logging
from datetime import datetime, timezone

import feedparser
import requests

from .base import NewsAdapter

logger = logging.getLogger(__name__)

REQUEST_HEADERS = {
    "User-Agent": "InfoHub/1.0 NewsReader (personal project)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


class GoogleRssAdapter(NewsAdapter):
    """通过 Google News RSS 抓取新闻"""

    def fetch(self, source_config: dict) -> list[dict]:
        url = source_config.get("url", "")
        if not url:
            logger.warning("Google RSS adapter: url is empty")
            return []

        page_size = source_config.get("page_size", 20)

        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
            if parsed.bozo and not parsed.entries:
                raise Exception(str(parsed.bozo_exception))
        except Exception as e:
            logger.error(f"Google RSS fetch failed: {e}")
            raise

        entries = parsed.entries[:page_size]
        articles = []

        for entry in entries:
            article_url = getattr(entry, "link", "") or ""
            if not article_url:
                continue

            title = entry.get("title", "无标题")
            author = entry.get("author", "") or entry.get("source", {}).get("title", "")
            content = entry.get("summary", "")
            if hasattr(entry, "content") and entry.content:
                content = entry.content[0].get("value", content)

            published_at = self._parse_published(entry)

            articles.append({
                "title": title,
                "url": article_url,
                "author": author,
                "content": content,
                "published_at": published_at,
            })

        return articles

    @staticmethod
    def _parse_published(entry):
        """解析 feedparser entry 的发布时间"""
        for attr in ("published_parsed", "updated_parsed"):
            tp = getattr(entry, attr, None)
            if tp:
                try:
                    from time import mktime
                    return datetime.fromtimestamp(mktime(tp), tz=timezone.utc).isoformat()
                except Exception:
                    pass
        return datetime.now(timezone.utc).isoformat()
