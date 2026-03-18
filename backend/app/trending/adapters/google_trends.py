"""Google Trends 适配器 —— 通过 Google Trends RSS 获取热搜"""
import logging

import feedparser

from .base import TrendingAdapter

logger = logging.getLogger(__name__)

# 中国 + 美国地区的热搜 RSS
FEED_URLS = [
    "https://trends.google.com/trending/rss?geo=CN",
    "https://trends.google.com/trending/rss?geo=US",
]


class GoogleTrendsAdapter(TrendingAdapter):
    source_name = "google_trends"

    def fetch(self) -> list[dict]:
        items = []
        seen = set()

        for feed_url in FEED_URLS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    title = entry.get("title", "").strip()
                    if not title or title in seen:
                        continue
                    seen.add(title)

                    url = entry.get("link", "")
                    if not url:
                        url = f"https://trends.google.com/trends/explore?q={title}"

                    # Google Trends RSS 有时在 ht:approx_traffic 提供流量数据
                    hot_score = 0
                    traffic = entry.get("ht_approx_traffic", "") or entry.get("approx_traffic", "")
                    if traffic:
                        traffic = traffic.replace(",", "").replace("+", "").strip()
                        try:
                            hot_score = int(traffic)
                        except ValueError:
                            pass

                    rank = len(items) + 1
                    if hot_score == 0:
                        hot_score = max(0, 100 - (rank - 1) * 3)

                    items.append({
                        "title": title,
                        "url": url,
                        "hot_score": hot_score,
                        "rank": rank,
                    })
            except Exception as e:
                logger.warning(f"Google Trends RSS {feed_url} 解析失败: {e}")
                continue

        # 重新编排排名
        items.sort(key=lambda x: x["hot_score"], reverse=True)
        for i, item in enumerate(items):
            item["rank"] = i + 1

        return items[:30]
