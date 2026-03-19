<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <aside :class="['sidebar', { collapsed: isCollapsed }]">
      <div class="sidebar-logo" @click="toggleCollapse">
        <span v-show="!isCollapsed" class="logo-text">InfoHub</span>
        <span v-show="isCollapsed" class="logo-icon">I</span>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          :class="['nav-item', { active: activeMenu === item.path }]"
        >
          <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          <span v-show="!isCollapsed" class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-bottom">
        <div :class="['nav-item', 'settings-item']" @click="showSettings = true">
          <el-icon class="nav-icon"><Setting /></el-icon>
          <span v-show="!isCollapsed" class="nav-label">设置</span>
        </div>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <div class="main-wrapper">
      <header class="topbar">
        <span class="topbar-title">{{ currentTitle }}</span>
        <div class="topbar-right">
          <el-tooltip content="AI 对话" placement="bottom">
            <button class="ai-btn" @click="toggleChat">
              <el-icon :size="18"><ChatLineSquare /></el-icon>
            </button>
          </el-tooltip>
        </div>
      </header>

      <main class="main-content">
        <div class="content-container">
          <router-view v-slot="{ Component }">
            <transition name="page-fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>
    </div>
  </el-container>

  <!-- 全局 AI 对话浮窗 -->
  <ChatFloat />

  <!-- 设置弹窗 -->
  <el-dialog v-model="showSettings" title="设置" width="400px" :append-to-body="true">
    <el-button type="primary" @click="handleChangePassword">修改密码</el-button>
    <el-divider />
    <el-button @click="handleLogout">锁定并退出</el-button>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import ChatFloat from '@/modules/chat/components/ChatFloat.vue'
import {
  HomeFilled, Connection, Paperclip, TrendCharts, Notebook,
  Setting, ChatLineSquare,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const chat = useChatStore()

const isCollapsed = ref(false)
const showSettings = ref(false)

const menuItems = [
  { path: '/dashboard', label: '中心', icon: HomeFilled },
  { path: '/rss', label: '订阅', icon: Connection },
  { path: '/news', label: '广场', icon: Paperclip },
  { path: '/trending', label: '趋势', icon: TrendCharts },
  { path: '/notes', label: '笔记', icon: Notebook },
]

const activeMenu = computed(() => '/' + (route.path.split('/')[1] || 'dashboard'))

const titleMap = {
  '/dashboard': '中心',
  '/rss': '订阅',
  '/news': '广场',
  '/trending': '趋势',
  '/notes': '笔记',
}
const currentTitle = computed(() => titleMap[activeMenu.value] || 'InfoHub')

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

function toggleChat() {
  chat.isPanelOpen = !chat.isPanelOpen
}

function handleLogout() {
  showSettings.value = false
  auth.logout()
  router.push('/lock')
}

function handleChangePassword() {
  showSettings.value = false
  router.push('/lock?change=1')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

/* ========== 侧边栏 ========== */
.sidebar {
  width: 200px;
  background: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  flex-shrink: 0;
}
.sidebar.collapsed {
  width: 64px;
}

.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}
.logo-text {
  color: var(--text-inverse);
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
  white-space: nowrap;
}
.logo-icon {
  color: var(--text-inverse);
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  height: 44px;
  padding: 0 20px;
  color: rgba(250, 249, 246, 0.65);
  cursor: pointer;
  text-decoration: none;
  position: relative;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}
.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-inverse);
}
.nav-item.active {
  color: var(--text-inverse);
  background: rgba(255, 255, 255, 0.1);
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
}

.collapsed .nav-item {
  justify-content: center;
  padding: 0;
}
.collapsed .nav-item.active::before {
  top: 12px;
  bottom: 12px;
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
}
.nav-label {
  margin-left: 12px;
  font-size: 14px;
}

/* 底部设置 */
.sidebar-bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}
.settings-item {
  height: 48px;
}

/* ========== 右侧主区域 ========== */
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* ========== 顶栏 ========== */
.topbar {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}
.topbar-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.15s;
}
.ai-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  box-shadow: var(--shadow-sm);
}

/* ========== 主内容 ========== */
.main-content {
  flex: 1;
  overflow-y: auto;
  background: var(--bg-primary);
}
.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 32px;
}
</style>
