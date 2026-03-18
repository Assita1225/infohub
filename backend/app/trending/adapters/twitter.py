"""Twitter/X Trending 适配器 —— 通过 trends24.in 获取实时趋势"""
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
    "Accept-Language": "en-US,en;q=0.9",
}


class TwitterTrendingAdapter(TrendingAdapter):
    source_name = "twitter"

    def fetch(self) -> list[dict]:
        resp = requests.get(
            "https://trends24.in/",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        seen = set()

        # trends24.in 按时间段分 card，取第一个（最新）card 的趋势
        cards = soup.select("div.trend-card")
        for card in cards[:3]:
            links = card.select("li a")
            for a_tag in links:
                title = a_tag.get_text(strip=True)
                if not title or title in seen:
                    continue
                seen.add(title)

                href = a_tag.get("href", "")
                # 构造 Twitter 搜索链接
                if title.startswith("#"):
                    url = f"https://x.com/search?q={title}"
                else:
                    url = f"https://x.com/search?q={title}"

                # 提取推文数（如果有）
                hot_score = 0
                tweet_count = a_tag.find_next_sibling("span")
                if tweet_count:
                    nums = re.findall(r"[\d,.]+[KkMm]?", tweet_count.get_text())
                    if nums:
                        hot_score = _parse_count(nums[0])

                rank = len(items) + 1
                if hot_score == 0:
                    hot_score = max(0, 100 - (rank - 1) * 3)

                items.append({
                    "title": title,
                    "url": url,
                    "hot_score": hot_score,
                    "rank": rank,
                })

                if len(items) >= 30:
                    return items

        return items


def _parse_count(s: str) -> int:
    """解析 '12.3K', '1.2M', '45,678' 等格式"""
    s = s.replace(",", "").strip()
    multiplier = 1
    if s.endswith(("K", "k")):
        multiplier = 1000
        s = s[:-1]
    elif s.endswith(("M", "m")):
        multiplier = 1000000
        s = s[:-1]
    try:
        return int(float(s) * multiplier)
    except ValueError:
        return 0
