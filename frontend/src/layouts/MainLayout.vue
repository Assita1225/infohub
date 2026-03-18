<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapsed ? '64px' : '200px'" class="sidebar">
      <div class="logo" @click="$router.push('/dashboard')">
        <span v-show="!isCollapsed" class="logo-text">InfoHub</span>
        <span v-show="isCollapsed" class="logo-text">I</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        router
        background-color="#1d1e1f"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title>中心</template>
        </el-menu-item>
        <el-menu-item index="/rss">
          <el-icon><Connection /></el-icon>
          <template #title>订阅</template>
        </el-menu-item>
        <el-menu-item index="/news">
          <el-icon><Paperclip /></el-icon>
          <template #title>广场</template>
        </el-menu-item>
        <el-menu-item index="/trending">
          <el-icon><TrendCharts /></el-icon>
          <template #title>趋势</template>
        </el-menu-item>
        <el-menu-item index="/notes">
          <el-icon><Notebook /></el-icon>
          <template #title>笔记</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧主区域 -->
    <el-container>
      <el-header class="header">
        <el-icon class="collapse-btn" @click="isCollapsed = !isCollapsed">
          <Fold v-if="!isCollapsed" />
          <Expand v-else />
        </el-icon>
        <span class="header-title">{{ currentTitle }}</span>
        <div class="header-right">
          <el-button text @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            锁定
          </el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>

  <!-- 全局 AI 对话浮窗 -->
  <ChatFloat />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ChatFloat from '@/modules/chat/components/ChatFloat.vue'
import {
  HomeFilled, Connection, Paperclip, TrendCharts, Notebook,
  Fold, Expand, SwitchButton,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const isCollapsed = ref(false)

const activeMenu = computed(() => '/' + (route.path.split('/')[1] || 'dashboard'))

const titleMap = {
  '/dashboard': '中心',
  '/rss': '订阅',
  '/news': '广场',
  '/trending': '趋势',
  '/notes': '笔记',
}
const currentTitle = computed(() => titleMap[activeMenu.value] || 'InfoHub')

function handleLogout() {
  auth.logout()
  router.push('/lock')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background-color: #1d1e1f;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.logo-text {
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 2px;
}

.header {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
  padding: 0 20px;
  height: 60px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  margin-right: 16px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.header-right {
  margin-left: auto;
}

.main-content {
  background-color: #f5f7fa;
}

.el-menu {
  border-right: none;
}
</style>
