<template>
  <div class="rss-page">
    <!-- 顶部操作栏 -->
    <div class="rss-toolbar">
      <div class="group-tabs">
        <el-radio-group v-model="activeGroup" size="default" @change="loadFeeds">
          <el-radio-button label="全部" value="" />
          <el-radio-button
            v-for="g in groups"
            :key="g.name"
            :label="`${g.name} (${g.count})`"
            :value="g.name"
          />
        </el-radio-group>
        <el-button text size="small" @click="showGroupDialog = true" style="margin-left: 8px">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
      <div class="toolbar-actions">
        <el-button type="primary" @click="handleRefreshAll" :loading="refreshingAll">
          刷新全部
        </el-button>
        <el-button @click="$router.push('/rss/manage')">管理订阅源</el-button>
      </div>
    </div>

    <!-- 订阅源卡片网格 -->
    <div class="feed-grid" v-loading="loading">
      <div v-for="feed in feeds" :key="feed._id" class="feed-card">
        <div class="feed-header">
          <span class="feed-title">{{ feed.title }}</span>
          <el-button
            text
            size="small"
            :loading="feed._refreshing"
            @click="handleRefreshFeed(feed)"
          >
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <div class="feed-meta">
          <el-tag size="small" type="info">{{ feed.group }}</el-tag>
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
      <el-empty v-if="!loading && feeds.length === 0" description="暂无订阅源，去添加一个吧" />
    </div>

    <!-- 分组管理对话框 -->
    <el-dialog v-model="showGroupDialog" title="管理分组" width="460px">
      <!-- 新建分组 -->
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
      <!-- 分组列表 -->
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
import { Refresh, WarningFilled, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  getFeeds, getFeedGroups, refreshFeed, refreshAllFeeds, getFeedArticles,
  createGroup, renameGroup, deleteGroup,
} from '../api'

const loading = ref(false)
const refreshingAll = ref(false)
const activeGroup = ref('')
const groups = ref([])
const feeds = ref([])

// 分组管理
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

// 分组操作
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

onMounted(() => {
  loadGroups()
  loadFeeds()
})
</script>

<style scoped>
.rss-page {
  padding: 0;
}

.rss-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.group-tabs {
  display: flex;
  align-items: center;
}

.feed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.feed-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.feed-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.feed-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.feed-time {
  font-size: 12px;
  color: #909399;
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
  border-top: 1px solid #f0f0f0;
  padding-top: 8px;
}

.article-row {
  padding: 6px 0;
  cursor: pointer;
  border-bottom: 1px solid #fafafa;
}

.article-row:hover {
  background: #f5f7fa;
  margin: 0 -16px;
  padding: 6px 16px;
}

.article-title {
  font-size: 13px;
  color: #303133;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-row.read .article-title {
  color: #b0b0b0;
}

.no-articles {
  font-size: 13px;
  color: #c0c4cc;
  text-align: center;
  padding: 16px 0;
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
  border-bottom: 1px solid #f0f0f0;
}

.group-name {
  font-size: 14px;
  color: #303133;
  flex: 1;
}

.group-count {
  font-size: 12px;
  color: #909399;
}

.no-groups {
  text-align: center;
  color: #c0c4cc;
  padding: 20px 0;
}
</style>
