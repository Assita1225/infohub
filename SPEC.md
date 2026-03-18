# SPEC.md — 面向个人信息聚合与智能分析的终端系统

> **第一性原则**：用户的核心矛盾是「信息过载 × 注意力有限」。  
> 系统存在的唯一理由 = 让用户用最少的时间，获取最高密度的有价值信息，并沉淀为可复用的知识。  
> 一切功能设计必须服务于这个等式，否则砍掉。

---

## 0. 项目元信息

| 项目 | 值 |
|---|---|
| 项目名称 | InfoHub — 个人信息聚合与智能分析终端 |
| 作者 | 岑佳雯 (2220541) |
| 指导教师 | 董辛酉 |
| 技术栈 | Vue 3 + Flask + MongoDB + Celery + Redis + LLM API |
| 开发模式 | 前后端分离 B/S 架构，模块化单体应用 |
| 部署目标 | 轻量云服务器（单机部署） |
| 用户模式 | **单用户个人应用**（无多用户注册体系） |

---

## 1. 系统架构总览

### 1.1 三层架构

```
┌─────────────────────────────────────────────────────┐
│                  用户交互层 (Frontend)                │
│  Vue 3 + Vue Router + Pinia + Element Plus + ECharts │
│  每个页面 = 一个独立 Vue 模块，按路由懒加载           │
└──────────────────────┬──────────────────────────────┘
                       │ RESTful API (JSON)
                       │ + WebSocket (AI 流式响应)
┌──────────────────────▼──────────────────────────────┐
│                  业务逻辑层 (Backend)                 │
│  Flask + Flask-CORS + Flask-SocketIO                 │
│  每个模块 = 一个 Blueprint，独立路由前缀              │
│  Celery + Redis = 异步任务队列                       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  数据支撑层 (Data)                    │
│  MongoDB (主存储) + Redis (缓存/消息队列/会话)        │
└─────────────────────────────────────────────────────┘
```

### 1.2 模块化原则

**核心规则：每个业务模块可独立启动、独立测试、独立迭代。**

实现方式：
- **后端**：每个模块是一个 Flask Blueprint，有自己的 `routes.py`、`services.py`、`models.py`，通过 `register_blueprint()` 挂载到主 app
- **前端**：每个模块是 `src/modules/<模块名>/` 目录，包含自己的 `views/`、`components/`、`api/`、`store/`，通过 Vue Router 懒加载
- **数据**：每个模块有自己的 MongoDB Collection，模块间通过 ID 引用而非嵌套
- **独立运行**：任何模块的后端 Blueprint 可单独注册到一个最小 Flask app 中运行和调试

### 1.3 目录结构

```
infohub/
├── README.md
├── SPEC.md                          # 本文件
├── .env.example                     # 环境变量模板
├── docker-compose.yml               # 本地开发环境（MongoDB + Redis）
│
├── backend/
│   ├── app/
│   │   ├── __init__.py              # create_app() 工厂函数
│   │   ├── config.py                # 配置类（dev/test/prod）
│   │   ├── extensions.py            # db, celery, socketio 等扩展初始化
│   │   │
│   │   ├── common/                  # 跨模块共享
│   │   │   ├── auth.py              # 密码锁认证装饰器
│   │   │   ├── errors.py            # 统一异常处理
│   │   │   ├── response.py          # 统一响应格式
│   │   │   ├── validators.py        # 输入校验工具
│   │   │   └── llm_client.py        # LLM API 封装（统一入口）
│   │   │
│   │   ├── auth/                    # [模块] 密码锁认证（极简）
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── services.py
│   │   │
│   │   ├── dashboard/               # [模块] 个人主页
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── services.py
│   │   │   └── models.py
│   │   │
│   │   ├── rss/                     # [模块] RSS 订阅
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── services.py
│   │   │   ├── models.py
│   │   │   └── tasks.py             # Celery 异步任务
│   │   │
│   │   ├── news/                    # [模块] 新闻广场
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── services.py
│   │   │   ├── models.py
│   │   │   ├── tasks.py
│   │   │   └── adapters/            # 新闻API适配器
│   │   │       ├── base.py
│   │   │       ├── google_news.py
│   │   │       ├── newsapi.py
│   │   │       └── ...
│   │   │
│   │   ├── trending/                # [模块] 热度榜 + 个性化推荐
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── services.py
│   │   │   ├── models.py
│   │   │   ├── tasks.py
│   │   │   └── adapters/            # 热榜来源适配器
│   │   │       ├── base.py
│   │   │       ├── weibo.py
│   │   │       ├── zhihu.py
│   │   │       └── ...
│   │   │
│   │   ├── recommend/               # [模块] 个性化推荐（后端独立 Blueprint）
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── services.py
│   │   │   └── models.py
│   │   │
│   │   ├── notes/                   # [模块] 笔记系统
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── services.py
│   │   │   └── models.py
│   │   │
│   │   └── chat/                    # [模块] 全局 AI 对话
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       ├── services.py
│   │       └── models.py
│   │
│   ├── celery_worker.py             # Celery 启动入口
│   ├── wsgi.py                      # Flask 启动入口
│   ├── requirements.txt
│   └── tests/                       # 按模块组织测试
│       ├── conftest.py
│       ├── test_auth/
│       ├── test_rss/
│       └── ...
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.js             # 路由总表（懒加载各模块）
│   │   ├── stores/                  # Pinia 全局 store
│   │   │   ├── auth.js              # 认证状态
│   │   │   └── chat.js              # 全局 AI 对话状态
│   │   │
│   │   ├── common/                  # 共享组件和工具
│   │   │   ├── components/          # 通用 UI 组件
│   │   │   ├── composables/         # 通用组合式函数
│   │   │   ├── api/                 # axios 实例 + 拦截器
│   │   │   └── utils/
│   │   │
│   │   ├── modules/
│   │   │   ├── auth/                # 密码锁屏页
│   │   │   ├── dashboard/
│   │   │   │   ├── views/
│   │   │   │   ├── components/
│   │   │   │   ├── api/
│   │   │   │   └── store/
│   │   │   ├── rss/
│   │   │   ├── news/
│   │   │   ├── trending/            # 热度榜 + 个性化推荐（同页面）
│   │   │   ├── notes/
│   │   │   └── chat/                # 全局悬浮组件
│   │   │
│   │   └── layouts/
│   │       └── MainLayout.vue       # 侧边栏 + 顶栏 + AI 对话浮窗
│   │
│   └── public/
│
└── scripts/
    ├── seed_data.py                 # 初始化测试数据
    └── backup.sh                    # 数据库备份脚本
```

