"""热榜适配器注册表"""
from .github import GitHubTrendingAdapter
from .baidu import BaiduTrendingAdapter
from .weibo import WeiboTrendingAdapter
from .google_trends import GoogleTrendsAdapter

# source_name → adapter 实例
_REGISTRY: dict[str, object] = {
    "github": GitHubTrendingAdapter(),
    "baidu": BaiduTrendingAdapter(),
    "weibo": WeiboTrendingAdapter(),
    "google_trends": GoogleTrendsAdapter(),
}

# 来源元信息（前端展示用）
TRENDING_SOURCES = [
    {"key": "github", "name": "GitHub Trending", "icon": "github"},
    {"key": "baidu", "name": "百度热搜", "icon": "search"},
    {"key": "weibo", "name": "微博热搜", "icon": "chat-dot-round"},
    {"key": "google_trends", "name": "Google Trends", "icon": "trend-charts"},
]


def get_adapter(source: str):
    """获取指定来源的适配器实例"""
    adapter = _REGISTRY.get(source)
    if not adapter:
        raise ValueError(f"未知的热榜来源: {source}")
    return adapter


def get_all_sources() -> list[str]:
    """返回所有已注册的来源 key 列表"""
    return list(_REGISTRY.keys())
