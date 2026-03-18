"""Trending 模块的 MongoDB 索引初始化"""
from app.extensions import mongo


def ensure_indexes():
    """创建 trending 模块必要的索引（幂等）"""
    col = mongo.db.trending_items

    # 按来源 + 抓取时间查询
    col.create_index([("source", 1), ("fetched_at", -1)])

    # TTL 索引：24h 后自动删除过期数据
    col.create_index("expires_at", expireAfterSeconds=0)

    # tags 索引：用于推荐模块匹配
    col.create_index("tags")
