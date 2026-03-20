from datetime import datetime, timezone
from bson import ObjectId

from app.extensions import mongo


def _str_id(doc):
    """ObjectId → str"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    if doc and "feed_id" in doc and isinstance(doc["feed_id"], ObjectId):
        doc["feed_id"] = str(doc["feed_id"])
    return doc


# ── 订阅源 CRUD ──

def list_feeds(group=None):
    query = {"is_active": True}
    if group:
        query["group"] = group
    feeds = mongo.db.rss_feeds.find(query).sort("created_at", -1)
    return [_str_id(f) for f in feeds]


def get_feed(feed_id):
    doc = mongo.db.rss_feeds.find_one({"_id": ObjectId(feed_id)})
    return _str_id(doc)


def create_feed(data):
    doc = {
        "title": data["title"],
        "url": data["url"],
        "site_url": data.get("site_url", ""),
        "group": data.get("group", "未分组"),
        "feed_type": data.get("feed_type", "rss"),       # "rss" | "web_monitor"
        "css_selector": data.get("css_selector", ""),     # 网页监控的 CSS 选择器（可选）
        "is_active": True,
        "display_count": data.get("display_count", 5),
        "last_fetched_at": None,
        "error_count": 0,
        "last_error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = mongo.db.rss_feeds.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def update_feed(feed_id, data):
    allowed = {"title", "url", "site_url", "group", "is_active", "display_count", "feed_type", "css_selector"}
    update_fields = {k: v for k, v in data.items() if k in allowed}
    if not update_fields:
        return None
    mongo.db.rss_feeds.update_one({"_id": ObjectId(feed_id)}, {"$set": update_fields})
    return get_feed(feed_id)


def delete_feed(feed_id):
    result = mongo.db.rss_feeds.delete_one({"_id": ObjectId(feed_id)})
    if result.deleted_count:
        # 同时删除该源的所有文章
        mongo.db.articles.delete_many({"feed_id": ObjectId(feed_id)})
    return result.deleted_count > 0


def create_group_record(name):
    """在 rss_groups 集合中持久化用户创建的分组"""
    mongo.db.rss_groups.update_one(
        {"name": name},
        {"$setOnInsert": {"name": name}},
        upsert=True,
    )


def get_feed_groups():
    """获取所有分组名（含每组订阅源数量）
    合并：用户主动创建的分组（即使为空）+ rss_feeds 中实际存在的 group 值"""
    # 从 rss_feeds 聚合得到每组数量
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$group", "count": {"$sum": 1}}},
    ]
    result = list(mongo.db.rss_feeds.aggregate(pipeline))
    counts = {r["_id"]: r["count"] for r in result}

    # 获取用户主动创建的所有分组名
    user_groups = mongo.db.rss_groups.find({}, {"_id": 0, "name": 1})
    all_names = set(counts.keys()) | {g["name"] for g in user_groups}

    return [{"name": n, "count": counts.get(n, 0)} for n in sorted(all_names)]


def rename_group(old_name, new_name):
    """重命名分组"""
    result = mongo.db.rss_feeds.update_many(
        {"group": old_name},
        {"$set": {"group": new_name}},
    )
    # 同步更新 rss_groups 记录
    mongo.db.rss_groups.update_one({"name": old_name}, {"$set": {"name": new_name}})
    return result.modified_count


def delete_group(name):
    """删除分组，该分组下的订阅源移到 '未分组'"""
    result = mongo.db.rss_feeds.update_many(
        {"group": name},
        {"$set": {"group": "未分组"}},
    )
    # 从 rss_groups 集合中删除记录
    mongo.db.rss_groups.delete_one({"name": name})
    return result.modified_count


# ── 文章 CRUD ──

def list_articles(feed_id, page=1, page_size=20):
    query = {"feed_id": ObjectId(feed_id), "source_type": "rss"}
    total = mongo.db.articles.count_documents(query)
    items = (
        mongo.db.articles.find(query)
        .sort("published_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return [_str_id(a) for a in items], total


def get_article(article_id):
    doc = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
    return _str_id(doc)


def mark_read(article_id):
    mongo.db.articles.update_one(
        {"_id": ObjectId(article_id)},
        {"$set": {"is_read": True}},
    )


def toggle_favorite(article_id):
    doc = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
    if not doc:
        return None
    new_val = not doc.get("is_favorited", False)
    mongo.db.articles.update_one(
        {"_id": ObjectId(article_id)},
        {"$set": {"is_favorited": new_val}},
    )
    return new_val


def summarize_article(article_id):
    """按需生成 AI 摘要，有缓存则直接返回。
    返回 (summary, status, error_msg)
    """
    doc = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
    if not doc:
        return None, None, "文章不存在"

    status = doc.get("summary_status", "none")

    # 已有摘要，直接返回
    if status == "done" and doc.get("summary"):
        return doc["summary"], "done", None

    # 获取正文
    content = doc.get("content", "")
    if not content or not content.strip():
        mongo.db.articles.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": {"summary_status": "failed"}},
        )
        return None, "failed", "文章正文为空，无法生成摘要"

    # 调用 LLM
    from app.common.llm_client import llm_client

    try:
        summary = llm_client.summarize(content)
        mongo.db.articles.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": {"summary": summary, "summary_status": "done"}},
        )
        return summary, "done", None
    except Exception as e:
        mongo.db.articles.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": {"summary_status": "failed"}},
        )
        return None, "failed", str(e)


def article_to_note(article_id):
    """将 RSS 文章保存到笔记本"""
    doc = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
    if not doc:
        return None, "文章不存在"

    from app.notes.services import create_note

    parts = []
    if doc.get("url"):
        parts.append(f"[原文链接]({doc['url']})\n")
    if doc.get("summary"):
        parts.append(f"**AI 摘要：**\n{doc['summary']}\n")
    if doc.get("content"):
        content = doc["content"][:500]
        if len(doc["content"]) > 500:
            content += "..."
        parts.append(f"**正文摘录：**\n{content}")

    note_data = {
        "title": doc.get("title", "无标题"),
        "content": "\n".join(parts),
        "source": {
            "type": "rss",
            "article_id": str(doc["_id"]),
            "article_url": doc.get("url", ""),
        },
        "tags": doc.get("tags", []),
    }

    note = create_note(note_data)
    return note, None


def get_reading_timeline(days=7):
    """获取最近 N 天已读文章，按日期分组"""
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    pipeline = [
        {"$match": {
            "is_read": True,
            "source_type": "rss",
            "published_at": {"$gte": cutoff},
        }},
        {"$lookup": {
            "from": "rss_feeds",
            "localField": "feed_id",
            "foreignField": "_id",
            "as": "feed_info",
        }},
        {"$unwind": {"path": "$feed_info", "preserveNullAndEmptyArrays": True}},
        {"$sort": {"published_at": -1}},
        {"$project": {
            "_id": {"$toString": "$_id"},
            "title": 1,
            "source": {"$ifNull": ["$feed_info.title", "未知来源"]},
            "published_at": 1,
            "tags": {"$ifNull": ["$tags", []]},
            "summary": {"$ifNull": ["$summary", ""]},
            "url": 1,
        }},
    ]
    articles = list(mongo.db.articles.aggregate(pipeline))

    # 按日期分组
    from collections import OrderedDict
    grouped = OrderedDict()
    for a in articles:
        date_str = a.get("published_at", "")[:10]  # YYYY-MM-DD
        if not date_str:
            continue
        if date_str not in grouped:
            grouped[date_str] = []
        grouped[date_str].append(a)

    result = []
    for date, items in grouped.items():
        result.append({"date": date, "count": len(items), "articles": items})
    return result


def get_feeds_health():
    """获取所有订阅源的健康状态"""
    feeds = mongo.db.rss_feeds.find(
        {"is_active": True},
        {"title": 1, "url": 1, "group": 1, "error_count": 1,
         "last_error": 1, "last_fetched_at": 1, "created_at": 1},
    )
    result = []
    for f in feeds:
        error_count = f.get("error_count", 0)
        if error_count >= 5:
            status = "danger"
        elif error_count > 0:
            status = "warning"
        else:
            status = "healthy"

        # 计算成功率（基于 error_count 的近似值）
        total_fetches = max(1, error_count + 1)  # 近似
        success_rate = round((1 - error_count / max(total_fetches, 1)) * 100, 1) if error_count > 0 else 100.0

        result.append({
            "_id": str(f["_id"]),
            "title": f.get("title", ""),
            "url": f.get("url", ""),
            "group": f.get("group", ""),
            "error_count": error_count,
            "last_error": f.get("last_error"),
            "last_fetched_at": f.get("last_fetched_at"),
            "status": status,
            "success_rate": success_rate,
        })
    return result


def get_rss_stats():
    """各分组文章数统计"""
    pipeline = [
        {"$match": {"source_type": "rss"}},
        {"$lookup": {
            "from": "rss_feeds",
            "localField": "feed_id",
            "foreignField": "_id",
            "as": "feed",
        }},
        {"$unwind": "$feed"},
        {"$group": {
            "_id": "$feed.group",
            "total": {"$sum": 1},
            "unread": {"$sum": {"$cond": [{"$eq": ["$is_read", False]}, 1, 0]}},
        }},
    ]
    result = list(mongo.db.articles.aggregate(pipeline))
    return [{"group": r["_id"], "total": r["total"], "unread": r["unread"]} for r in result]
