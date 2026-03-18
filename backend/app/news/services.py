"""News 模块业务逻辑"""
from datetime import datetime, timezone

from bson import ObjectId

from app.extensions import mongo
from .models import CATEGORIES


def _str_id(doc):
    """ObjectId → str"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    if doc and "news_source_id" in doc and isinstance(doc["news_source_id"], ObjectId):
        doc["news_source_id"] = str(doc["news_source_id"])
    return doc


def _now():
    return datetime.now(timezone.utc).isoformat()


# ── 分类 ──

def get_categories():
    """获取分类列表（含每个分类的文章数）"""
    pipeline = [
        {"$match": {"source_type": "news"}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
    ]
    result = list(mongo.db.articles.aggregate(pipeline))
    counts = {r["_id"]: r["count"] for r in result}

    return [
        {"key": c["key"], "name": c["name"], "count": counts.get(c["key"], 0)}
        for c in CATEGORIES
    ]


# ── 文章列表 ──

def list_articles(category=None, page=1, page_size=20):
    """按分类获取新闻文章（分页）"""
    query = {"source_type": "news"}
    if category:
        query["category"] = category
    total = mongo.db.articles.count_documents(query)
    items = (
        mongo.db.articles.find(query)
        .sort("published_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return [_str_id(a) for a in items], total


def get_article(article_id):
    """获取单篇新闻详情"""
    doc = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
    return _str_id(doc)


# ── AI 摘要 ──

def summarize_article(article_id):
    """按需生成 AI 摘要（有缓存直接返回）"""
    doc = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
    if not doc:
        return None, None, "文章不存在"

    status = doc.get("summary_status", "none")
    if status == "done" and doc.get("summary"):
        return doc["summary"], "done", None

    content = doc.get("content", "")
    if not content or not content.strip():
        mongo.db.articles.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": {"summary_status": "failed"}},
        )
        return None, "failed", "文章正文为空，无法生成摘要"

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


# ── 稍后读 ──

def set_read_later(article_id, value=True):
    """设置/取消稍后读"""
    result = mongo.db.articles.update_one(
        {"_id": ObjectId(article_id)},
        {"$set": {"is_read_later": value}},
    )
    return result.modified_count > 0 or result.matched_count > 0


def list_read_later(page=1, page_size=20):
    """获取稍后读列表"""
    query = {"source_type": "news", "is_read_later": True}
    total = mongo.db.articles.count_documents(query)
    items = (
        mongo.db.articles.find(query)
        .sort("published_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return [_str_id(a) for a in items], total


# ── 转笔记 ──

def article_to_note(article_id):
    """将新闻文章转为笔记初始内容"""
    doc = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
    if not doc:
        return None, "文章不存在"

    from app.notes.services import create_note

    note_data = {
        "title": doc.get("title", "无标题"),
        "content": _build_note_content(doc),
        "source": {
            "type": "news",
            "article_id": str(doc["_id"]),
            "article_url": doc.get("url", ""),
        },
        "tags": doc.get("tags", []),
    }

    note = create_note(note_data)
    return note, None


def _build_note_content(doc):
    """构建笔记初始内容"""
    parts = []
    if doc.get("url"):
        parts.append(f"[原文链接]({doc['url']})\n")
    if doc.get("summary"):
        parts.append(f"**AI 摘要：**\n{doc['summary']}\n")
    if doc.get("content"):
        # 截取前 500 字作为笔记初始内容
        content = doc["content"][:500]
        if len(doc["content"]) > 500:
            content += "..."
        parts.append(f"**正文摘录：**\n{content}")
    return "\n".join(parts)