---

## 2. 模块详细设计

> 以下每个模块定义：职责边界、页面路由、API 端点、数据模型、关键逻辑。
> 模块间依赖关系在末尾汇总。

---

### 2.0 Auth — 密码锁认证模块（极简单用户模式）

> **设计思路**：这是一个面向个人的应用，不需要多用户注册体系。  
> 但系统部署在云服务器上，没有任何认证 = 任何人知道 URL 就能看到所有数据。  
> 因此采用**最轻量的方案：密码锁**。
>
> 对用户来说：首次打开设置一个密码，之后每次打开输入密码即可。  
> 对开发来说：只有 4 个接口，半天就能做完，但安全性质变。

**用户体验流程**

```
首次访问 → 检测到未设置密码 → 跳转设置密码页 → 设置完成自动登录
再次访问 → 密码锁屏页 → 输入密码 → 进入系统
密码正确后签发 JWT → 后续请求自动带 token → 过期后重新输入密码
```

**页面路由**

| 路径 | 页面 | 说明 |
|---|---|---|
| `/lock` | 密码锁屏页 | 输入密码解锁 |
| `/setup` | 首次设置页 | 仅首次使用时出现，设置密码 |

**API 端点**

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/api/auth/status` | 检查是否已设置密码 | 否 |
| POST | `/api/auth/setup` | 首次设置密码 | 否（仅允许调用一次） |
| POST | `/api/auth/unlock` | 验证密码，返回 JWT | 否 |
| POST | `/api/auth/change-password` | 修改密码 | 是 |

**数据模型：`app_config` Collection**

```javascript
// 只有一条记录，存储全局应用配置
{
  _id: "app_config",
  password_hash: String,       // bcrypt 哈希
  created_at: DateTime,
  settings: {                  // 用户全局偏好
    theme: "light" | "dark",
    language: "zh-CN",
    dashboard_layout: Object,  // 个人主页微件布局
    weather_city: String       // 天气微件城市
  }
}
```

**安全要点**
- 密码使用 `bcrypt` 哈希（cost factor ≥ 12），绝不存明文
- JWT 过期时间设为 24h（个人设备可以长一些）
- 连续输错密码 5 次 → 锁定 5 分钟（Flask-Limiter）
- `/api/auth/setup` 检查密码是否已存在，已存在则拒绝（防止被外人重设）

**为什么不能省掉**：
你的系统存了 RSS 订阅、阅读偏好、个人笔记、AI 对话记录——这些都是隐私数据。
部署在公网云服务器上，不加密码锁 = 裸奔。
这个模块总共只有 4 个 API + 一个锁屏页面，开发量约半天，但安全价值极高。

---

### 2.1 Dashboard — 个人主页模块

> **职责**：用户的信息总览面板 + 快捷入口。  
> **第一性**：这是用户打开系统后的第一个页面，必须在 3 秒内让用户掌握全局。

**页面路由**

| 路径 | 页面 |
|---|---|
| `/` 或 `/dashboard` | 个人主页（可拖拽微件画布） |

**API 端点**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/dashboard/widgets` | 获取用户的微件配置列表 |
| PUT | `/api/dashboard/widgets` | 保存微件布局（位置、大小、开关） |
| GET | `/api/dashboard/summary` | 聚合数据：未读数、最新笔记数、今日热点概要 |

**微件清单**

| 微件 | 数据来源 | 说明 |
|---|---|---|
| 天气 | 第三方天气 API（和风天气/OpenWeather） | 根据 settings.weather_city |
| 时钟 | 前端本地 | 支持多时区 |
| 日历 | 前端本地 | 显示当月，可标记待办 |
| 待办事项 | `todos` Collection | 简单 CRUD |
| 未读统计 | RSS/News 模块 API | 显示未读文章数 |
| 最近笔记 | Notes 模块 API | 最近 5 条笔记标题 |
| 快捷入口 | 前端配置 | 一键跳转各模块 |

**前端实现要点**
- 拖拽：使用 `vue-grid-layout`（比 vue-draggable 更适合网格画布场景）
- 布局持久化：保存到后端 `app_config.settings.dashboard_layout`
- 微件懒加载：每个微件是独立异步组件，互不阻塞

---

### 2.2 RSS — RSS 订阅模块

> **职责**：管理用户的 RSS 订阅源，手动/按需采集 + 按需 AI 摘要 + 阅读消费。  
> **第一性**：这是系统最核心的数据管道——没有数据输入，后续所有模块都无意义。
>
> **核心交互模型**：
> - 每个订阅源 = 一张卡片，卡片内展示该源最新的 N 条文章标题
> - 用户点击卡片上的"刷新"按钮 → 触发该源的实时抓取 → 更新卡片内容
> - 用户点击某篇文章 → 进入详情 → **此时才按需生成 AI 摘要**（省 token）
> - 不点不抓、不读不摘，一切按需触发

**页面路由**

| 路径 | 页面 |
|---|---|
| `/rss` | RSS 主页：分组标签页 + 订阅源卡片网格 |
| `/rss/manage` | 订阅源管理（增删改查、分组） |
| `/rss/article/<id>` | 文章详情页（正文 + AI 摘要 + 一键对话） |

**API 端点**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/rss/feeds` | 获取所有订阅源（支持 ?group= 过滤） |
| POST | `/api/rss/feeds` | 添加订阅源（URL + 名称 + 分组） |
| PUT | `/api/rss/feeds/<id>` | 编辑订阅源（名称、分组、启用/禁用） |
| DELETE | `/api/rss/feeds/<id>` | 删除订阅源 |
| POST | `/api/rss/feeds/<id>/refresh` | **手动刷新**：立即抓取该源最新 N 条 |
| POST | `/api/rss/feeds/refresh-all` | 一键刷新所有源 |
| GET | `/api/rss/feeds/<id>/articles` | 获取某个源的文章列表（分页） |
| GET | `/api/rss/articles/<id>` | 文章详情（正文 + 摘要） |
| POST | `/api/rss/articles/<id>/summarize` | **按需生成 AI 摘要**（仅首次调用时生成） |
| POST | `/api/rss/articles/<id>/read` | 标记已读 |
| POST | `/api/rss/articles/<id>/favorite` | 收藏/取消收藏 |
| GET | `/api/rss/stats` | 热度雷达数据（各分组文章数/更新频率） |

**数据模型**

```javascript
// Collection: rss_feeds
{
  _id: ObjectId,
  title: String,               // 订阅源名称
  url: String,                 // RSS/Atom feed URL
  site_url: String,            // 源网站主页
  group: String,               // 分组名称（默认"未分组"）
  is_active: Boolean,          // 启用/禁用
  display_count: Number,       // 卡片展示文章数（默认 5）
  last_fetched_at: DateTime,   // 上次抓取时间
  error_count: Number,         // 连续失败次数
  last_error: String,          // 最后一次错误信息
  created_at: DateTime
}

