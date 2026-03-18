<template>
  <div class="article-wrapper" v-loading="loading">
    <template v-if="article">
      <Splitpanes v-if="splitMode" class="default-theme split-container" @resize="onSplitResize">
        <Pane :size="splitSize">
          <div class="article-page split-article">
            <div class="article-toolbar">
              <el-button @click="$router.back()">
                <el-icon><ArrowLeft /></el-icon> 返回
              </el-button>
              <div class="toolbar-actions">
                <el-button @click="splitMode = false">关闭分屏</el-button>
              </div>
            </div>
            <h1 class="article-title">{{ article.title }}</h1>
            <div class="article-meta">
              <span v-if="article.author">{{ article.author }}</span>
              <span>{{ formatDate(article.published_at) }}</span>
            </div>
            <div class="article-content" v-html="article.content"></div>
          </div>
        </Pane>
        <Pane :size="100 - splitSize">
          <div class="split-editor">
            <div class="split-editor-toolbar">
              <el-input v-model="splitNoteTitle" placeholder="笔记标题" size="default" />
              <el-button type="primary" size="default" @click="saveSplitNote" :loading="splitSaving">保存</el-button>
            </div>
            <MdEditor v-model="splitNoteContent" language="zh-CN" style="height: calc(100% - 50px)" />
          </div>
        </Pane>
      </Splitpanes>

      <!-- 普通模式 -->
      <div v-else class="article-page">
        <!-- 顶部操作栏 -->
        <div class="article-toolbar">
          <el-button @click="$router.back()">
            <el-icon><ArrowLeft /></el-icon> 返回
          </el-button>
          <div class="toolbar-actions">
            <el-button @click="handleSaveToNote" :loading="noteLoading">
              <el-icon><Notebook /></el-icon> 保存到笔记本
            </el-button>
            <el-button @click="enterSplitMode">
              <el-icon><Reading /></el-icon> 分屏笔记
            </el-button>
            <el-button @click="openOriginal">
              <el-icon><Link /></el-icon> 原文
            </el-button>
          </div>
        </div>

        <!-- 文章标题 -->
        <h1 class="article-title">{{ article.title }}</h1>

        <!-- 元信息 -->
        <div class="article-meta">
          <span v-if="article.author">{{ article.author }}</span>
          <span>{{ formatDate(article.published_at) }}</span>
          <el-tag v-for="tag in article.tags" :key="tag" size="small" type="info">
            {{ tag }}
          </el-tag>
        </div>

        <!-- AI 摘要区域 -->
        <div class="summary-section">
          <div v-if="summaryStatus === 'done'" class="summary-box summary-done">
            <div class="summary-header">
              <el-icon><MagicStick /></el-icon>
              <span>AI 摘要</span>
            </div>
            <p class="summary-text">{{ summaryText }}</p>
          </div>
          <div v-else-if="summaryLoading" class="summary-box summary-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>正在生成 AI 摘要...</span>
          </div>
          <div v-else-if="summaryStatus === 'failed'" class="summary-box summary-failed">
            <el-icon><WarningFilled /></el-icon>
            <span>摘要生成失败</span>
            <el-button text type="primary" size="small" @click="handleSummarize">点击重试</el-button>
          </div>
          <div v-else class="summary-box summary-none">
            <el-icon><MagicStick /></el-icon>
            <el-button type="primary" size="small" @click="handleSummarize">生成 AI 摘要</el-button>
          </div>
        </div>

        <!-- 正文（带右键菜单） -->
        <div class="article-content" v-html="article.content" @contextmenu="onContextMenu"></div>

        <!-- 右键菜单 -->
        <teleport to="body">
          <div
            v-if="ctxMenuVisible"
            class="context-menu"
            :style="{ left: ctxMenuX + 'px', top: ctxMenuY + 'px' }"
          >
            <div class="context-menu-item" @mousedown.prevent="handleCtxCreateNote">
              创建笔记
            </div>
          </div>
        </teleport>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Link, MagicStick, WarningFilled, Loading, Notebook, Reading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { h } from 'vue'
import { getArticle, markRead, summarizeArticle, articleToNote } from '../api'
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const article = ref(null)
const noteLoading = ref(false)

// 摘要状态
const summaryStatus = ref('none')
const summaryText = ref('')
const summaryLoading = ref(false)

// 右键菜单
const ctxMenuVisible = ref(false)
const ctxMenuX = ref(0)
const ctxMenuY = ref(0)
const selectedText = ref('')

// 分屏模式
const splitMode = ref(false)
const splitSize = ref(50)
const splitNoteTitle = ref('')
const splitNoteContent = ref('')
const splitSaving = ref(false)

async function loadArticle() {
  loading.value = true
  try {
    const res = await getArticle(route.params.id)
    article.value = res.data
    summaryStatus.value = res.data.summary_status || 'none'
    summaryText.value = res.data.summary || ''
    await markRead(route.params.id)
    article.value.is_read = true
  } catch {
    ElMessage.error('文章不存在')
  } finally {
    loading.value = false
  }
}

