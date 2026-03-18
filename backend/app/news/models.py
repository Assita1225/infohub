"""News 模块的 MongoDB 索引初始化 + 预设数据"""
from datetime import datetime, timezone

from app.extensions import mongo

# 预设新闻源（Google News RSS，免费无需 Key）
SEED_NEWS_SOURCES = [
    {
        "name": "Google News 科技",
        "url": "https://news.google.com/rss/search?q=科技+OR+AI+OR+互联网&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category": "tech",
        "category_name": "科技",
        "adapter_type": "google_rss",
        "is_active": True,
        "fetch_config": {
            "query": "科技 OR AI OR 互联网",
            "language": "zh",
            "country": "cn",
            "page_size": 20,
        },
    },
    {
        "name": "Google News 财经",
        "url": "https://news.google.com/rss/search?q=财经+OR+股市+OR+经济&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category": "finance",
        "category_name": "财经",
        "adapter_type": "google_rss",
        "is_active": True,
        "fetch_config": {
            "query": "财经 OR 股市 OR 经济",
            "language": "zh",
            "country": "cn",
            "page_size": 20,
        },
    },
    {
        "name": "Google News 国际",
        "url": "https://news.google.com/rss/search?q=国际+OR+世界&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category": "world",
        "category_name": "国际",
        "adapter_type": "google_rss",
        "is_active": True,
        "fetch_config": {
            "query": "国际 OR 世界",
            "language": "zh",
            "country": "cn",
            "page_size": 20,
        },
    },
    {
        "name": "Google News 社会",
        "url": "https://news.google.com/rss/search?q=社会+OR+民生&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
        "category": "society",
        "category_name": "社会",
        "adapter_type": "google_rss",
        "is_active": True,
        "fetch_config": {
            "query": "社会 OR 民生",
            "language": "zh",
            "country": "cn",
            "page_size": 20,
        },
    },
]

# 分类元数据（前端展示用）
CATEGORIES = [
    {"key": "tech", "name": "科技"},
    {"key": "finance", "name": "财经"},
    {"key": "world", "name": "国际"},
    {"key": "society", "name": "社会"},
]


def ensure_indexes():
    """创建 news 模块必要的索引（幂等）"""
    # news_sources 索引
    mongo.db.news_sources.create_index("category")
    mongo.db.news_sources.create_index("adapter_type")

    # articles 中 news 相关索引（补充 rss 模块已建的索引）
    mongo.db.articles.create_index([("category", 1), ("published_at", -1)])
    mongo.db.articles.create_index([("source_type", 1), ("is_read_later", 1)])
    mongo.db.articles.create_index("news_source_id")


def seed_news_sources():
    """初始化预设新闻源（幂等：按 url 判断是否已存在）"""
    for src in SEED_NEWS_SOURCES:
        existing = mongo.db.news_sources.find_one({"url": src["url"]})
        if existing:
            continue
        doc = {
            **src,
            "last_fetched_at": None,
            "error_count": 0,
            "last_error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        mongo.db.news_sources.insert_one(doc)
