<template>
  <!-- FAB 悬浮按钮 -->
  <div
    v-show="!chatStore.isPanelOpen"
    class="chat-fab"
    @click="chatStore.togglePanel"
  >
    <el-icon :size="24"><ChatDotRound /></el-icon>
  </div>

  <!-- 对话面板 -->
  <transition name="chat-slide">
    <div v-show="chatStore.isPanelOpen" class="chat-panel">
      <!-- 顶部栏 -->
      <div class="chat-header">
        <div class="chat-header-left">
          <span class="chat-context-label">{{ contextLabel }}</span>
        </div>
        <div class="chat-header-actions">
          <el-tooltip content="历史会话" placement="top">
            <el-icon class="header-btn" @click="showSessions = !showSessions">
              <Clock />
            </el-icon>
          </el-tooltip>
          <el-tooltip content="新建对话" placement="top">
            <el-icon class="header-btn" @click="handleNewSession">
              <Plus />
            </el-icon>
          </el-tooltip>
          <el-icon class="header-btn" @click="chatStore.togglePanel">
            <Close />
          </el-icon>
        </div>
      </div>

      <!-- 会话列表（可折叠） -->
      <div v-if="showSessions" class="session-list">
        <div
          v-for="session in chatStore.sessions"
          :key="session._id"
          class="session-item"
          :class="{ active: session._id === chatStore.currentSessionId }"
          @click="handleSwitchSession(session._id)"
        >
          <div class="session-info">
            <span class="session-title">{{ session.title }}</span>
            <span class="session-date">{{ formatDate(session.updated_at) }}</span>
          </div>
          <el-icon
            class="session-delete"
            @click.stop="chatStore.removeSession(session._id)"
          >
            <Delete />
          </el-icon>
        </div>
        <div v-if="chatStore.sessions.length === 0" class="session-empty">
          暂无历史会话
        </div>
      </div>

      <!-- 消息区域 -->
      <div ref="messageListRef" class="message-list">
        <!-- 预设建议（无消息时显示） -->
        <div v-if="chatStore.messages.length === 0" class="preset-suggestions">
          <p class="preset-hint">你可以试试问我：</p>
          <button
            v-for="(q, i) in presetQuestions"
            :key="i"
            class="preset-btn"
            @click="handlePreset(q)"
          >
            {{ q }}
          </button>
        </div>

        <!-- 消息列表 -->
        <div
          v-for="(msg, idx) in chatStore.messages"
          :key="idx"
          class="message-row"
          :class="msg.role"
        >
          <div class="message-bubble" :class="msg.role">
            <div v-if="msg.role === 'assistant'" class="assistant-content" v-html="renderMarkdown(msg.content)"></div>
            <div v-else class="user-content">{{ msg.content }}</div>
          </div>
        </div>

        <!-- 流式加载指示 -->
        <div v-if="chatStore.isStreaming && lastAssistantContent === ''" class="message-row assistant">
          <div class="message-bubble assistant">
            <span class="typing-indicator">思考中...</span>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="chat-input-area">
        <el-input
          v-model="inputText"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 3 }"
          placeholder="输入消息..."
          :disabled="chatStore.isStreaming"
          @keydown="handleKeydown"
        />
        <el-button
          type="primary"
          :icon="Promotion"
          circle
          size="small"
          :disabled="!inputText.trim() || chatStore.isStreaming"
          :loading="chatStore.isStreaming"
          @click="handleSend"
        />
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { getArticle } from '@/modules/rss/api'
import {
  ChatDotRound, Clock, Plus, Close, Delete, Promotion,
} from '@element-plus/icons-vue'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'

const route = useRoute()
const chatStore = useChatStore()

const inputText = ref('')
const showSessions = ref(false)
const messageListRef = ref(null)

// ── 上下文感知 ──

const contextLabel = computed(() => {
  const ctx = chatStore.currentContext
  if (ctx.article_title) {
    return `关联：《${ctx.article_title}》`
  }
  const pageLabels = {
    rss: 'RSS 订阅',
    news: '新闻广场',
    trending: '热度榜',
  }
  return pageLabels[ctx.page] || '通用对话'
})

watch(
  () => route.path,
  async (path) => {
    if (path.startsWith('/rss/article/')) {
      const articleId = route.params.id
      try {
        const res = await getArticle(articleId)
        const article = res.data
        chatStore.setContext({
          page: 'rss',
          article_id: articleId,
          article_title: article.title,
          article_content: (article.content || '')
            .replace(/<[^>]*>/g, '')
            .substring(0, 3000),
        })
      } catch {
        chatStore.setContext({ page: 'rss' })
      }
    } else if (path.startsWith('/rss')) {
      chatStore.setContext({ page: 'rss' })
    } else if (path.startsWith('/news')) {
      chatStore.setContext({ page: 'news' })
    } else if (path.startsWith('/trending')) {
      chatStore.setContext({ page: 'trending' })
    } else {
      chatStore.setContext({ page: 'general' })
    }
  },
  { immediate: true },
)

