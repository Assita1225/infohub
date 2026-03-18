"""GitHub Trending 适配器"""
import logging

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


class GitHubTrendingAdapter(TrendingAdapter):
    source_name = "github"

    def fetch(self) -> list[dict]:
        resp = requests.get(
            "https://github.com/trending",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        items = []

        rows = soup.select("article.Box-row")
        for rank, row in enumerate(rows, start=1):
            # 仓库名称
            h2 = row.select_one("h2 a")
            if not h2:
                continue
            repo_path = h2.get("href", "").strip("/")
            title = repo_path  # e.g. "owner/repo"
            url = f"https://github.com/{repo_path}"

            # 描述
            desc_tag = row.select_one("p")
            desc = desc_tag.get_text(strip=True) if desc_tag else ""

            # Stars today
            hot_score = 0
            star_tag = row.select_one("span.d-inline-block.float-sm-right")
            if star_tag:
                star_text = star_tag.get_text(strip=True).replace(",", "").split()[0]
                try:
                    hot_score = int(star_text)
                except ValueError:
                    pass

            # 标准化热度到 0-100（基于排名）
            normalized_score = max(0, 100 - (rank - 1) * 4)
            if hot_score > 0:
                normalized_score = hot_score  # 保留原始 star 数作为热度

            if desc:
                title = f"{repo_path} — {desc}"

            items.append({
                "title": title,
                "url": url,
                "hot_score": normalized_score,
                "rank": rank,
            })

        return items[:25]
