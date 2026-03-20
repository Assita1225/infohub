from datetime import datetime, timezone
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


# ── CRUD ──

def create_record(data):
    doc = {
        "amount": float(data.get("amount", 0)),
        "type": data.get("type", "expense"),
        "category": data.get("category", "其他"),
        "note": data.get("note", "").strip(),
        "date": data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "created_at": _now(),
    }
    result = mongo.db.finance_records.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def list_records(month=None, record_type=None, page=1, page_size=50):
    query = {}
    if month:
        # month 格式: "2026-03"
        query["date"] = {"$gte": f"{month}-01", "$lte": f"{month}-31"}
    if record_type and record_type in ("income", "expense"):
        query["type"] = record_type

    total = mongo.db.finance_records.count_documents(query)
    skip = (page - 1) * page_size
    items = mongo.db.finance_records.find(query).sort("date", -1).skip(skip).limit(page_size)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_str_id(r) for r in items],
    }


def update_record(record_id, data):
    allowed = {"amount", "type", "category", "note", "date"}
    update_fields = {}
    for k, v in data.items():
        if k in allowed:
            update_fields[k] = float(v) if k == "amount" else v
    if not update_fields:
        return None
    try:
        result = mongo.db.finance_records.update_one(
            {"_id": ObjectId(record_id)},
            {"$set": update_fields},
        )
    except InvalidId:
        return None
    if result.matched_count == 0:
        return None
    doc = mongo.db.finance_records.find_one({"_id": ObjectId(record_id)})
    return _str_id(doc)


def delete_record(record_id):
    try:
        result = mongo.db.finance_records.delete_one({"_id": ObjectId(record_id)})
    except InvalidId:
        return False
    return result.deleted_count > 0


# ── 汇总 ──

def get_summary(month):
    """月度汇总：总收入、总支出、各分类占比"""
    date_query = {"$gte": f"{month}-01", "$lte": f"{month}-31"}

    pipeline = [
        {"$match": {"date": date_query}},
        {"$group": {
            "_id": {"type": "$type", "category": "$category"},
            "total": {"$sum": "$amount"},
        }},
    ]
    results = list(mongo.db.finance_records.aggregate(pipeline))

    income = 0.0
    expense = 0.0
    categories = {"income": {}, "expense": {}}

    for r in results:
        t = r["_id"]["type"]
        cat = r["_id"]["category"]
        amt = r["total"]
        if t == "income":
            income += amt
        else:
            expense += amt
        categories[t][cat] = round(amt, 2)

    return {
        "month": month,
        "income": round(income, 2),
        "expense": round(expense, 2),
        "balance": round(income - expense, 2),
        "categories": categories,
    }


def get_trend(year):
    """年度趋势：每月收支对比"""
    pipeline = [
        {"$match": {"date": {"$gte": f"{year}-01-01", "$lte": f"{year}-12-31"}}},
        {"$addFields": {"month": {"$substr": ["$date", 0, 7]}}},
        {"$group": {
            "_id": {"month": "$month", "type": "$type"},
            "total": {"$sum": "$amount"},
        }},
        {"$sort": {"_id.month": 1}},
    ]
    results = list(mongo.db.finance_records.aggregate(pipeline))

    months_data = {}
    for r in results:
        m = r["_id"]["month"]
        t = r["_id"]["type"]
        if m not in months_data:
            months_data[m] = {"month": m, "income": 0, "expense": 0}
        months_data[m][t] = round(r["total"], 2)

    # 填充空月份
    trend = []
    for i in range(1, 13):
        m = f"{year}-{i:02d}"
        if m in months_data:
            trend.append(months_data[m])
        else:
            trend.append({"month": m, "income": 0, "expense": 0})

    return trend