async function handleSummarize() {
  summaryLoading.value = true
  summaryStatus.value = 'none'
  try {
    const res = await summarizeArticle(route.params.id)
    summaryText.value = res.data.summary
    summaryStatus.value = 'done'
  } catch (e) {
    summaryStatus.value = 'failed'
    ElMessage.error(e.response?.data?.message || '摘要生成失败')
  } finally {
    summaryLoading.value = false
  }
}

function openOriginal() {
  window.open(article.value.url, '_blank')
}

// 保存到笔记本
async function handleSaveToNote() {
  noteLoading.value = true
  try {
    const res = await articleToNote(article.value._id)
    const noteId = res.data._id
    ElMessage({
      type: 'success',
      message: h('span', null, [
        '已保存到笔记本 ',
        h('a', {
          style: 'color: #409eff; cursor: pointer; text-decoration: underline;',
          onClick: () => router.push(`/notes/${noteId}`),
        }, '去查看'),
      ]),
      duration: 5000,
    })
  } catch {
    ElMessage.error('保存失败')
  } finally {
    noteLoading.value = false
  }
}

// 右键菜单
function onContextMenu(e) {
  const sel = window.getSelection()
  const text = sel ? sel.toString().trim() : ''
  if (!text) return
  e.preventDefault()
  selectedText.value = text
  ctxMenuX.value = e.clientX
  ctxMenuY.value = e.clientY
  ctxMenuVisible.value = true
}

function handleCtxCreateNote() {
  ctxMenuVisible.value = false
  router.push({
    path: '/notes/new',
    query: {
      source_type: 'rss',
      article_id: article.value._id,
      article_url: article.value.url || '',
      title: article.value.title || '',
      selected_text: selectedText.value,
    },
  })
}

function hideCtxMenu() {
  ctxMenuVisible.value = false
}

// 分屏模式
function enterSplitMode() {
  splitNoteTitle.value = article.value.title || ''
  splitNoteContent.value = ''
  if (article.value.url) {
    splitNoteContent.value = `[原文链接](${article.value.url})\n\n`
  }
  splitMode.value = true
}

function onSplitResize(e) {
  if (e && e[0]) splitSize.value = e[0].size
}

async function saveSplitNote() {
  if (!splitNoteTitle.value.trim()) {
    ElMessage.warning('请输入笔记标题')
    return
  }
  splitSaving.value = true
  try {
    await createNote({
      title: splitNoteTitle.value,
      content: splitNoteContent.value,
      source: {
        type: 'rss',
        article_id: article.value._id,
        article_url: article.value.url || '',
      },
      tags: [],
    })
    ElMessage.success('笔记已保存')
    splitMode.value = false
  } catch {
    ElMessage.error('保存失败')
  } finally {
    splitSaving.value = false
  }
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(() => {
  loadArticle()
  document.addEventListener('click', hideCtxMenu)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', hideCtxMenu)
})
</script>

<style scoped>
.article-wrapper {
  min-height: 400px;
}

.split-container {
  height: calc(100vh - 100px);
}

.split-article {
  height: 100%;
  overflow-y: auto;
}

.split-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 12px;
  background: #fff;
}

.split-editor-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.article-page {
  max-width: 800px;
  margin: 0 auto;
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  min-height: 400px;
}

.article-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.article-title {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  line-height: 1.4;
  margin-bottom: 12px;
}

.article-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  color: #909399;
  margin-bottom: 16px;
}

/* 摘要区域 */
.summary-section {
  margin-bottom: 20px;
}

.summary-box {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  border-radius: 6px;
  padding: 12px 16px;
  font-size: 13px;
}

.summary-none {
  background: #f5f7fa;
  color: #909399;
  align-items: center;
}

.summary-loading {
  background: #ecf5ff;
  color: #409eff;
  align-items: center;
}

.summary-done {
  background: #f0f9eb;
  color: #303133;
  flex-direction: column;
  gap: 6px;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #67c23a;
  font-size: 13px;
}

.summary-text {
  margin: 0;
  line-height: 1.7;
  font-size: 14px;
}

.summary-failed {
  background: #fef0f0;
  color: #f56c6c;
  align-items: center;
}

.article-content {
  font-size: 15px;
  line-height: 1.8;
  color: #303133;
  word-break: break-word;
}

.article-content :deep(img) {
  max-width: 100%;
  border-radius: 4px;
}

.article-content :deep(a) {
  color: #409eff;
}

.article-content :deep(pre) {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

/* 右键菜单 */
.context-menu {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  padding: 4px 0;
}

.context-menu-item {
  padding: 8px 16px;
  font-size: 13px;
  color: #303133;
  cursor: pointer;
  white-space: nowrap;
}

.context-menu-item:hover {
  background: #ecf5ff;
  color: #409eff;
}
</style>
