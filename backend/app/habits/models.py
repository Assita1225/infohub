from app.extensions import mongo


def ensure_indexes():
    """创建索引（幂等）"""
    mongo.db.check_ins.create_index(
        [("habit_id", 1), ("date", 1)],
        unique=True,
        name="checkin_habit_date_unique",
    )
