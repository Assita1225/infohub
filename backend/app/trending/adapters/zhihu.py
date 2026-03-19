"""知乎热榜适配器"""
import logging
import re

import requests
from bs4 import BeautifulSoup

from app.common.http_client import http_get
from .base import TrendingAdapter

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cookie": "_zap=placeholder",  # 知乎需要基本 cookie 才不会 403
}


class ZhihuTrendingAdapter(TrendingAdapter):
    source_name = "zhihu"

    def fetch(self) -> list[dict]:
        resp = http_get(
            "https://www.zhihu.com/hot",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        items = []

        rows = soup.select("div.HotItem")
        for row in rows:
            # 排名
            rank_tag = row.select_one("div.HotItem-index div")
            rank = 0
            if rank_tag:
                rank_text = rank_tag.get_text(strip=True)
                nums = re.findall(r"\d+", rank_text)
                rank = int(nums[0]) if nums else 0

            # 标题
            title_tag = row.select_one("h2.HotItem-title")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            # 链接
            a_tag = row.select_one("a")
            url = a_tag.get("href", "") if a_tag else ""
            if not url:
                continue
            if not url.startswith("http"):
                url = "https://www.zhihu.com" + url

            # 热度
            hot_score = 0
            metrics_tag = row.select_one("div.HotItem-metrics")
            if metrics_tag:
                metrics_text = metrics_tag.get_text(strip=True)
                # "1234 万热度" 或 "1234 热度"
                nums = re.findall(r"([\d.]+)\s*万", metrics_text)
                if nums:
                    hot_score = int(float(nums[0]) * 10000)
                else:
                    nums = re.findall(r"(\d+)", metrics_text)
                    if nums:
                        hot_score = int(nums[0])

            if rank == 0:
                rank = len(items) + 1

            items.append({
                "title": title,
                "url": url,
                "hot_score": hot_score,
                "rank": rank,
            })

        return items[:50]
