<template>
  <div class="notes-page">
    <p class="page-subtitle">{{ subtitle }}</p>
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
        <template v-if="!showTrash">
          <el-button v-if="selectMode" :disabled="selectedIds.length === 0" @click="handleBatchExport">
            导出选中 ({{ selectedIds.length }})
          </el-button>
          <el-button @click="selectMode = !selectMode; selectedIds = []">
            {{ selectMode ? '取消选择' : '批量导出' }}
          </el-button>
          <el-button type="primary" @click="$router.push('/notes/new')">
            <el-icon><Plus /></el-icon> 新建笔记
          </el-button>
        </template>
      </div>
    </div>

    <!-- 笔记卡片列表 -->
    <div class="notes-list" v-loading="loading">
      <div
        v-for="note in notes"
        :key="note._id"
        class="note-item card"
        @click="!showTrash && $router.push(`/notes/${note._id}`)"
      >
        <el-checkbox
          v-if="selectMode && !showTrash"
          :model-value="selectedIds.includes(note._id)"
          class="note-checkbox"
          @click.stop
          @change="toggleSelect(note._id)"
        />
        <div class="note-accent-bar" />
        <div class="note-body">
          <div class="note-card-header">
            <h3 class="note-title">{{ note.title || '无标题' }}</h3>
            <el-tag v-if="note.source && note.source.type !== 'manual'" size="small" effect="plain" round>
              {{ note.source.type === 'rss' ? 'RSS' : '新闻' }}
            </el-tag>
          </div>
          <p class="note-preview">{{ stripMarkdown(note.content) }}</p>
          <div class="note-footer">
            <div class="note-tags">
              <span v-for="tag in note.tags" :key="tag" class="note-tag-pill">{{ tag }}</span>
            </div>
            <span class="note-time">{{ formatTime(showTrash ? note.deleted_at : note.updated_at) }}</span>
          </div>
          <!-- 回收站操作 -->
          <div v-if="showTrash" class="trash-actions">
            <el-button type="primary" size="small" @click.stop="handleRestore(note._id)">恢复</el-button>
          </div>
        </div>
      </div>

      <div v-if="!loading && notes.length === 0" class="empty-state">
        <el-icon :size="48" color="var(--text-muted)"><Notebook /></el-icon>
        <p>{{ showTrash ? '回收站为空' : '暂无笔记，创建一个吧' }}</p>
        <el-button v-if="!showTrash" type="primary" @click="$router.push('/notes/new')">新建笔记</el-button>
      </div>
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
import { Search, Plus, Delete, ArrowLeft, Notebook } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getNotes, getTrashNotes, restoreNote, exportNotesBatch } from '../api'

const subtitle = ref('记录灵感，沉淀知识')

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
const selectMode = ref(false)
const selectedIds = ref([])

async function loadNotes() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize, sort: sortField.value }
    if (searchText.value) params.search = searchText.value
    if (filterTag.value) params.tag = filterTag.value
    const res = await getNotes(params)
    notes.value = res.data.items
    total.value = res.data.total
    subtitle.value = `你已积累 ${res.data.total} 篇笔记`
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

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

async function handleBatchExport() {
  if (selectedIds.value.length === 0) return
  try {
    const res = await exportNotesBatch(selectedIds.value)
    const url = URL.createObjectURL(res)
    const a = document.createElement('a')
    a.href = url
    a.download = 'notes_export.zip'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
    selectMode.value = false
    selectedIds.value = []
  } catch {
    ElMessage.error('导出失败')
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
.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 16px;
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

/* 笔记列表项 */
.notes-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.note-item {
  display: flex;
  overflow: hidden;
  padding: 0;
  cursor: pointer;
}

.note-checkbox {
  margin: auto 0;
  padding: 0 8px 0 14px;
}

.note-accent-bar {
  width: 3px;
  flex-shrink: 0;
  background: transparent;
  transition: background 0.15s;
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
}

.note-item:hover .note-accent-bar {
  background: var(--accent);
}

.note-body {
  flex: 1;
  padding: 16px 20px;
  min-width: 0;
}

.note-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.note-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.note-preview {
  font-size: 13px;
  color: var(--text-muted);
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

.note-tag-pill {
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 11px;
}

.note-time {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}

.trash-actions {
  margin-top: 10px;
  text-align: right;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: var(--text-muted);
  font-size: 14px;
  gap: 12px;
}

.notes-pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

@media (max-width: 767px) {
  .notes-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .toolbar-left {
    flex-wrap: wrap;
  }
  .toolbar-left .el-input,
  .toolbar-left .el-select {
    width: 100% !important;
  }
  .toolbar-right {
    justify-content: flex-end;
  }
}
</style>
