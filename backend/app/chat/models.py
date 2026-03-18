from ..extensions import mongo


def ensure_indexes():
    """为 chat_sessions 集合创建索引"""
    mongo.db.chat_sessions.create_index([("updated_at", -1)])
