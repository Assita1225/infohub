import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  // 认证页面（无侧边栏布局）
  {
    path: '/lock',
    name: 'Lock',
    component: () => import('@/modules/auth/views/LockView.vue'),
    meta: { public: true },
  },
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('@/modules/auth/views/SetupView.vue'),
    meta: { public: true },
  },
  // 主布局（带侧边栏）
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/modules/dashboard/views/DashboardView.vue'),
      },
      {
        path: 'overview',
        name: 'Overview',
        component: () => import('@/modules/overview/views/OverviewView.vue'),
      },
      {
        path: 'rss',
        name: 'RSS',
        component: () => import('@/modules/rss/views/RssView.vue'),
      },
      {
        path: 'rss/manage',
        name: 'RSSManage',
        component: () => import('@/modules/rss/views/ManageView.vue'),
      },
      {
        path: 'rss/timeline',
        name: 'RSSTimeline',
        component: () => import('@/modules/rss/views/TimelineView.vue'),
      },
      {
        path: 'rss/article/:id',
        name: 'RSSArticle',
        component: () => import('@/modules/rss/views/ArticleView.vue'),
      },
      {
        path: 'news',
        name: 'News',
        component: () => import('@/modules/news/views/NewsView.vue'),
      },
      {
        path: 'news/read-later',
        name: 'NewsReadLater',
        component: () => import('@/modules/news/views/ReadLaterView.vue'),
      },
      {
        path: 'news/article/:id',
        name: 'NewsArticle',
        component: () => import('@/modules/news/views/NewsArticleView.vue'),
      },
      {
        path: 'trending',
        name: 'Trending',
        component: () => import('@/modules/trending/views/TrendingView.vue'),
      },
      {
        path: 'notes',
        name: 'Notes',
        component: () => import('@/modules/notes/views/NotesView.vue'),
      },
      {
        path: 'notes/new',
        name: 'NoteNew',
        component: () => import('@/modules/notes/views/NoteEditView.vue'),
      },
      {
        path: 'notes/:id',
        name: 'NoteEdit',
        component: () => import('@/modules/notes/views/NoteEditView.vue'),
      },
      {
        path: 'tools',
        name: 'Tools',
        component: () => import('@/modules/tools/views/ToolsView.vue'),
      },
      {
        path: 'tools/translate',
        name: 'ToolTranslate',
        component: () => import('@/modules/tools/views/TranslateView.vue'),
      },
      {
        path: 'tools/polish',
        name: 'ToolPolish',
        component: () => import('@/modules/tools/views/PolishView.vue'),
      },
      {
        path: 'tools/summarize',
        name: 'ToolSummarize',
        component: () => import('@/modules/tools/views/SummarizeView.vue'),
      },
      {
        path: 'habits',
        name: 'Habits',
        component: () => import('@/modules/habits/views/HabitsView.vue'),
      },
      {
        path: 'finance',
        name: 'Finance',
        component: () => import('@/modules/finance/views/FinanceView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // 首次加载时检查密码是否已设置
  if (!auth.checked) {
    try {
      await auth.checkStatus()
    } catch {
      // 后端不可用时放行到 lock 页
      if (!to.meta.public) return '/lock'
      return true
    }
  }

  // 未设置密码 → 强制跳转 setup
  if (!auth.initialized && to.name !== 'Setup') {
    return '/setup'
  }

  // 已设置密码但未登录 → 跳转 lock
  if (auth.initialized && !auth.isLoggedIn() && !to.meta.public) {
    return '/lock'
  }

  // 已登录却访问 lock/setup → 跳转首页
  if (auth.isLoggedIn() && to.meta.public) {
    return '/dashboard'
  }
})

export default router
