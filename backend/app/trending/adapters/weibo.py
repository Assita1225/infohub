"""微博热搜适配器 —— 通过微博公开 AJAX 接口获取"""
import logging

import requests

from app.common.http_client import http_get
from .base import TrendingAdapter

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://weibo.com/",
}


class WeiboTrendingAdapter(TrendingAdapter):
    source_name = "weibo"

    def fetch(self) -> list[dict]:
        resp = http_get(
            "https://weibo.com/ajax/side/hotSearch",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        realtime = data.get("data", {}).get("realtime", [])
        items = []

        for entry in realtime:
            word = entry.get("word", "").strip()
            if not word:
                continue

            rank = entry.get("rank", len(items) + 1)
            # rank 从 0 开始，转成从 1 开始
            if isinstance(rank, int):
                rank = rank + 1

            hot_score = entry.get("num", 0) or 0

            # 微博热搜链接
            url = f"https://s.weibo.com/weibo?q=%23{word}%23"

            items.append({
                "title": word,
                "url": url,
                "hot_score": hot_score,
                "rank": rank,
            })

        return items[:30]
