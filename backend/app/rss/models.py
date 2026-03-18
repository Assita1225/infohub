"""RSS 模块的 MongoDB 索引初始化"""
from app.extensions import mongo


def ensure_indexes():
    """创建必要的索引（幂等操作，可重复调用）"""
    # rss_feeds 索引
    mongo.db.rss_feeds.create_index("group")

    # articles 索引
    mongo.db.articles.create_index([("feed_id", 1), ("published_at", -1)])
    mongo.db.articles.create_index([("source_type", 1), ("is_read", 1), ("published_at", -1)])
    mongo.db.articles.create_index("url", unique=True)
    mongo.db.articles.create_index("simhash")
    mongo.db.articles.create_index("tags")
