<template>
  <div class="article-wrapper" v-loading="loading">
    <template v-if="article">
      <div class="article-page">
        <div class="article-toolbar">
          <el-button @click="$router.back()">
            <el-icon><ArrowLeft /></el-icon> 返回
          </el-button>
          <div class="toolbar-actions">
            <el-button
              :type="article.is_read_later ? 'warning' : 'default'"
              @click="handleReadLater"
            >
              <el-icon><Collection /></el-icon>
              {{ article.is_read_later ? '已稍后读' : '稍后读' }}
            </el-button>
            <el-button @click="handleToNote" :loading="noteLoading">
              <el-icon><Notebook /></el-icon> 保存到笔记本
            </el-button>
            <el-button @click="openOriginal">
              <el-icon><Link /></el-icon> 原文
            </el-button>
          </div>
        </div>

        <h1 class="article-title">{{ article.title }}</h1>

        <div class="article-meta">
          <span v-if="article.author">{{ article.author }}</span>
          <span>{{ formatDate(article.published_at) }}</span>
          <el-tag v-for="tag in article.tags" :key="tag" size="small" effect="plain" round>
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

        <!-- 正文 -->
        <div class="article-content" v-html="article.content"></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Collection, Link, MagicStick, WarningFilled, Loading, Notebook } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  getNewsArticle,
  summarizeNewsArticle,
  addReadLater,
  removeReadLater,
  articleToNote,
} from '../api'
import { useChatStore } from '@/stores/chat'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

const loading = ref(true)
const article = ref(null)
const noteLoading = ref(false)

const summaryStatus = ref('none')
const summaryText = ref('')
const summaryLoading = ref(false)

async function loadArticle() {
  loading.value = true
  try {
    const res = await getNewsArticle(route.params.id)
    article.value = res.data
    summaryStatus.value = res.data.summary_status || 'none'
    summaryText.value = res.data.summary || ''

    chatStore.setContext({
      page: 'news',
      articleId: res.data._id,
      articleTitle: res.data.title,
    })
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
    const res = await summarizeNewsArticle(route.params.id)
    summaryText.value = res.data.summary
    summaryStatus.value = 'done'
  } catch (e) {
    summaryStatus.value = 'failed'
    ElMessage.error(e.response?.data?.message || '摘要生成失败')
  } finally {
    summaryLoading.value = false
  }
}

async function handleReadLater() {
  try {
    if (article.value.is_read_later) {
      await removeReadLater(article.value._id)
      article.value.is_read_later = false
      ElMessage.success('已移出稍后读')
    } else {
      await addReadLater(article.value._id)
      article.value.is_read_later = true
      ElMessage.success('已添加到稍后读')
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleToNote() {
  noteLoading.value = true
  try {
    const res = await articleToNote(article.value._id)
    const noteId = res.data._id
    ElMessage({
      type: 'success',
      message: h('span', null, [
        '已保存到笔记本 ',
        h('a', {
          style: 'color: var(--accent); cursor: pointer; text-decoration: underline;',
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

function openOriginal() {
  window.open(article.value.url, '_blank')
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(loadArticle)
</script>

<style scoped>
.article-wrapper {
  min-height: 400px;
}

.article-page {
  max-width: 720px;
  margin: 0 auto;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 32px;
  min-height: 400px;
  box-shadow: var(--shadow-sm);
}

.article-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.article-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 12px;
}

.article-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-light);
}

/* 摘要区域 */
.summary-section {
  margin-bottom: 24px;
}

.summary-box {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  border-radius: var(--radius-md);
  padding: 12px 16px;
  font-size: 13px;
}

.summary-none {
  background: var(--bg-hover);
  color: var(--text-muted);
  align-items: center;
}

.summary-loading {
  background: var(--accent-light);
  color: var(--accent);
  align-items: center;
}

.summary-done {
  background: var(--accent-light);
  color: var(--text-primary);
  flex-direction: column;
  gap: 6px;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--accent);
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
  font-size: 16px;
  line-height: 1.8;
  color: var(--text-primary);
  word-break: break-word;
}

.article-content :deep(p) {
  margin-bottom: 1.2em;
}

.article-content :deep(img) {
  max-width: 100%;
  border-radius: var(--radius-md);
  margin: 16px 0;
}

.article-content :deep(a) {
  color: var(--accent);
}

.article-content :deep(blockquote) {
  border-left: 3px solid var(--accent);
  padding-left: 16px;
  color: var(--text-secondary);
  margin: 16px 0;
}
</style>
