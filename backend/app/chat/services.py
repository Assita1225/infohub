"""Chat 模块业务逻辑 —— 会话管理、Prompt 构建。"""

from datetime import datetime, timezone

from bson import ObjectId

from ..extensions import mongo


def _str_id(doc):
    """将 MongoDB 文档的 _id 从 ObjectId 转为 string"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


def _now():
    """UTC 时间戳"""
    return datetime.now(timezone.utc)


# ── 会话 CRUD ──────────────────────────────────────────

def create_session(context=None):
    """创建新会话，返回文档（_id 已转 str）。"""
    doc = {
        "title": "新对话",
        "context": context or {"page": "general"},
        "messages": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    result = mongo.db.chat_sessions.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def list_sessions():
    """返回所有会话（降序），仅投影摘要字段。"""
    cursor = mongo.db.chat_sessions.find(
        {},
        {
            "title": 1,
            "context.page": 1,
            "context.article_title": 1,
            "created_at": 1,
            "updated_at": 1,
        },
    ).sort("updated_at", -1)
    return [_str_id(doc) for doc in cursor]


def get_session(session_id):
    """根据 ID 获取完整会话（含 messages）。"""
    try:
        doc = mongo.db.chat_sessions.find_one({"_id": ObjectId(session_id)})
    except Exception:
        return None
    return _str_id(doc) if doc else None


def delete_session(session_id):
    """删除会话，返回是否成功。"""
    try:
        result = mongo.db.chat_sessions.delete_one({"_id": ObjectId(session_id)})
    except Exception:
        return False
    return result.deleted_count == 1


# ── 消息管理 ───────────────────────────────────────────

def add_message(session_id, role, content):
    """向会话追加一条消息。首条 user 消息自动设置标题。"""
    msg = {
        "role": role,
        "content": content,
        "timestamp": _now(),
    }

    update = {
        "$push": {"messages": msg},
        "$set": {"updated_at": _now()},
    }

    # 首条 user 消息 → 自动生成标题
    if role == "user":
        session = mongo.db.chat_sessions.find_one(
            {"_id": ObjectId(session_id)},
            {"messages": 1},
        )
        if session and len(session.get("messages", [])) == 0:
            title = content[:20].strip()
            if len(content) > 20:
                title += "…"
            update["$set"]["title"] = title

    mongo.db.chat_sessions.update_one(
        {"_id": ObjectId(session_id)},
        update,
    )


# ── Prompt 构建 ────────────────────────────────────────

def build_prompt(session_id, user_message):
    """构建 LLM 调用所需的 system_prompt 和 messages 列表。

    Returns
    -------
    (system_prompt: str, messages: list[dict])
    """
    session = mongo.db.chat_sessions.find_one({"_id": ObjectId(session_id)})
    if not session:
        return "", [{"role": "user", "content": user_message}]

    # ── system prompt ──
    system_prompt = (
        "你是一个信息分析助手，名叫 InfoHub AI。"
        "你的职责是帮助用户分析、总结和理解各类信息内容。请用中文回答。"
    )

    ctx = session.get("context") or {}
    if ctx.get("article_content"):
        article_title = ctx.get("article_title", "")
        article_content = ctx["article_content"][:3000]
        system_prompt += (
            f"\n\n当前用户正在阅读以下文章，请基于此文章回答问题：\n"
            f"标题：{article_title}\n内容：{article_content}"
        )

    # ── 对话历史（最近 10 轮 = 20 条） ──
    history = session.get("messages", [])[-20:]
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history
    ]
    messages.append({"role": "user", "content": user_message})

    return system_prompt, messages
