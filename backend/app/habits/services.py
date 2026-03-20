from datetime import datetime, timezone, timedelta
from bson import ObjectId
from bson.errors import InvalidId

from app.extensions import mongo


def _str_id(doc):
    """ObjectId → str"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


def _now():
    return datetime.now(timezone.utc).isoformat()


def _today():
    """当前日期字符串，如 2026-03-20"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── 习惯 CRUD ──

def create_habit(data):
    doc = {
        "name": data.get("name", "").strip(),
        "icon": data.get("icon", "📌"),
        "color": data.get("color", "#C45A3C"),
        "created_at": _now(),
    }
    result = mongo.db.habits.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def list_habits():
    items = mongo.db.habits.find().sort("created_at", 1)
    return [_str_id(h) for h in items]


def get_habit(habit_id):
    try:
        doc = mongo.db.habits.find_one({"_id": ObjectId(habit_id)})
    except InvalidId:
        return None
    return _str_id(doc)


def update_habit(habit_id, data):
    allowed = {"name", "icon", "color"}
    update_fields = {k: v for k, v in data.items() if k in allowed}
    if not update_fields:
        return None
    try:
        result = mongo.db.habits.update_one(
            {"_id": ObjectId(habit_id)},
            {"$set": update_fields},
        )
    except InvalidId:
        return None
    if result.matched_count == 0:
        return None
    return get_habit(habit_id)


def delete_habit(habit_id):
    try:
        oid = ObjectId(habit_id)
    except InvalidId:
        return False
    result = mongo.db.habits.delete_one({"_id": oid})
    if result.deleted_count > 0:
        # 同时删除该习惯的所有打卡记录
        mongo.db.check_ins.delete_many({"habit_id": habit_id})
        return True
    return False


# ── 打卡 ──

def check_in(habit_id, date=None):
    """今日打卡（幂等）"""
    if not get_habit(habit_id):
        return None
    date = date or _today()
    # upsert 保证幂等
    mongo.db.check_ins.update_one(
        {"habit_id": habit_id, "date": date},
        {"$setOnInsert": {"habit_id": habit_id, "date": date, "created_at": _now()}},
        upsert=True,
    )
    return {"habit_id": habit_id, "date": date}


def cancel_check_in(habit_id, date=None):
    """取消今日打卡"""
    date = date or _today()
    result = mongo.db.check_ins.delete_one({"habit_id": habit_id, "date": date})
    return result.deleted_count > 0


def get_history(habit_id, year):
    """获取某年全部打卡记录"""
    start = f"{year}-01-01"
    end = f"{year}-12-31"
    records = mongo.db.check_ins.find(
        {"habit_id": habit_id, "date": {"$gte": start, "$lte": end}},
        {"_id": 0, "date": 1},
    ).sort("date", 1)
    return [r["date"] for r in records]


def get_stats():
    """统计每个习惯的连续天数、总天数、本月完成率"""
    habits = list_habits()
    today = _today()
    now = datetime.now(timezone.utc)
    month_start = now.strftime("%Y-%m-01")
    days_in_month = (now - datetime.strptime(month_start, "%Y-%m-%d").replace(tzinfo=timezone.utc)).days + 1

    result = []
    for h in habits:
        hid = h["_id"]
        # 总天数
        total = mongo.db.check_ins.count_documents({"habit_id": hid})

        # 本月打卡天数
        month_count = mongo.db.check_ins.count_documents({
            "habit_id": hid,
            "date": {"$gte": month_start, "$lte": today},
        })
        month_rate = round(month_count / days_in_month * 100) if days_in_month > 0 else 0

        # 连续天数（从今天往前数）
        streak = 0
        d = datetime.strptime(today, "%Y-%m-%d")
        while True:
            ds = d.strftime("%Y-%m-%d")
            if mongo.db.check_ins.find_one({"habit_id": hid, "date": ds}):
                streak += 1
                d -= timedelta(days=1)
            else:
                break

        # 最长连续天数
        all_dates = sorted([
            r["date"] for r in mongo.db.check_ins.find(
                {"habit_id": hid}, {"_id": 0, "date": 1}
            )
        ])
        max_streak = _calc_max_streak(all_dates)

        result.append({
            "habit_id": hid,
            "name": h["name"],
            "icon": h["icon"],
            "total": total,
            "streak": streak,
            "max_streak": max_streak,
            "month_rate": month_rate,
        })

    return result


def _calc_max_streak(sorted_dates):
    """计算最长连续天数"""
    if not sorted_dates:
        return 0
    max_s = 1
    cur = 1
    for i in range(1, len(sorted_dates)):
        prev = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d")
        curr = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
        if (curr - prev).days == 1:
            cur += 1
            max_s = max(max_s, cur)
        else:
            cur = 1
    return max_s


def get_today_checkins():
    """获取今日所有打卡记录"""
    today = _today()
    records = mongo.db.check_ins.find(
        {"date": today}, {"_id": 0, "habit_id": 1}
    )
    return {r["habit_id"] for r in records}
