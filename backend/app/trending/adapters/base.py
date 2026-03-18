"""热榜适配器抽象基类"""
from abc import ABC, abstractmethod


class TrendingAdapter(ABC):
    """所有热榜来源适配器的基类"""

    # 子类必须设置来源标识
    source_name: str = ""

    @abstractmethod
    def fetch(self) -> list[dict]:
        """
        抓取热榜条目列表。

        Returns:
            标准化条目列表，每条包含:
            - title: str       标题
            - url: str         链接
            - hot_score: float 热度值（标准化到 0-100）
            - rank: int        排名（从 1 开始）
        """
        pass