// Collection: articles
{
  _id: ObjectId,
  feed_id: ObjectId,           // 关联订阅源
  source_type: "rss" | "news", // 来源类型（RSS 和新闻模块共用此 Collection）
  title: String,
  url: String,                 // 原文链接（唯一索引，用于去重）
  author: String,
  content: String,             // 正文（Goose3 提取）
  summary: String,             // AI 生成摘要（默认 null，按需生成）
  summary_status: "none" | "pending" | "done" | "failed",
  tags: [String],              // 自动提取的关键词标签（Jieba + TF-IDF）
  simhash: String,             // SimHash 指纹（用于去重）
  is_read: Boolean,
  is_favorited: Boolean,
  published_at: DateTime,      // 原文发布时间
  fetched_at: DateTime,        // 系统采集时间
  created_at: DateTime
}

// 索引设计（性能关键）
// articles: { feed_id: 1, published_at: -1 }  （按源查最新文章）
// articles: { source_type: 1, is_read: 1, published_at: -1 }
// articles: { url: 1 } (唯一，去重)
// articles: { simhash: 1 }
// articles: { tags: 1 }
```

**抓取流程（手动触发）**

```
用户点击"刷新" → POST /api/rss/feeds/<id>/refresh
  → 后端启动 Celery 任务（异步，前端显示加载状态）
  → feedparser 解析 RSS feed
  → 取最新 N 条（N = feed.display_count）
  → 对每条：Goose3 提取正文 → SimHash 去重 → 存入 articles
  → 同时为每条文章提取关键词标签（Jieba + TF-IDF，本地运算不花钱）
  → 任务完成 → 前端轮询或 WebSocket 通知 → 更新卡片
```

**AI 摘要流程（按需触发，省 token）**

```
用户打开文章详情 → 检查 summary_status
  → 如果是 "done"：直接展示缓存的摘要
  → 如果是 "none"：
      → 前端显示"生成摘要"按钮（用户主动点击）
      → POST /api/rss/articles/<id>/summarize
      → 后端调用 LLM 生成摘要 → 存入 articles.summary
      → 返回摘要内容
  → 如果是 "failed"：显示"重试"按钮
```

**为什么这样设计更好**：
- **省 token**：只有用户真正想读的文章才生成摘要，而非抓取时全部生成
- **省时间**：刷新操作只做抓取 + 去重 + 标签提取（全是本地运算），几秒完成
- **用户可控**：用户决定什么时候刷新、什么文章值得生成摘要
- **标签提取仍然自动做**：因为 Jieba + TF-IDF 是纯本地运算，不花钱，且标签是推荐模块的数据基础

**健壮性设计**
- 抓取失败自动重试（最多 3 次，指数退避）
- 连续失败 5 次 → 卡片上显示警告标记 + 错误原因，不自动禁用（用户手动决定）
- 摘要生成失败不影响文章阅读（降级为无摘要模式）
- 前端卡片显示"上次刷新时间"，让用户知道数据新鲜度

---

### 2.3 News — 新闻广场模块

> **职责**：系统预设的新闻源浏览，侧重 API 聚合（区别于 RSS 的订阅模式）。  
> **与 RSS 模块的区分**：
> - RSS = 用户自己添加的专业/垂直信息源，以"订阅源"为单位管理
> - 新闻 = 系统预设的大众新闻聚合，以"分类"为单位浏览，来源更广泛（新闻 API + 聚合平台）
>
> **数据来源策略**（优先使用 API，与 RSS 形成差异）：
> - **新闻聚合 API**：NewsAPI.org（免费版 100次/天）、GNews API、CurrentsAPI
> - **Google News RSS**：`https://news.google.com/rss/search?q=关键词&hl=zh-CN` — 免费、无需 API Key、返回标准 RSS 格式但内容来自 Google 新闻聚合
> - **平台开放 API**：少数派 API、36氪 API（如有）
> - **兜底方案**：部分源用 RSS 格式接入（feedparser 可统一处理）

**页面路由**

| 路径 | 页面 |
|---|---|
| `/news` | 新闻主页：顶部分类标签栏 + 文章卡片流 |
| `/news/read-later` | 稍后读列表 |
| `/news/article/<id>` | 新闻详情页 |

**页面布局**

```
┌─────────────────────────────────────────────┐
│  科技 | 财经 | 国际 | 社会 | 娱乐 | 体育     │  ← 分类标签栏（可横向滚动）
├─────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  │ 文章卡片 │  │ 文章卡片 │  │ 文章卡片 │     │  ← 当前分类下的文章
│  │ 标题     │  │ 标题     │  │ 标题     │     │
│  │ 来源+时间│  │ 来源+时间│  │ 来源+时间│     │
│  │ AI摘要.. │  │ AI摘要.. │  │ AI摘要.. │     │
│  └─────────┘  └─────────┘  └─────────┘     │
│  ...加载更多...                              │
└─────────────────────────────────────────────┘
```

**API 端点**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/news/categories` | 获取分类列表 |
| GET | `/api/news/articles` | 按分类获取新闻（?category=tech&page=1） |
| GET | `/api/news/articles/<id>` | 新闻详情 |
| POST | `/api/news/articles/<id>/summarize` | 按需 AI 摘要（同 RSS 的按需策略） |
| POST | `/api/news/articles/<id>/read-later` | 添加到稍后读 |
| DELETE | `/api/news/articles/<id>/read-later` | 移出稍后读 |
| POST | `/api/news/articles/<id>/to-note` | 转为笔记初始内容 |

**数据模型**

```javascript
// Collection: news_sources（系统预设，在 seed_data.py 中初始化）
{
  _id: ObjectId,
  name: String,                // 源名称，如"Google News 科技"、"NewsAPI 国际"
  url: String,                 // API endpoint 或 RSS URL
  category: String,            // 分类：tech, finance, world, society, entertainment, sports
  adapter_type: "newsapi" | "gnews" | "google_rss" | "rss",
  is_active: Boolean,
  fetch_config: {              // 适配器专属配置
    api_key_env: String,       // 环境变量名（如 "NEWSAPI_KEY"），非明文
    query: String,             // 搜索关键词（Google News RSS 用）
    language: "zh",
    country: "cn",
    page_size: 20
  },
  last_fetched_at: DateTime
}