// ── 预设问题 ──

const presetQuestions = computed(() => {
  const ctx = chatStore.currentContext
  if (ctx.article_title) {
    return ['总结这篇文章', '这篇文章的核心观点是什么', '有哪些值得关注的信息']
  }
  if (ctx.page === 'trending') {
    return ['今天最值得关注的趋势是什么', '帮我整理最近阅读的内容']
  }
  return ['帮我整理最近阅读的内容']
})

// ── 消息处理 ──

const lastAssistantContent = computed(() => {
  const msgs = chatStore.messages
  if (msgs.length === 0) return ''
  const last = msgs[msgs.length - 1]
  return last.role === 'assistant' ? last.content : ''
})

function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.isStreaming) return
  inputText.value = ''
  chatStore.sendMessage(text)
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handlePreset(question) {
  inputText.value = question
  handleSend()
}

// ── 会话操作 ──

function handleNewSession() {
  chatStore.startNewSession()
  showSessions.value = false
}

async function handleSwitchSession(id) {
  await chatStore.loadSession(id)
  showSessions.value = false
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const mins = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hours}:${mins}`
}

// ── Markdown 渲染 ──

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

// ── 自动滚动 ──

watch(
  () => {
    const msgs = chatStore.messages
    return msgs.length > 0 ? msgs[msgs.length - 1].content : ''
  },
  () => {
    nextTick(() => {
      const el = messageListRef.value
      if (el) el.scrollTop = el.scrollHeight
    })
  },
)
</script>

<style scoped>
/* ── FAB 按钮 ── */
.chat-fab {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(196, 90, 60, 0.3);
  z-index: 9999;
  transition: transform 0.2s, box-shadow 0.2s;
}
.chat-fab:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 20px rgba(196, 90, 60, 0.4);
}

/* ── 面板滑入动画 ── */
.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(16px);
}

/* ── 对话面板 ── */
.chat-panel {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 380px;
  height: 560px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  z-index: 9999;
  overflow: hidden;
  border: 1px solid var(--border-light);
}

/* ── 顶部栏 ── */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-primary);
  flex-shrink: 0;
}
.chat-context-label {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}
.chat-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-btn {
  font-size: 18px;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.2s;
}
.header-btn:hover {
  color: var(--accent);
}

/* ── 会话列表 ── */
.session-list {
  max-height: 200px;
  overflow-y: auto;
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}
.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  cursor: pointer;
  transition: background 0.15s;
}
.session-item:hover {
  background: var(--bg-hover);
}
.session-item.active {
  background: var(--accent-light);
}
.session-info {
  flex: 1;
  min-width: 0;
}
.session-title {
  font-size: 13px;
  color: var(--text-primary);
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.session-date {
  font-size: 11px;
  color: var(--text-muted);
}
.session-delete {
  font-size: 14px;
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  margin-left: 8px;
}
.session-delete:hover {
  color: #f56c6c;
}
.session-empty {
  padding: 16px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}

/* ── 消息区域 ── */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* 预设建议 */
.preset-suggestions {
  text-align: center;
  padding: 40px 16px 16px;
}
.preset-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 12px;
}
.preset-btn {
  display: inline-block;
  margin: 4px;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.preset-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* 消息行 */
.message-row {
  display: flex;
  margin-bottom: 12px;
}
.message-row.user {
  justify-content: flex-end;
}
.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}
.message-bubble.user {
  background: var(--accent-light);
  color: var(--text-primary);
  border-bottom-right-radius: 2px;
}
.message-bubble.assistant {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-bottom-left-radius: 2px;
}

.assistant-content :deep(code) {
  background: var(--bg-hover);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 12px;
}

.typing-indicator {
  color: var(--text-muted);
  font-style: italic;
}

/* ── 输入区 ── */
.chat-input-area {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-light);
  background: var(--bg-card);
  flex-shrink: 0;
}
.chat-input-area :deep(.el-textarea__inner) {
  resize: none;
  box-shadow: none;
}

@media (max-width: 767px) {
  .chat-panel {
    right: 0;
    bottom: 0;
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }
  .chat-fab {
    right: 16px;
    bottom: 16px;
  }
}
</style>
