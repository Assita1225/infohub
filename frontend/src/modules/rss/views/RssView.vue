<template>
  <div class="rss-page">
    <p class="page-subtitle">{{ subtitle }}</p>
    <!-- 顶部操作栏 -->
    <div class="rss-toolbar">
      <div class="group-tabs">
        <button
          :class="['pill-btn', { active: activeGroup === '' }]"
          @click="activeGroup = ''; loadFeeds()"
        >全部</button>
        <button
          v-for="g in groups"
          :key="g.name"
          :class="['pill-btn', { active: activeGroup === g.name }]"
          @click="activeGroup = g.name; loadFeeds()"
        >{{ g.name }} ({{ g.count }})</button>
        <el-button text size="small" @click="showGroupDialog = true" style="margin-left: 4px">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
      <div class="toolbar-actions">
        <el-button type="primary" @click="handleRefreshAll" :loading="refreshingAll">
          刷新全部
        </el-button>
        <el-button @click="$router.push('/rss/timeline')">时间线</el-button>
        <el-button @click="$router.push('/rss/manage')">管理订阅源</el-button>
      </div>
    </div>

    <!-- 订阅源卡片网格 -->
    <div class="feed-grid" v-loading="loading">
      <div v-for="(feed, fi) in feeds" :key="feed._id" class="feed-card card">
        <div class="feed-color-bar" :style="{ background: groupColors[fi % groupColors.length] }" />
        <div class="feed-body">
          <div class="feed-header">
            <span class="feed-title">{{ feed.title }}</span>
            <button
              class="refresh-btn"
              :class="{ spinning: feed._refreshing }"
              @click="handleRefreshFeed(feed)"
            >
              <el-icon><Refresh /></el-icon>
            </button>
          </div>
          <div class="feed-meta">
            <el-tag size="small" effect="plain" round>{{ feed.group }}</el-tag>
            <el-tag v-if="feed.feed_type === 'web_monitor'" size="small" type="warning" effect="plain" round>网页监控</el-tag>
            <span v-if="feed.last_fetched_at" class="feed-time">
              {{ formatTime(feed.last_fetched_at) }}
            </span>
            <span v-else class="feed-time">未刷新</span>
          </div>
          <div v-if="feed.error_count > 0" class="feed-error">
            <el-icon color="#f56c6c"><WarningFilled /></el-icon>
            <span>{{ feed.last_error }}</span>
          </div>
          <!-- 文章列表 -->
          <div class="feed-articles">
            <div
              v-for="a in feed._articles"
              :key="a._id"
              class="article-row"
              :class="{ read: a.is_read }"
              @click="$router.push(`/rss/article/${a._id}`)"
            >
              <span class="article-title">{{ a.title }}</span>
            </div>
            <div v-if="feed._articles && feed._articles.length === 0" class="no-articles">
              暂无文章，点击刷新
            </div>
          </div>
        </div>
      </div>

      <div v-if="!loading && feeds.length === 0" class="empty-state">
        <el-icon :size="48" color="var(--text-muted)"><Connection /></el-icon>
        <p>还没有订阅源，去添加一个？</p>
        <el-button type="primary" @click="$router.push('/rss/manage')">添加订阅源</el-button>
      </div>
    </div>

    <!-- 分组管理对话框 -->
    <el-dialog v-model="showGroupDialog" title="管理分组" width="460px">
      <div class="group-add-row">
        <el-input
          v-model="newGroupName"
          placeholder="输入新分组名称"
          size="default"
          @keyup.enter="handleAddGroup"
        />
        <el-button type="primary" @click="handleAddGroup" :disabled="!newGroupName.trim()">
          添加
        </el-button>
      </div>
      <div class="group-list">
        <div v-for="g in groups" :key="g.name" class="group-item">
          <template v-if="editingGroup === g.name">
            <el-input v-model="editGroupName" size="small" style="flex:1" @keyup.enter="handleRenameGroup(g.name)" />
            <el-button text size="small" type="primary" @click="handleRenameGroup(g.name)">保存</el-button>
            <el-button text size="small" @click="editingGroup = null">取消</el-button>
          </template>
          <template v-else>
            <span class="group-name">{{ g.name }}</span>
            <span class="group-count">{{ g.count }} 个源</span>
            <el-button text size="small" @click="startEditGroup(g)">重命名</el-button>
            <el-popconfirm
              v-if="g.name !== '未分组'"
              :title="`确认删除？该分组下 ${g.count} 个订阅源将移至「未分组」`"
              @confirm="handleDeleteGroup(g.name)"
            >
              <template #reference>
                <el-button text size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </div>
        <div v-if="groups.length === 0" class="no-groups">暂无分组</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Refresh, WarningFilled, Setting, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  getFeeds, getFeedGroups, refreshFeed, refreshAllFeeds, getFeedArticles,
  createGroup, renameGroup, deleteGroup, getRssStats,
} from '../api'

