"""NewsAPI.org 适配器（需要 API Key）"""
import logging
import os
from datetime import datetime, timezone

import requests

from .base import NewsAdapter

logger = logging.getLogger(__name__)


class NewsApiAdapter(NewsAdapter):
    """通过 NewsAPI.org 抓取新闻"""

    BASE_URL = "https://newsapi.org/v2/top-headlines"

    def fetch(self, source_config: dict) -> list[dict]:
        api_key_env = source_config.get("api_key_env", "NEWSAPI_KEY")
        api_key = os.getenv(api_key_env)
        if not api_key:
            logger.warning(f"NewsAPI adapter: env var {api_key_env} not set, skipping")
            return []

        params = {
            "apiKey": api_key,
            "language": source_config.get("language", "zh"),
            "country": source_config.get("country", "cn"),
            "pageSize": source_config.get("page_size", 20),
        }
        query = source_config.get("query")
        if query:
            params["q"] = query

        category = source_config.get("api_category")
        if category:
            params["category"] = category

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"NewsAPI fetch failed: {e}")
            raise

        if data.get("status") != "ok":
            logger.error(f"NewsAPI error: {data.get('message', 'unknown')}")
            return []

        articles = []
        for item in data.get("articles", []):
            url = item.get("url", "")
            if not url:
                continue
            articles.append({
                "title": item.get("title", "无标题"),
                "url": url,
                "author": item.get("author", "") or (item.get("source", {}) or {}).get("name", ""),
                "content": item.get("content", "") or item.get("description", ""),
                "published_at": item.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
            })

        return articles
