"""新闻源适配器注册表"""
from .google_rss import GoogleRssAdapter
from .newsapi import NewsApiAdapter

# adapter_type → 适配器类映射
ADAPTER_MAP = {
    "google_rss": GoogleRssAdapter,
    "newsapi": NewsApiAdapter,
}


def get_adapter(adapter_type):
    """根据 adapter_type 获取适配器实例"""
    cls = ADAPTER_MAP.get(adapter_type)
    if not cls:
        raise ValueError(f"未知适配器类型: {adapter_type}")
    return cls()