// 文章复用 articles Collection，source_type = "news"
// 额外字段：
{
  source_type: "news",
  news_source_id: ObjectId,    // 关联 news_sources
  category: String,            // 冗余分类（加速按分类查询）
  is_read_later: Boolean       // 稍后读标记
}
```

**新闻源适配器架构**

```python
# backend/app/news/adapters/base.py
class NewsAdapter(ABC):
    @abstractmethod
    def fetch(self, config: dict) -> list[dict]:
        """返回标准化的新闻条目列表"""
        pass

# 每个来源一个适配器
# adapters/newsapi.py     → NewsAPI.org
# adapters/gnews.py       → GNews API  
# adapters/google_rss.py  → Google News RSS（用 feedparser 解析）
# adapters/rss.py         → 通用 RSS（兜底）
```

**Google News RSS 说明**：
Google News 提供标准 RSS feed，可以按主题或搜索词获取：
- 按搜索：`https://news.google.com/rss/search?q=人工智能&hl=zh-CN&gl=CN&ceid=CN:zh-Hans`
- 可用 feedparser 直接解析，无需 API Key
- 聚合了多家媒体来源，内容丰富

**定时抓取策略**
- 新闻源由 Celery Beat 定时抓取（每 2-4 小时一次），因为新闻具有时效性
- 这与 RSS 模块的"手动刷新"策略不同：新闻强调"打开就有内容"
- AI 摘要仍然按需生成（用户点击文章时才触发）

---

### 2.4 Trending — 热度榜模块

> **职责**：打破信息茧房，提供跨平台宏观趋势视图。  
> **第一性**：用户来这里的目的 = 5 分钟了解"今天世界上正在发生什么"。
>
> **数据来源**：抓取各大网站的热搜/热榜/Trending 页面。
> 这类数据通常是公开的排行榜页面，可通过 RSS、API 或轻量级爬虫获取。

**可选热榜来源**（开发时按优先级逐个接入，不必一次全做）

| 来源 | 获取方式 | 难度 | 说明 |
|---|---|---|---|
| 微博热搜 | 第三方 API / 爬虫 | 中 | 国内最大社交热点 |
| 知乎热榜 | 第三方 API / 爬虫 | 中 | 问答类热点 |
| 百度热搜 | 爬虫 / RSS | 低 | 搜索趋势 |
| GitHub Trending | 官方页面爬虫 | 低 | 技术趋势 |
| 今日头条热榜 | API / 爬虫 | 中 | 综合新闻热点 |
| 抖音热搜 | 第三方 API | 中 | 短视频热点 |
| 36氪热榜 | RSS / 爬虫 | 低 | 科技创投 |
| 少数派热门 | RSS | 低 | 数码科技 |

> **实用建议**：先做 2-3 个容易的（如百度热搜、GitHub Trending、36氪），  
> 跑通整个流程后再逐步添加更多来源。  
> 每个来源是一个独立适配器文件，新增来源不影响已有代码。

**页面路由**

| 路径 | 页面 |
|---|---|
| `/trending` | 热度榜 + 个性化推荐（同一页面，推荐部分详见 2.5） |

**页面布局**

```
┌─────────────────────────────────────────────────────────────┐
│                        热度榜 + 发现                         │
├──────────────────────────────┬──────────────────────────────┤
│                              │                              │
│     热榜主区域（左侧/上方）    │   个性化推荐卡片（右侧/下方） │
│                              │   （详见 2.5 节）             │
│  ┌──────────────────────┐   │                              │
│  │ 微博热搜    百度热搜  │   │                              │
│  │ GitHub     36氪     │   │                              │
│  │ （来源标签页切换）     │   │                              │
│  ├──────────────────────┤   │                              │
│  │ 1. 热搜话题A  🔥9999 │   │                              │
│  │ 2. 热搜话题B  🔥8888 │   │                              │
│  │ 3. 热搜话题C  🔥7777 │   │                              │
│  │ ...                  │   │                              │
│  └──────────────────────┘   │                              │
│                              │                              │
│  词云可视化区域              │                              │
│  ┌──────────────────────┐   │                              │
│  │    词云（ECharts）     │   │                              │
│  └──────────────────────┘   │                              │
│                              │                              │
└──────────────────────────────┴──────────────────────────────┘
```

**API 端点**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/trending/sources` | 获取支持的热榜来源列表 |
| GET | `/api/trending/list` | 获取热榜数据（?source=weibo,zhihu,github） |
| GET | `/api/trending/wordcloud` | 词云数据（聚合所有热榜的关键词频率） |
| POST | `/api/trending/refresh` | 手动刷新热榜数据 |

**数据模型**

```javascript
// Collection: trending_items
{
  _id: ObjectId,
  source: String,              // "weibo" | "zhihu" | "github" | "baidu" ...
  title: String,
  url: String,
  hot_score: Number,           // 热度值（标准化到 0-100）
  rank: Number,                // 排名
  tags: [String],              // 从标题提取的关键词（用于推荐模块匹配）
  fetched_at: DateTime,        // 抓取时间
  expires_at: DateTime         // TTL 过期（24h 后自动删除）
}

// 索引
// { source: 1, fetched_at: -1 }
// { expires_at: 1 }, expireAfterSeconds: 0  （MongoDB TTL 索引，自动清理过期数据）
// { tags: 1 }  （用于推荐模块查询）
```

**多源适配器架构**
```python
# backend/app/trending/adapters/base.py
class TrendingAdapter(ABC):
    @abstractmethod
    def fetch(self) -> list[dict]:
        """返回标准化的热榜条目列表"""
        # 每条包含：title, url, hot_score, rank
        pass

