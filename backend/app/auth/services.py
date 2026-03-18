from datetime import datetime, timezone

import bcrypt

from app.extensions import mongo


def get_app_config():
    """获取全局配置文档"""
    return mongo.db.app_config.find_one({"_id": "app_config"})


def is_password_set():
    """检查是否已设置密码"""
    config = get_app_config()
    return config is not None and config.get("password_hash") is not None


def setup_password(password):
    """首次设置密码"""
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    mongo.db.app_config.update_one(
        {"_id": "app_config"},
        {
            "$set": {
                "password_hash": password_hash.decode('utf-8'),
                "created_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "settings": {
                    "theme": "light",
                    "language": "zh-CN",
                    "dashboard_layout": {},
                    "weather_city": "北京",
                },
            },
        },
        upsert=True,
    )


def verify_password(password):
    """验证密码"""
    config = get_app_config()
    if config is None or config.get("password_hash") is None:
        return False
    stored_hash = config["password_hash"].encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)


def change_password(old_password, new_password):
    """修改密码，返回 (success, error_message)"""
    if not verify_password(old_password):
        return False, "原密码错误"
    new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    mongo.db.app_config.update_one(
        {"_id": "app_config"},
        {"$set": {"password_hash": new_hash.decode('utf-8')}},
    )
    return True, None
