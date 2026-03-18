"""Recommend 模块业务逻辑"""
import re
from datetime import datetime, timedelta, timezone

from app.extensions import mongo
from .models import PRESET_TAGS


# ── 预设标签同义词/关联词映射 ──

TAG_SYNONYMS = {
    "人工智能": ["人工智能", "AI", "GPT", "大模型", "机器学习", "深度学习", "LLM", "OpenAI", "Claude", "neural"],
    "区块链": ["区块链", "blockchain", "crypto", "比特币", "bitcoin", "以太坊", "web3"],
    "前端开发": ["前端", "frontend", "Vue", "React", "JavaScript", "TypeScript", "CSS", "nextjs", "svelte"],
    "后端开发": ["后端", "backend", "Python", "Java", "Go", "Rust", "Node.js", "Django", "Flask", "Spring"],
    "金融": ["金融", "股市", "基金", "A股", "美股", "finance", "投资", "理财"],
    "创业": ["创业", "融资", "startup", "创投", "风投", "YC", "独角兽"],
    "游戏": ["游戏", "game", "Steam", "任天堂", "PlayStation", "电竞", "手游"],
    "设计": ["设计", "design", "UI", "UX", "Figma", "设计师"],
    "科学": ["科学", "science", "物理", "化学", "生物", "太空", "NASA", "量子"],
    "教育": ["教育", "考研", "高考", "大学", "留学", "教师"],
    "健康": ["健康", "医疗", "医院", "疫情", "health", "医学"],
    "体育": ["体育", "NBA", "足球", "奥运", "CBA", "欧冠", "世界杯"],
    "数码": ["数码", "手机", "iPhone", "华为", "小米", "Apple", "Android", "芯片"],
    "汽车": ["汽车", "新能源", "特斯拉", "Tesla", "电动车", "比亚迪", "自动驾驶"],
}

_SOURCE_LABELS = {
    "github": "GitHub",
    "baidu": "百度",
    "weibo": "微博",
    "google_trends": "Google",
}


# ── 标签管理 ──

def get_tags():
    """获取预设标签 + 用户已选标签 + 自定义标签"""
    doc = mongo.db.user_tags.find_one({"_id": "user_tags"})
    if not doc:
        return {
            "preset_tags": PRESET_TAGS,
            "custom_tags": [],
            "selected_tags": [],
        }
    return {
        "preset_tags": doc.get("preset_tags", PRESET_TAGS),
        "custom_tags": doc.get("custom_tags", []),
        "selected_tags": doc.get("selected_tags", []),
    }


def update_selected_tags(selected: list[str]):
    """更新用户选中的标签"""
    mongo.db.user_tags.update_one(
        {"_id": "user_tags"},
        {
            "$set": {
                "selected_tags": selected,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True,
    )
    return True


def add_custom_tag(tag: str):
    """添加自定义标签"""
    tag = tag.strip()
    if not tag:
        return False, "标签不能为空"

    doc = mongo.db.user_tags.find_one({"_id": "user_tags"})
    if doc:
        all_tags = doc.get("preset_tags", []) + doc.get("custom_tags", [])
        if tag in all_tags:
            return False, "标签已存在"

    mongo.db.user_tags.update_one(
        {"_id": "user_tags"},
        {
            "$addToSet": {"custom_tags": tag},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
        upsert=True,
    )
    return True, None


def delete_custom_tag(tag: str):
    """删除自定义标签（同时从 selected_tags 中移除）"""
    mongo.db.user_tags.update_one(
        {"_id": "user_tags"},
        {
            "$pull": {"custom_tags": tag, "selected_tags": tag},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )
    return True


# ── 推荐 Feed ──

def _expand_keywords(tags: list[str]) -> list[str]:
    """将选中标签展开为所有同义词/关联词。
    预设标签用 TAG_SYNONYMS 映射；自定义标签直接作为关键词。"""
    keywords = []
    for tag in tags:
        synonyms = TAG_SYNONYMS.get(tag)
        if synonyms:
            keywords.extend(synonyms)
        else:
            keywords.append(tag)
    return list(dict.fromkeys(keywords))  # 去重保序


def _find_matched_keywords(item: dict, keywords: list[str]) -> list[str]:
    """找出条目中匹配到的关键词（用于前端高亮展示）"""
    title = item.get("title", "")
    tags = item.get("tags", [])
    matched = []
    for kw in keywords:
        # 在 title 中不区分大小写匹配
        if re.search(re.escape(kw), title, re.IGNORECASE):
            matched.append(kw)
        elif kw.lower() in [t.lower() for t in tags]:
            matched.append(kw)
    return matched


def get_feed(tags: list[str], limit: int = 20):
    """根据选中标签从 trending_items 中模糊匹配推荐内容，按热度降序"""
    if not tags:
        return {"items": [], "hint": "请选择兴趣标签以获取个性化推荐"}

    keywords = _expand_keywords(tags)
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    # 构建正则：在 title 中匹配任意关键词（不区分大小写）
    regex_pattern = "|".join(re.escape(kw) for kw in keywords)
    # 同时也做 tags 精确匹配（不区分大小写的 $in）
    keywords_lower = [kw.lower() for kw in keywords]

    matches = list(
        mongo.db.trending_items.find(
            {
                "fetched_at": {"$gte": since},
                "$or": [
                    {"title": {"$regex": regex_pattern, "$options": "i"}},
                    {"tags": {"$in": keywords}},
                ],
            },
            {"_id": 0, "title": 1, "url": 1, "hot_score": 1, "source": 1, "tags": 1},
        )
        .sort("hot_score", -1)
        .limit(limit)
    )

    if not matches:
        return {"items": [], "hint": "当前热榜中暂无匹配内容，试试其他标签"}

    results = []
    for item in matches:
        source_key = item.get("source", "")
        matched_kws = _find_matched_keywords(item, keywords)
        results.append({
            "title": item["title"],
            "url": item["url"],
            "source": source_key,
            "source_label": _SOURCE_LABELS.get(source_key, source_key),
            "hot_score": item.get("hot_score", 0),
            "tags": item.get("tags", []),
            "matched_keywords": matched_kws,
        })

    hint = ""
    if len(results) < 3:
        hint = "匹配结果较少，试试选择更多标签"

    return {"items": results, "hint": hint}