# 每个来源一个适配器文件，新增来源只需：
# 1. 新建 adapters/xxx.py，实现 TrendingAdapter
# 2. 在配置中注册
# 不影响已有代码
```

**健壮性设计**
- 某个源抓取失败不影响其他源展示
- Redis 缓存热榜数据（TTL=15min），避免频繁请求
- 前端展示"最后更新时间"，用户可手动刷新
- Celery Beat 定时抓取（每 30 分钟），也支持用户手动触发

---

### 2.5 Recommend — 个性化推荐卡片（内嵌于热度榜页面）

> **职责**：基于用户手动选择的兴趣标签，从热榜和文章中筛选匹配内容。  
> **不是独立页面**，而是热度榜页面右侧/下方的一个卡片组件。
>
> **核心交互**：
> 用户在卡片内看到预设标签 → 点击选中/取消 → 推荐内容实时变化。
> 没有自动画像更新，一切由用户手动控制。
>
> **数据源**：从 `trending_items` 和 `articles` 中匹配标签。

**UI 交互设计**

```
┌────────────────────────────────┐
│  🎯 我的兴趣                    │
│                                │
│  预设标签区：                    │
│  [人工智能✓] [区块链] [前端✓]   │
│  [金融] [创业✓] [游戏] [设计]   │
│  [科学] [教育] [健康] [体育]    │
│                                │
│  + 自定义标签：[________] [添加] │
│                                │
├────────────────────────────────┤
│  为你筛选：                      │
│                                │
│  📰 OpenAI发布新模型...   (微博) │
│  📰 Vue 4.0 发布计划...  (GitHub)│
│  📰 AI创业公司融资盘点... (36氪) │
│  📰 ...                        │
│                                │
│  暂无更多匹配内容               │
└────────────────────────────────┘
```

**交互流程**

```
1. 页面加载 → 从后端获取用户已选标签 + 预设标签列表
2. 用户点击标签 → 选中变高亮 / 再点取消
3. 标签变化 → 前端带着选中标签列表请求后端
4. 后端从 trending_items + articles 中匹配 tags 字段
5. 返回匹配的条目 → 前端刷新"为你筛选"区域
6. 用户可输入自定义标签添加到列表中
```

**API 端点**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/recommend/tags` | 获取预设标签列表 + 用户已选标签 |
| PUT | `/api/recommend/tags` | 更新用户选中的标签 |
| POST | `/api/recommend/tags/custom` | 添加自定义标签 |
| DELETE | `/api/recommend/tags/<tag>` | 删除自定义标签 |
| GET | `/api/recommend/feed` | 获取推荐内容（?tags=AI,前端,创业） |

**数据模型**

```javascript
// Collection: user_tags
{
  _id: "user_tags",            // 单用户，固定 ID
  preset_tags: [               // 系统预设标签（seed_data.py 初始化）
    "人工智能", "区块链", "前端开发", "后端开发",
    "金融", "创业", "游戏", "设计", "科学",
    "教育", "健康", "体育", "数码", "汽车"
  ],
  custom_tags: [String],       // 用户自定义添加的标签
  selected_tags: [String],     // 当前选中的标签（preset + custom 中的子集）
  updated_at: DateTime
}
```

**推荐匹配逻辑**

```python
def get_recommendations(selected_tags: list[str], limit=20):
    """从热榜和文章中匹配用户选中的标签"""
    
    # 1. 从 trending_items 中匹配
    trending_matches = db.trending_items.find({
        "tags": {"$in": selected_tags},
        "fetched_at": {"$gte": 最近24小时}
    }).sort("hot_score", -1).limit(limit // 2)
    
    # 2. 从 articles 中匹配（RSS + 新闻的文章）
    article_matches = db.articles.find({
        "tags": {"$in": selected_tags},
        "created_at": {"$gte": 最近7天}
    }).sort("published_at", -1).limit(limit // 2)
    
    # 3. 合并、去重、排序返回
    return merge_and_rank(trending_matches, article_matches)
```

---

### 2.6 Notes — 笔记闭环模块

> **职责**：将阅读中的灵感和内容沉淀为结构化知识。  
> **第一性**：信息消费如果没有输出，就是在浪费时间。笔记是将"看过"变成"知道"的关键环节。

**页面路由**

| 路径 | 页面 |
|---|---|
| `/notes` | 笔记列表（搜索、分类、排序） |
| `/notes/<id>` | 笔记编辑器 |
| `/notes/new` | 新建笔记 |

**API 端点**

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/notes` | 笔记列表（分页、搜索、排序） |
| POST | `/api/notes` | 创建笔记 |
| GET | `/api/notes/<id>` | 获取笔记详情 |
| PUT | `/api/notes/<id>` | 更新笔记 |
| DELETE | `/api/notes/<id>` | 删除笔记（软删除） |
| POST | `/api/notes/<id>/restore` | 恢复已删除笔记 |
| GET | `/api/notes/search` | 全文搜索（MongoDB text index） |
| GET | `/api/notes/trash` | 查看回收站 |

**数据模型**

```javascript
// Collection: notes
{
  _id: ObjectId,
  title: String,
  content: String,             // Markdown 格式
  source: {                    // 笔记来源（可选）
    type: "rss" | "news" | "manual",
    article_id: ObjectId,      // 关联原文
    article_url: String,       // 原文 URL
    selected_text: String      // 选中的文本片段
  },
  tags: [String],              // 用户标签
  is_deleted: Boolean,         // 软删除
  deleted_at: DateTime,        // 删除时间（30天后真正清理）
  created_at: DateTime,
  updated_at: DateTime
}

// 索引
// { is_deleted: 1, updated_at: -1 }
// { tags: 1 }
// { "$**": "text" }  （全文搜索索引，覆盖 title + content）
```

**右键 → 分屏创建笔记流程**

```
前端：用户在文章页选中文本 → 右键菜单"创建笔记"
  → 将 { selected_text, article_id, article_url } 传入笔记编辑器
  → 以分屏（右侧面板）形式打开编辑器
  → 自动填入引用内容作为初始文本
  → 用户编辑 → 保存入库
```

**前端实现**
- Markdown 编辑器：使用 `md-editor-v3`（Vue 3 专用，支持预览、工具栏、快捷键）
- 分屏：使用 `splitpanes` 库实现左右分屏

---

### 2.7 Chat — 全局 AI 对话模块

> **职责**：随时可用的智能研究助手，"哪里不懂问哪里"。  
> **设计核心**：它是一个全局浮窗组件，不是独立页面。跟随用户在每个页面的上下文。

**UI 形态**
- 固定在页面右下角的浮动按钮 → 点击展开对话面板
- 对话面板可拖拽、可调整大小
- 每个页面的对话上下文独立（但可选择"继续上次对话"）

**API 端点**

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/chat/message` | 发送消息（返回 AI 响应，支持流式） |
| GET | `/api/chat/sessions` | 获取会话列表 |
| GET | `/api/chat/sessions/<id>` | 获取会话历史 |
| DELETE | `/api/chat/sessions/<id>` | 删除会话 |

