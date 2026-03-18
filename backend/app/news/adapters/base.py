"""新闻适配器抽象基类"""
from abc import ABC, abstractmethod


class NewsAdapter(ABC):
    """所有新闻源适配器的基类"""

    @abstractmethod
    def fetch(self, source_config: dict) -> list[dict]:
        """
        抓取新闻条目。

        Args:
            source_config: news_sources 文档中的 fetch_config 字段

        Returns:
            标准化新闻条目列表，每个条目包含:
            - title: str
            - url: str
            - author: str
            - content: str (正文或摘要)
            - published_at: str (ISO8601)
        """
        pass
