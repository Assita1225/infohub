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


def update_selected_tags(selected: list):
    """更新用户选中的标签（带权重）
    selected: [{"name": "标签名", "weight": 0.5}, ...]
    """
    # 兼容旧格式：如果传入的是纯字符串数组，自动转换
    normalized = []
    for item in selected:
        if isinstance(item, str):
            normalized.append({"name": item, "weight": 0.5})
        elif isinstance(item, dict) and "name" in item:
            weight = item.get("weight", 0.5)
            weight = max(0.1, min(1.0, float(weight)))
            normalized.append({"name": item["name"], "weight": weight})

    mongo.db.user_tags.update_one(
        {"_id": "user_tags"},
        {
            "$set": {
                "selected_tags": normalized,
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
            "$pull": {
                "custom_tags": tag,
                "selected_tags": {"name": tag},
            },
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


def get_feed(tags_with_weights: list[dict], limit: int = 20):
    """根据选中标签（带权重）从 trending_items 中模糊匹配推荐内容。
    tags_with_weights: [{"name": "人工智能", "weight": 0.8}, ...]
    排序公式：hot_score × max(matched_tag_weight)
    """
    if not tags_with_weights:
        return {"items": [], "hint": "请选择兴趣标签以获取个性化推荐"}

    # 兼容旧格式
    normalized = []
    for t in tags_with_weights:
        if isinstance(t, str):
            normalized.append({"name": t, "weight": 0.5})
        else:
            normalized.append(t)

    tag_names = [t["name"] for t in normalized]
    # 构建 tag_name → weight 映射
    tag_weight_map = {t["name"]: t.get("weight", 0.5) for t in normalized}

    # 构建 keyword → weight 映射（同义词继承父标签权重）
    keyword_weight_map = {}
    all_keywords = []
    for tag_name in tag_names:
        weight = tag_weight_map.get(tag_name, 0.5)
        synonyms = TAG_SYNONYMS.get(tag_name)
        if synonyms:
            for s in synonyms:
                all_keywords.append(s)
                # 取最大权重（一个关键词可能属于多个标签）
                keyword_weight_map[s] = max(keyword_weight_map.get(s, 0), weight)
        else:
            all_keywords.append(tag_name)
            keyword_weight_map[tag_name] = max(keyword_weight_map.get(tag_name, 0), weight)

    keywords = list(dict.fromkeys(all_keywords))  # 去重保序
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    regex_pattern = "|".join(re.escape(kw) for kw in keywords)

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
        .limit(limit * 3)  # 多取一些，排序后再截断
    )

    if not matches:
        return {"items": [], "hint": "当前热榜中暂无匹配内容，试试其他标签"}

    results = []
    for item in matches:
        source_key = item.get("source", "")
        matched_kws = _find_matched_keywords(item, keywords)

        # 计算该条目匹配到的最大权重
        max_weight = 0.1
        for kw in matched_kws:
            w = keyword_weight_map.get(kw, 0.1)
            if w > max_weight:
                max_weight = w

        hot_score = item.get("hot_score", 0) or 0
        weighted_score = hot_score * max_weight

        results.append({
            "title": item["title"],
            "url": item["url"],
            "source": source_key,
            "source_label": _SOURCE_LABELS.get(source_key, source_key),
            "hot_score": hot_score,
            "weighted_score": round(weighted_score, 2),
            "tags": item.get("tags", []),
            "matched_keywords": matched_kws,
        })

    # 按加权分数降序排列
    results.sort(key=lambda x: x["weighted_score"], reverse=True)
    results = results[:limit]

    hint = ""
    if len(results) < 3:
        hint = "匹配结果较少，试试选择更多标签"

    return {"items": results, "hint": hint}