**数据模型**

```javascript
// Collection: chat_sessions
{
  _id: ObjectId,
  title: String,               // 自动生成（第一条消息的摘要）
  context: {                   // 会话绑定的上下文
    page: String,              // "rss" | "news" | "trending" | "general"
    article_id: ObjectId,      // 当前正在阅读的文章（可选）
    article_title: String,
    article_content: String    // 用于构建 prompt（截断到合理长度）
  },
  messages: [
    {
      role: "user" | "assistant",
      content: String,
      timestamp: DateTime
    }
  ],
  created_at: DateTime,
  updated_at: DateTime
}
```

**Prompt 工程策略**

```python
def build_prompt(session, user_message):
    system_prompt = "你是一个信息分析助手，帮助用户理解和分析文章内容。请用中文回复。"
    
    # 注入上下文
    if session.get("context") and session["context"].get("article_content"):
        system_prompt += f"\n\n用户正在阅读的文章：\n{session['context']['article_content'][:3000]}"
    
    # 注入历史（最近 10 轮）
    history = session["messages"][-20:]  # 最近 10 轮 = 20 条消息
    
    return {
        "system": system_prompt,
        "messages": history + [{"role": "user", "content": user_message}]
    }
```

**流式响应**
- 使用 Flask-SocketIO（WebSocket）或 SSE（Server-Sent Events）实现流式输出
- 前端逐字渲染，提升响应感知速度
- 超时处理：30 秒无响应则显示错误提示，支持重试

**预设问题建议**
- 根据当前页面类型动态生成：
  - RSS/新闻详情页："总结这篇文章"、"这篇文章的核心观点是什么"、"有哪些值得关注的信息"
  - 热度榜："今天最值得关注的趋势是什么"
  - 通用："帮我整理最近阅读的内容"

---

## 3. 跨模块共享设计

### 3.1 统一响应格式

所有 API 返回统一格式，前端只需一个拦截器处理：

```json
// 成功
{
  "code": 200,
  "data": { ... },
  "message": "success"
}

// 分页
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  },
  "message": "success"
}

// 失败
{
  "code": 400,
  "data": null,
  "message": "订阅源 URL 格式无效",
  "errors": {
    "url": "必须是合法的 HTTP/HTTPS URL"
  }
}
```

### 3.2 统一错误处理

```python
# backend/app/common/errors.py
class AppError(Exception):
    def __init__(self, message, code=400, errors=None):
        self.message = message
        self.code = code
        self.errors = errors

# 在 create_app() 中注册全局错误处理器
@app.errorhandler(AppError)
@app.errorhandler(404)
@app.errorhandler(500)
```

### 3.3 LLM 客户端封装

```python
# backend/app/common/llm_client.py
class LLMClient:
    """统一的 LLM 调用入口，所有模块通过此类调用 AI 服务。
    好处：
    1. 切换 LLM 提供商只改这一个文件（如从通义千问换到 DeepSeek）
    2. 统一 token 计费、限速、重试逻辑
    3. 统一 prompt 模板管理
    """
    
    def summarize(self, text: str, max_length: int = 200) -> str:
        """生成摘要"""
    
    def chat(self, messages: list, system_prompt: str = None, stream: bool = False):
        """对话（支持流式）"""
    
    def extract_tags(self, text: str, top_n: int = 5) -> list[str]:
        """提取关键词标签（备选方案：当 Jieba+TF-IDF 不够好时用 LLM 补充）"""
```

### 3.4 前端 Axios 拦截器

```javascript
// frontend/src/common/api/request.js
import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截：自动带上 JWT
request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截：
// - 统一处理 401（跳转锁屏页）
// - 统一处理 500（全局错误提示）
// - 统一提取 response.data
request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      router.push('/lock')
    }
    return Promise.reject(error)
  }
)
```

---

## 4. 安全性设计

| 类别 | 措施 |
|---|---|
| **认证** | 密码锁 + JWT + bcrypt 哈希 |
| **输入校验** | 后端对所有输入做 schema 校验（使用 `marshmallow` 或 `cerberus`） |
| **XSS 防护** | 文章正文 HTML 使用 `bleach` 库清洗，只保留安全标签 |
| **注入防护** | MongoDB 使用 PyMongo 参数化查询，不拼接字符串 |
| **限速** | `Flask-Limiter`：锁屏密码接口 5次/分钟，其他 API 60次/分钟 |
| **CORS** | `Flask-CORS` 仅允许前端域名的跨域请求 |
| **敏感信息** | API Key、数据库密码等全部通过 `.env` 环境变量加载，`.gitignore` 排除 `.env` |
| **数据备份** | 定时 `mongodump` 脚本（cron job），保留最近 7 天备份 |

---

## 5. 开发路线图（渐进式）

> **原则：每个阶段结束时，系统是可运行、可演示的。**  
> 不追求一次做完，而是每阶段都有一个完整可用的子系统。

### Phase 0 — 项目骨架（预计 2-3 天）

**目标**：空项目能跑起来，前后端能通信。

- [ ] 初始化 Git 仓库
- [ ] 后端：Flask 工厂函数 + config + extensions
- [ ] 后端：统一响应格式 + 错误处理
- [ ] 前端：Vite + Vue 3 + Vue Router + Pinia + Element Plus
- [ ] 前端：MainLayout（侧边栏 + 顶栏 + 路由出口）
- [ ] 前端：Axios 实例 + 拦截器
- [ ] docker-compose.yml 配置 MongoDB + Redis
- [ ] 验证：前端访问后端 `/api/health` 返回 `{"status": "ok"}`

**交付物**：一个有侧边栏导航的空壳应用，点击菜单可切换空白页面。

---

### Phase 1 — 密码锁认证（预计 1 天）

**目标**：系统有基本的访问保护。

