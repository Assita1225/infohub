<template>
  <div class="notes-page">
    <!-- 顶部操作栏 -->
    <div class="notes-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchText"
          placeholder="搜索笔记..."
          :prefix-icon="Search"
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-select v-model="filterTag" placeholder="标签筛选" clearable style="width: 140px" @change="loadNotes">
          <el-option v-for="t in allTags" :key="t" :label="t" :value="t" />
        </el-select>
        <el-select v-model="sortField" style="width: 140px" @change="loadNotes">
          <el-option label="最近更新" value="updated_at" />
          <el-option label="最近创建" value="created_at" />
          <el-option label="标题排序" value="title" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button v-if="showTrash" @click="showTrash = false; loadNotes()">
          <el-icon><ArrowLeft /></el-icon> 返回笔记
        </el-button>
        <el-button v-else text @click="enterTrash">
          <el-icon><Delete /></el-icon> 回收站
        </el-button>
        <el-button v-if="!showTrash" type="primary" @click="$router.push('/notes/new')">
          <el-icon><Plus /></el-icon> 新建笔记
        </el-button>
      </div>
    </div>

    <!-- 笔记卡片列表 -->
    <div class="notes-grid" v-loading="loading">
      <div
        v-for="note in notes"
        :key="note._id"
        class="note-card"
        @click="!showTrash && $router.push(`/notes/${note._id}`)"
      >
        <div class="note-card-header">
          <h3 class="note-title">{{ note.title || '无标题' }}</h3>
          <el-tag v-if="note.source && note.source.type !== 'manual'" size="small" type="info">
            {{ note.source.type === 'rss' ? 'RSS' : '新闻' }}
          </el-tag>
        </div>
        <p class="note-preview">{{ stripMarkdown(note.content) }}</p>
        <div class="note-footer">
          <div class="note-tags">
            <el-tag v-for="tag in note.tags" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
          </div>
          <span class="note-time">{{ formatTime(showTrash ? note.deleted_at : note.updated_at) }}</span>
        </div>
        <!-- 回收站操作 -->
        <div v-if="showTrash" class="trash-actions">
          <el-button type="primary" size="small" @click.stop="handleRestore(note._id)">恢复</el-button>
        </div>
      </div>
      <el-empty v-if="!loading && notes.length === 0" :description="showTrash ? '回收站为空' : '暂无笔记'" />
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="notes-pagination">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="showTrash ? loadTrash() : loadNotes()"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, Plus, Delete, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getNotes, getTrashNotes, restoreNote } from '../api'

const loading = ref(false)
const notes = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const searchText = ref('')
const filterTag = ref('')
const sortField = ref('updated_at')
const allTags = ref([])
const showTrash = ref(false)

async function loadNotes() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize, sort: sortField.value }
    if (searchText.value) params.search = searchText.value
    if (filterTag.value) params.tag = filterTag.value
    const res = await getNotes(params)
    notes.value = res.data.items
    total.value = res.data.total
    collectTags(res.data.items)
  } catch {
    ElMessage.error('加载笔记失败')
  } finally {
    loading.value = false
  }
}

async function loadTrash() {
  loading.value = true
  try {
    const res = await getTrashNotes({ page: page.value, page_size: pageSize })
    notes.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('加载回收站失败')
  } finally {
    loading.value = false
  }
}

function enterTrash() {
  showTrash.value = true
  page.value = 1
  loadTrash()
}

async function handleRestore(id) {
  try {
    await restoreNote(id)
    ElMessage.success('已恢复')
    loadTrash()
  } catch {
    ElMessage.error('恢复失败')
  }
}

function handleSearch() {
  page.value = 1
  loadNotes()
}

function collectTags(items) {
  const tagSet = new Set(allTags.value)
  items.forEach(n => (n.tags || []).forEach(t => tagSet.add(t)))
  allTags.value = [...tagSet].sort()
}

function stripMarkdown(text) {
  if (!text) return ''
  return text.replace(/[#*`>\[\]()_~\-|]/g, '').substring(0, 120)
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

onMounted(loadNotes)
</script>

<style scoped>
.notes-page {
  padding: 0;
}

.notes-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  gap: 8px;
  align-items: center;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.note-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.note-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.note-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.note-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.note-preview {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
  margin: 0 0 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.note-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.note-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.note-time {
  font-size: 12px;
  color: #c0c4cc;
  white-space: nowrap;
}

.trash-actions {
  margin-top: 10px;
  text-align: right;
}

.notes-pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
