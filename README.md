# InfoHub — 个人信息聚合与智能分析终端

#没更新，不是最新

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | Vue 3 + Vue Router + Pinia + Element Plus + ECharts |
| 后端 | Flask + Flask-CORS + Flask-SocketIO + Flask-Limiter |
| 数据库 | MongoDB（主存储）+ Redis（缓存/消息队列/会话） |
| 异步任务 | Celery + Redis |
| AI | LLM API（统一封装，可切换提供商） |
| NLP | Jieba 中文分词 + scikit-learn TF-IDF + SimHash 去重 |
| 部署 | Nginx + Gunicorn + Docker（MongoDB/Redis） |

## 功能模块

| 模块 | 说明 |
|---|---|
| 密码锁认证 (Auth) | 极简单用户密码锁，JWT 鉴权，保护个人隐私数据 |
| 个人中心 (Dashboard) | 可拖拽微件画布，集成天气、时钟、日历、待办、未读统计等 |
| RSS 订阅 (RSS) | 订阅源管理、手动/批量刷新、按需 AI 摘要、收藏与已读管理 |
| 新闻广场 (News) | 系统预设新闻源，按分类浏览，支持稍后读、转笔记 |
| 热度趋势 (Trending) | 跨平台热搜热榜聚合（微博、知乎、百度、GitHub 等）+ 词云可视化 |
| 个性化推荐 (Recommend) | 基于兴趣标签的内容筛选，内嵌于趋势页面 |
| 笔记 (Notes) | Markdown 编辑器，支持从文章一键创建笔记，软删除 + 回收站 |
| AI 对话 (Chat) | 全局浮窗智能助手，感知当前页面上下文，支持流式响应 |

## 本地开发启动

### 前置条件

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### 环境配置

```bash
# 复制环境变量模板并填写配置
cp .env.example .env
```

### 启动步骤

```bash
# 1. 启动基础设施（MongoDB + Redis）
docker-compose up -d

# 2. 启动后端
cd backend
pip install -r requirements.txt
flask run --debug                # 开发服务器，端口 5000

# 3. 启动 Celery Worker（新终端）
cd backend
celery -A celery_worker.celery worker --loglevel=info

# 4. 启动 Celery Beat（新终端，定时任务调度）
cd backend
celery -A celery_worker.celery beat --loglevel=info

# 5. 启动前端（新终端）
cd frontend
npm install
npm run dev                      # Vite 开发服务器，端口 5173
```

### 访问

- 前端：http://localhost:5173
- 后端 API：http://localhost:5000/api