const groupColors = ['#C45A3C', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#14B8A6']

const loading = ref(false)
const refreshingAll = ref(false)
const activeGroup = ref('')
const groups = ref([])
const feeds = ref([])

const subtitle = ref('我的专属信息源')

const showGroupDialog = ref(false)
const newGroupName = ref('')
const editingGroup = ref(null)
const editGroupName = ref('')

async function loadGroups() {
  try {
    const res = await getFeedGroups()
    groups.value = res.data
  } catch { /* 静默 */ }
}

async function loadFeeds() {
  loading.value = true
  try {
    const res = await getFeeds(activeGroup.value || undefined)
    feeds.value = res.data.map(f => reactive({ ...f, _refreshing: false, _articles: [] }))
    for (const feed of feeds.value) {
      loadFeedArticles(feed)
    }
  } catch {
    ElMessage.error('加载订阅源失败')
  } finally {
    loading.value = false
  }
}

async function loadFeedArticles(feed) {
  try {
    const res = await getFeedArticles(feed._id, 1, feed.display_count || 5)
    feed._articles = res.data.items
  } catch { /* 静默 */ }
}

async function handleRefreshFeed(feed) {
  feed._refreshing = true
  try {
    const res = await refreshFeed(feed._id)
    ElMessage.success(res.message)
    await loadFeedArticles(feed)
    feed.last_fetched_at = new Date().toISOString()
    feed.error_count = 0
    feed.last_error = null
  } catch (e) {
    const msg = e.response?.data?.message || '刷新失败'
    ElMessage.error(msg)
  } finally {
    feed._refreshing = false
  }
}

async function handleRefreshAll() {
  refreshingAll.value = true
  try {
    const res = await refreshAllFeeds()
    ElMessage.success(res.message)
    await loadGroups()
    await loadFeeds()
  } catch {
    ElMessage.error('刷新失败')
  } finally {
    refreshingAll.value = false
  }
}

async function handleAddGroup() {
  const name = newGroupName.value.trim()
  if (!name) return
  try {
    await createGroup(name)
    ElMessage.success('分组已创建')
    newGroupName.value = ''
    await loadGroups()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '创建失败')
  }
}

function startEditGroup(g) {
  editingGroup.value = g.name
  editGroupName.value = g.name
}

async function handleRenameGroup(oldName) {
  const newName = editGroupName.value.trim()
  if (!newName || newName === oldName) { editingGroup.value = null; return }
  try {
    await renameGroup(oldName, newName)
    ElMessage.success('重命名成功')
    editingGroup.value = null
    if (activeGroup.value === oldName) activeGroup.value = newName
    await loadGroups()
    await loadFeeds()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '重命名失败')
  }
}

async function handleDeleteGroup(name) {
  try {
    await deleteGroup(name)
    ElMessage.success('分组已删除')
    if (activeGroup.value === name) activeGroup.value = ''
    await loadGroups()
    await loadFeeds()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '删除失败')
  }
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = (now - d) / 1000 / 60
  if (diff < 1) return '刚刚'
  if (diff < 60) return `${Math.floor(diff)}分钟前`
  if (diff < 1440) return `${Math.floor(diff / 60)}小时前`
  return d.toLocaleDateString('zh-CN')
}

async function loadSubtitle() {
  try {
    const res = await getRssStats()
    const unread = res.data.unread_count
    if (unread != null) subtitle.value = `今天有 ${unread} 条新内容等你查看`
  } catch { /* fallback already set */ }
}

onMounted(() => {
  loadGroups()
  loadFeeds()
  loadSubtitle()
})
</script>

<style scoped>
.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 16px;
}

/* 胶囊标签 */
.group-tabs {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.pill-btn {
  padding: 5px 14px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.pill-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.pill-btn.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.rss-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* 卡片网格 */
.feed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.feed-card {
  display: flex;
  overflow: hidden;
  padding: 0;
}

.feed-color-bar {
  width: 4px;
  flex-shrink: 0;
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
}

.feed-body {
  flex: 1;
  padding: 16px 20px;
  min-width: 0;
}

.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.feed-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.refresh-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  padding: 4px;
  border-radius: var(--radius-sm);
  transition: color 0.15s;
}
.refresh-btn:hover {
  color: var(--accent);
}
.refresh-btn.spinning .el-icon {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.feed-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.feed-time {
  font-size: 12px;
  color: var(--text-muted);
}

.feed-error {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #f56c6c;
  margin-top: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.feed-articles {
  margin-top: 12px;
  border-top: 1px solid var(--border-light);
  padding-top: 8px;
}

.article-row {
  padding: 6px 0;
  cursor: pointer;
  border-bottom: 1px solid var(--border-light);
  transition: background 0.1s;
}

.article-row:last-child {
  border-bottom: none;
}

.article-row:hover {
  background: var(--bg-hover);
  margin: 0 -20px;
  padding: 6px 20px;
}

.article-title {
  font-size: 13px;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-row.read .article-title {
  color: var(--text-muted);
}

.no-articles {
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  padding: 16px 0;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: var(--text-muted);
  font-size: 14px;
  gap: 12px;
}

/* 分组管理对话框 */
.group-add-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.group-list {
  max-height: 300px;
  overflow-y: auto;
}

.group-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
}

.group-name {
  font-size: 14px;
  color: var(--text-primary);
  flex: 1;
}

.group-count {
  font-size: 12px;
  color: var(--text-muted);
}

.no-groups {
  text-align: center;
  color: var(--text-muted);
  padding: 20px 0;
}

@media (max-width: 767px) {
  .feed-grid {
    grid-template-columns: 1fr;
  }
  .rss-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .toolbar-actions {
    justify-content: flex-end;
  }
}
</style>
