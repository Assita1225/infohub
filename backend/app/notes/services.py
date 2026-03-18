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


# ── 索引 ──

def ensure_text_index():
    """创建全文搜索索引（幂等）"""
    mongo.db.notes.create_index(
        [("title", "text"), ("content", "text")],
        name="notes_text_idx",
    )


# ── CRUD ──

def create_note(data):
    source = data.get("source") or {}
    doc = {
        "title": data.get("title", "").strip() or "无标题",
        "content": data.get("content", ""),
        "source": {
            "type": source.get("type", "manual"),
            "article_id": source.get("article_id"),
            "article_url": source.get("article_url", ""),
            "selected_text": source.get("selected_text", ""),
        },
        "tags": data.get("tags", []),
        "is_deleted": False,
        "deleted_at": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    result = mongo.db.notes.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def list_notes(page=1, page_size=20, search=None, tag=None, sort="updated_at"):
    query = {"is_deleted": False}
    if search:
        query["$text"] = {"$search": search}
    if tag:
        query["tags"] = tag

    total = mongo.db.notes.count_documents(query)

    sort_field = sort if sort in ("updated_at", "created_at", "title") else "updated_at"
    sort_dir = 1 if sort_field == "title" else -1

    items = (
        mongo.db.notes.find(query)
        .sort(sort_field, sort_dir)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return [_str_id(n) for n in items], total


def get_note(note_id):
    try:
        doc = mongo.db.notes.find_one({"_id": ObjectId(note_id)})
    except InvalidId:
        return None
    return _str_id(doc)


def update_note(note_id, data):
    allowed = {"title", "content", "tags", "source"}
    update_fields = {k: v for k, v in data.items() if k in allowed}
    if not update_fields:
        return None
    update_fields["updated_at"] = _now()
    try:
        result = mongo.db.notes.update_one(
            {"_id": ObjectId(note_id)},
            {"$set": update_fields},
        )
    except InvalidId:
        return None
    if result.matched_count == 0:
        return None
    return get_note(note_id)


def soft_delete_note(note_id):
    try:
        result = mongo.db.notes.update_one(
            {"_id": ObjectId(note_id), "is_deleted": False},
            {"$set": {"is_deleted": True, "deleted_at": _now()}},
        )
    except InvalidId:
        return False
    return result.modified_count > 0


def restore_note(note_id):
    try:
        result = mongo.db.notes.update_one(
            {"_id": ObjectId(note_id), "is_deleted": True},
            {"$set": {"is_deleted": False, "deleted_at": None}},
        )
    except InvalidId:
        return False
    return result.modified_count > 0


def search_notes(q, page=1, page_size=20):
    if not q or not q.strip():
        return [], 0

    query = {"$text": {"$search": q}, "is_deleted": False}
    total = mongo.db.notes.count_documents(query)
    items = (
        mongo.db.notes.find(query, {"score": {"$meta": "textScore"}})
        .sort([("score", {"$meta": "textScore"})])
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return [_str_id(n) for n in items], total


def list_trash(page=1, page_size=20):
    query = {"is_deleted": True}
    total = mongo.db.notes.count_documents(query)
    items = (
        mongo.db.notes.find(query)
        .sort("deleted_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return [_str_id(n) for n in items], total