- [ ] 后端：Auth Blueprint（status / setup / unlock / change-password）
- [ ] 后端：`@login_required` 装饰器
- [ ] 前端：锁屏页 + 首次设置页
- [ ] 前端：路由守卫（未认证跳转锁屏）
- [ ] 前端：Pinia auth store
- [ ] 测试：首次设置密码 → 解锁 → 访问主页 → 刷新仍保持登录 → token 过期回到锁屏

**交付物**：有密码保护的空壳应用。

---

### Phase 2 — 个人主页（预计 3-4 天）

**目标**：可拖拽的微件画布，至少实现天气+时钟+待办。

- [ ] 后端：Dashboard Blueprint（微件配置 CRUD、待办 CRUD）
- [ ] 前端：`vue-grid-layout` 集成
- [ ] 前端：天气微件（调用第三方 API）
- [ ] 前端：时钟微件
- [ ] 前端：待办事项微件（增删改查 + 完成状态）
- [ ] 布局保存到后端
- [ ] 测试：拖拽布局 → 刷新 → 布局恢复

**交付物**：功能完整的个人主页，可拖拽，数据持久化。

---

### Phase 3 — RSS 订阅（预计 5-7 天）⭐ 核心模块

**目标**：完整的 RSS 订阅 + 手动刷新 + 按需 AI 摘要。

**Phase 3a — 基础框架 + 数据采集（3-4 天）**
- [ ] 后端：RSS Blueprint（订阅源 CRUD + 文章 CRUD）
- [ ] 后端：`feedparser` 解析 + `goose3` 正文提取
- [ ] 后端：SimHash 去重逻辑（使用 `simhash` 库）
- [ ] 后端：手动刷新 API → Celery 异步任务
- [ ] 后端：`jieba` + `scikit-learn` TF-IDF 关键词提取（本地运算）
- [ ] 前端：订阅源管理页（添加、分组、删除）
- [ ] 前端：RSS 主页 — 分组标签 + 订阅源卡片网格
- [ ] 前端：卡片展示最新 N 条文章 + 刷新按钮
- [ ] 测试：添加源 → 点击刷新 → 文章出现在卡片中

**Phase 3b — AI 增强 + 阅读体验（2-3 天）**
- [ ] 后端：`LLMClient` 封装
- [ ] 后端：按需摘要生成 API
- [ ] 前端：文章详情页（正文 + AI 摘要按钮 + 收藏）
- [ ] 前端：热度雷达图（ECharts）
- [ ] 测试：打开文章 → 点击生成摘要 → 摘要出现 → 再次打开直接展示缓存

**交付物**：完整可用的 RSS 阅读器，手动刷新 + 按需 AI 摘要。

---

### Phase 4 — 笔记系统（预计 3-4 天）

**目标**：从文章中创建笔记，完成阅读→沉淀闭环。

- [ ] 后端：Notes Blueprint（CRUD + 全文搜索 + 软删除 + 回收站）
- [ ] 前端：笔记列表页
- [ ] 前端：`md-editor-v3` Markdown 编辑器集成
- [ ] 前端：文章页右键菜单 → 创建笔记
- [ ] 前端：分屏编辑体验（`splitpanes` 库）
- [ ] 收藏文章 → 可转为笔记初始内容
- [ ] 测试：阅读文章 → 选中文本 → 创建笔记 → 保存 → 在笔记列表找到

**交付物**：文章页和笔记页联动，形成完整闭环。

---

### Phase 5 — 全局 AI 对话（预计 3-4 天）

**目标**：随时可唤起的 AI 助手，感知当前页面上下文。

- [ ] 后端：Chat Blueprint（会话管理 + LLM 调用）
- [ ] 后端：WebSocket（Flask-SocketIO）或 SSE 流式响应
- [ ] 前端：全局浮窗对话组件（`MainLayout.vue` 中挂载）
- [ ] 前端：上下文注入（当前正在阅读的文章）
- [ ] 前端：流式渲染（逐字显示）
- [ ] 前端：预设问题建议
- [ ] 测试：在文章页打开对话 → 问"总结这篇文章" → AI 能基于文章内容回答

**交付物**：全局可用的 AI 助手，能理解当前阅读的内容。

---

### Phase 6 — 新闻广场（预计 3-4 天）

**目标**：基于 API 的新闻聚合浏览。

- [ ] 后端：News Blueprint + 新闻适配器架构
- [ ] 后端：至少实现 2 个适配器（Google News RSS + 一个新闻 API）
- [ ] 后端：Celery Beat 定时抓取新闻
- [ ] 前端：分类标签栏 + 文章卡片流
- [ ] 前端：稍后读功能
- [ ] 前端：文章 → 转笔记联动
- [ ] 测试：切换分类 → 看到不同新闻 → 添加稍后读 → 转为笔记

**交付物**：分类浏览的新闻广场，与 RSS 形成互补。

---

### Phase 7 — 热度榜 + 个性化推荐（预计 4-5 天）

**目标**：跨平台热榜 + 基于标签筛选的个性化推荐。

**Phase 7a — 热度榜（2-3 天）**
- [ ] 后端：Trending Blueprint + 适配器架构
- [ ] 后端：先实现 2-3 个简单适配器（百度热搜、GitHub Trending、36氪）
- [ ] 后端：Celery Beat 定时抓取 + Redis 缓存
- [ ] 前端：热榜主区域（来源切换 + 排行列表）
- [ ] 前端：词云可视化（`echarts-wordcloud` 插件）

**Phase 7b — 个性化推荐卡片（2 天）**
- [ ] 后端：Recommend Blueprint（标签管理 + 推荐匹配）
- [ ] 后端：预设标签初始化（seed_data.py）
- [ ] 前端：兴趣标签选择卡片（点击选中/取消）
- [ ] 前端：自定义标签输入框
- [ ] 前端：推荐内容实时刷新
- [ ] 测试：选中"人工智能" → 推荐区出现 AI 相关热榜/文章 → 取消 → 内容变化

**交付物**：热度榜仪表盘 + 可交互的个性化推荐。

---

### Phase 8 — 打磨与部署（预计 3-5 天）

- [ ] Dashboard 微件补全（未读统计、最近笔记等跨模块微件）
- [ ] UI 统一打磨（加载状态、空状态、错误状态的友好提示）
- [ ] 性能优化（前端路由懒加载、图片懒加载、后端 MongoDB 查询优化）
- [ ] Redis 缓存热数据（热榜、推荐结果）
- [ ] 错误日志（Python `logging` → 文件轮转）
- [ ] 云服务器部署（Nginx + Gunicorn + Supervisor + MongoDB + Redis）
- [ ] 数据库备份脚本（cron + mongodump）
- [ ] 完整功能测试

