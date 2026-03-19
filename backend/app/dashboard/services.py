from datetime import datetime, timezone
from bson import ObjectId

from app.extensions import mongo


# ── 微件布局 ──

def get_widget_layout():
    """获取用户的微件布局配置"""
    config = mongo.db.app_config.find_one({"_id": "app_config"})
    if config and config.get("settings", {}).get("dashboard_layout"):
        return config["settings"]["dashboard_layout"]
    # 默认布局（row-height=36px, col-num=6）
    return [
        {"i": "clock",        "x": 0, "y": 0, "w": 2, "h": 5},
        {"i": "calendar",     "x": 2, "y": 0, "w": 2, "h": 8},
        {"i": "todo",         "x": 4, "y": 0, "w": 2, "h": 8},
        {"i": "weather",      "x": 0, "y": 5, "w": 2, "h": 5},
        {"i": "recent_notes", "x": 0, "y": 10, "w": 2, "h": 7},
    ]


def save_widget_layout(layout):
    """保存微件布局配置"""
    mongo.db.app_config.update_one(
        {"_id": "app_config"},
        {"$set": {"settings.dashboard_layout": layout}},
        upsert=True,
    )


# ── 城市设置 ──

def get_weather_city():
    """获取天气城市设置"""
    config = mongo.db.app_config.find_one({"_id": "app_config"})
    if config:
        return config.get("settings", {}).get("weather_city", "杭州")
    return "杭州"


def save_weather_city(city):
    """保存天气城市设置"""
    mongo.db.app_config.update_one(
        {"_id": "app_config"},
        {"$set": {"settings.weather_city": city}},
        upsert=True,
    )


# ── 待办事项 ──

def _serialize_todo(doc):
    """将 MongoDB 文档转为可序列化的 dict"""
    doc["_id"] = str(doc["_id"])
    return doc


def list_todos():
    """获取所有待办事项"""
    items = mongo.db.todos.find().sort("created_at", -1)
    return [_serialize_todo(t) for t in items]


def create_todo(title):
    """创建待办事项"""
    doc = {
        "title": title,
        "completed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = mongo.db.todos.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def update_todo(todo_id, data):
    """更新待办事项（标题 / 完成状态）"""
    update_fields = {}
    if "title" in data:
        update_fields["title"] = data["title"]
    if "completed" in data:
        update_fields["completed"] = data["completed"]
    if not update_fields:
        return None
    mongo.db.todos.update_one({"_id": ObjectId(todo_id)}, {"$set": update_fields})
    doc = mongo.db.todos.find_one({"_id": ObjectId(todo_id)})
    return _serialize_todo(doc) if doc else None


def delete_todo(todo_id):
    """删除待办事项"""
    result = mongo.db.todos.delete_one({"_id": ObjectId(todo_id)})
    return result.deleted_count > 0


# ── 活跃微件列表 ──

DEFAULT_ACTIVE_WIDGETS = ["clock", "calendar", "todo", "weather", "recent_notes"]


def get_active_widgets():
    """获取用户已激活的微件列表"""
    config = mongo.db.app_config.find_one({"_id": "app_config"})
    if config:
        active = config.get("settings", {}).get("active_widgets")
        if active is not None:
            return active
    return list(DEFAULT_ACTIVE_WIDGETS)


def save_active_widgets(widgets):
    """保存用户已激活的微件列表"""
    mongo.db.app_config.update_one(
        {"_id": "app_config"},
        {"$set": {"settings.active_widgets": widgets}},
        upsert=True,
    )


# ── 倒计时 ──

def _serialize_countdown(doc):
    """将 MongoDB 文档转为可序列化的 dict"""
    doc["_id"] = str(doc["_id"])
    return doc


def list_countdowns():
    """获取所有倒计时"""
    items = mongo.db.countdowns.find().sort("target_date", 1)
    return [_serialize_countdown(c) for c in items]


def create_countdown(name, target_date):
    """创建倒计时"""
    doc = {
        "name": name,
        "target_date": target_date,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = mongo.db.countdowns.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def delete_countdown(countdown_id):
    """删除倒计时"""
    result = mongo.db.countdowns.delete_one({"_id": ObjectId(countdown_id)})
    return result.deleted_count > 0
