"""百度热搜适配器"""
import logging
import re

import requests
from bs4 import BeautifulSoup

from .base import TrendingAdapter

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class BaiduTrendingAdapter(TrendingAdapter):
    source_name = "baidu"

    def fetch(self) -> list[dict]:
        resp = requests.get(
            "https://top.baidu.com/board?tab=realtime",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        items = []

        # 百度热搜的热点条目
        rows = soup.select("div.category-wrap_iQLoo")
        for rank, row in enumerate(rows, start=1):
            # 标题
            title_tag = row.select_one("div.c-single-text-ellipsis")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            # 链接
            a_tag = row.select_one("a")
            url = a_tag.get("href", "") if a_tag else ""
            if not url:
                continue

            # 热度值
            hot_score = 0
            hot_tag = row.select_one("div.hot-index_1Bl1a")
            if hot_tag:
                hot_text = hot_tag.get_text(strip=True).replace(",", "")
                nums = re.findall(r"\d+", hot_text)
                if nums:
                    hot_score = int(nums[0])

            items.append({
                "title": title,
                "url": url,
                "hot_score": hot_score,
                "rank": rank,
            })

        return items[:30]