---

## 6. 模块依赖关系

```
Auth（独立）← 所有模块都依赖密码锁认证
   │
   ▼
Dashboard（仅依赖 Auth）
   │
   ▼
RSS（依赖 Auth）⭐ 核心数据管道
   │
   ├──▶ Notes（依赖 Auth + 文章数据）
   │
   ├──▶ Chat（依赖 Auth + 文章上下文）
   │
   ├──▶ News（依赖 Auth，与 RSS 共享 articles Collection）
   │      │
   │      ├──▶ Notes
   │      └──▶ Chat
   │
   └──▶ Trending + Recommend（同页面）
          │
          └──▶ 匹配 articles 和 trending_items 的 tags
```

**关键规则**：
- Auth 是唯一的硬依赖
- RSS 是数据源头：大多数模块从 articles Collection 取数据
- 每个模块的业务逻辑完全独立：关掉推荐不影响 RSS 和笔记
- Trending 和 Recommend 在同一页面但后端是各自独立的 Blueprint

---

## 7. 开发环境配置

### 7.1 环境变量 (.env)

```bash
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production

# MongoDB
MONGO_URI=mongodb://localhost:27017/infohub

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# LLM API（根据你选择的提供商配置）
LLM_API_KEY=your-api-key
LLM_API_BASE=https://api.example.com/v1
LLM_MODEL=your-model-name

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=86400       # 24 小时

# 天气 API
WEATHER_API_KEY=your-weather-api-key

# 新闻 API（可选，按需配置）
NEWSAPI_KEY=your-newsapi-key
```

### 7.2 核心依赖清单

**后端 (requirements.txt)**
```
# Web 框架
flask
flask-cors
flask-socketio
flask-limiter

# 数据库
pymongo
redis

# 异步任务
celery

# 认证
pyjwt
bcrypt

# 数据采集
feedparser          # RSS 解析
goose3              # 正文提取
requests            # HTTP 请求
beautifulsoup4      # HTML 解析
lxml                # XML/HTML 解析加速

# NLP + 数据分析
jieba               # 中文分词
scikit-learn        # TF-IDF
simhash             # 内容去重

# 数据校验
marshmallow         # 输入校验

# 安全
bleach              # HTML 清洗（防 XSS）

# 环境变量
python-dotenv

# 部署
gunicorn
```

**前端 (package.json 主要依赖)**
```
vue                 # 3.x
vue-router          # 路由
pinia               # 状态管理
element-plus        # UI 组件库
axios               # HTTP 请求
echarts             # 数据可视化
vue-echarts         # ECharts Vue 封装
echarts-wordcloud   # 词云插件
vue-grid-layout     # 可拖拽网格布局（Dashboard）
md-editor-v3        # Markdown 编辑器（Notes）
splitpanes          # 分屏面板
```

### 7.3 本地启动流程

```bash
# 1. 启动基础设施
docker-compose up -d  # MongoDB + Redis

# 2. 启动后端
cd backend
pip install -r requirements.txt
flask run --debug     # 开发服务器，端口 5000

# 3. 启动 Celery Worker（新终端）
celery -A celery_worker.celery worker --loglevel=info

# 4. 启动 Celery Beat（新终端，定时任务调度）
celery -A celery_worker.celery beat --loglevel=info

# 5. 启动前端（新终端）
cd frontend
npm install
npm run dev           # Vite 开发服务器，端口 5173
```

---

## 8. 补充设计清单

> 以下是开题报告中未提及但工程上必须有的设计。

| 补充项 | 为什么必须有 |
|---|---|
| **密码锁认证** | 部署在公网 = 数据裸奔，半天开发量换来安全保障 |
| **统一错误处理** | 没有它，每个接口都要写 try-catch，代码膨胀且不一致 |
| **统一响应格式** | 前端只需一个拦截器，不用每个页面单独处理返回值结构 |
| **输入校验层** | 不验证输入 = 脏数据入库 = 不可预测的 bug |
| **LLM 统一封装** | 切换 AI 提供商时只改一个文件，不用全项目搜索替换 |
| **软删除（笔记）** | 误删可恢复，答辩时也能证明数据完整性 |
| **数据库索引设计** | articles 表数据量大，没有索引 = 查询越来越慢 |
| **RSS 抓取容错** | 订阅源经常挂掉，不处理 = 错误扩散影响整个系统 |
| **环境变量管理** | 密钥写死在代码里 = 推到 Git 就泄露了 |
| **API 限速** | 密码接口不限速 = 可被暴力破解 |
| **前端路由守卫** | 未认证不该访问任何功能页 |
| **文章 HTML 清洗** | RSS 正文可能包含恶意脚本，不清洗 = XSS 漏洞 |
| **Redis 缓存** | 热榜、推荐结果等热数据不需要每次查 MongoDB |
| **分页机制** | 文章列表不分页 = 数据量大时前端卡死 |

---

## 9. 给 Claude Code 的使用提示

将本文件放在项目根目录。开始开发时，用以下方式与 Claude Code 交互：

```
# 每个 Phase 开始时，把对应章节给它：
"请根据 SPEC.md 中 Phase 0 的要求，初始化项目骨架。
参考 1.3 目录结构、3.1 统一响应格式、3.2 统一错误处理。"

# 每个模块开发时，明确指向具体章节：
"请实现 SPEC.md 2.2 节 RSS 模块的后端 Blueprint，
包括 routes.py、services.py、models.py、tasks.py。
数据模型参考 2.2 节的 MongoDB Schema。"

# 调试时给出具体上下文：
"RSS 刷新任务报错 [贴错误日志]，请修复。
参考 SPEC.md 2.2 节的抓取流程和健壮性设计。"

# 迭代时引用规范：
"Phase 3a 完成了，现在开始 Phase 3b。
请在已有的 RSS 模块基础上添加 AI 摘要功能。
参考 SPEC.md 2.2 节的 AI 摘要流程（按需触发）。"
```

**关键原则**：
1. **一次只让它做一个小任务**（一个文件、一个功能点）
2. **每完成一步就运行测试**，确认没问题再继续
3. **遇到 bug 先自己看日志**，带着日志去问它
4. **不要让它一次生成整个模块的所有代码**——会出错且难排查
5. **善用现成库**：凡是有成熟库能解决的事情，直接用库，不要自己实现
