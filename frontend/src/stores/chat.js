import { ref } from 'vue'
import { defineStore } from 'pinia'
import {
  getSessions as apiGetSessions,
  getSession as apiGetSession,
  deleteSession as apiDeleteSession,
  sendMessageStream,
} from '@/modules/chat/api'

export const useChatStore = defineStore('chat', () => {
  // ── 状态 ──
  const sessions = ref([])
  const currentSessionId = ref(null)
  const messages = ref([])
  const isStreaming = ref(false)
  const isPanelOpen = ref(false)
  const currentContext = ref({ page: 'general' })

  // ── 会话管理 ──

  async function loadSessions() {
    try {
      const res = await apiGetSessions()
      sessions.value = res.data || []
    } catch {
      sessions.value = []
    }
  }

  async function loadSession(id) {
    try {
      const res = await apiGetSession(id)
      const session = res.data
      currentSessionId.value = session._id
      messages.value = session.messages || []
      // 恢复上下文信息
      if (session.context) {
        currentContext.value = session.context
      }
    } catch {
      // 会话不存在，重置
      startNewSession()
    }
  }

  async function removeSession(id) {
    try {
      await apiDeleteSession(id)
      sessions.value = sessions.value.filter((s) => s._id !== id)
      // 如果删除的是当前会话，重置
      if (currentSessionId.value === id) {
        startNewSession()
      }
    } catch {
      // ignore
    }
  }

  function startNewSession() {
    currentSessionId.value = null
    messages.value = []
  }

  // ── 上下文 ──

  function setContext(ctx) {
    currentContext.value = ctx
  }

  // ── 发送消息 ──

  async function sendMessage(content) {
    if (!content.trim() || isStreaming.value) return

    isStreaming.value = true

    // 添加用户消息
    messages.value.push({
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    })

    // 添加 assistant 占位
    const assistantIdx = messages.value.length
    messages.value.push({
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    })

    const payload = {
      content,
      session_id: currentSessionId.value || undefined,
      // 仅在创建新会话时发送上下文
      context: currentSessionId.value ? undefined : currentContext.value,
    }

    await sendMessageStream(payload, {
      onChunk({ chunk, session_id }) {
        // 首次收到 session_id → 记录
        if (!currentSessionId.value && session_id) {
          currentSessionId.value = session_id
        }
        messages.value[assistantIdx].content += chunk
      },
      onDone() {
        isStreaming.value = false
        loadSessions() // 刷新会话列表（标题可能已更新）
      },
      onError(err) {
        isStreaming.value = false
        messages.value[assistantIdx].content += `\n\n[错误：${err}]`
      },
    })
  }

  // ── 面板 ──

  function togglePanel() {
    isPanelOpen.value = !isPanelOpen.value
    if (isPanelOpen.value && sessions.value.length === 0) {
      loadSessions()
    }
  }

  return {
    sessions,
    currentSessionId,
    messages,
    isStreaming,
    isPanelOpen,
    currentContext,
    loadSessions,
    loadSession,
    removeSession,
    startNewSession,
    setContext,
    sendMessage,
    togglePanel,
  }
})
