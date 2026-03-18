"""Recommend 模块的预设标签 + 索引初始化"""
from datetime import datetime, timezone

from app.extensions import mongo

# 系统预设标签
PRESET_TAGS = [
    "人工智能", "区块链", "前端开发", "后端开发",
    "金融", "创业", "游戏", "设计", "科学",
    "教育", "健康", "体育", "数码", "汽车",
]


def ensure_indexes():
    """创建 recommend 模块必要的索引（幂等）"""
    # user_tags 只有一条文档，无需额外索引
    pass


def seed_user_tags():
    """初始化 user_tags 文档（幂等）"""
    existing = mongo.db.user_tags.find_one({"_id": "user_tags"})
    if existing:
        return

    mongo.db.user_tags.insert_one({
        "_id": "user_tags",
        "preset_tags": PRESET_TAGS,
        "custom_tags": [],
        "selected_tags": [],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
