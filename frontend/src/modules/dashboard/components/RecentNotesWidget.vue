<template>
  <div class="recent-notes-widget">
    <div class="rn-header">
      <span class="rn-title">最近笔记</span>
    </div>

    <div class="rn-list">
      <div
        v-for="note in notes"
        :key="note._id"
        class="rn-item"
        @click="goToNote(note._id)"
      >
        <div class="rn-note-title">{{ note.title || '无标题' }}</div>
        <div class="rn-time">{{ formatTime(note.updated_at) }}</div>
      </div>
      <div v-if="!loading && notes.length === 0" class="rn-empty">
        <span>暂无笔记</span>
      </div>
    </div>

    <div class="rn-footer">
      <router-link to="/notes" class="rn-link">查看全部</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getRecentNotes } from '../api'

const router = useRouter()
const notes = ref([])
const loading = ref(true)

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function goToNote(id) {
  router.push(`/notes/${id}`)
}

async function loadNotes() {
  loading.value = true
  try {
    const res = await getRecentNotes()
    notes.value = res.data?.items || res.data || []
  } catch { /* 静默 */ }
  loading.value = false
}

onMounted(loadNotes)
</script>

<style scoped>
.recent-notes-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 12px;
}

.rn-header {
  margin-bottom: 10px;
}

.rn-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.rn-list {
  flex: 1;
  overflow-y: auto;
}

.rn-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 4px;
  border-bottom: 1px solid var(--border-light);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
}

.rn-item:hover {
  background: var(--bg-primary);
}

.rn-note-title {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 8px;
}

.rn-time {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}

.rn-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 13px;
  padding: 20px 0;
}

.rn-footer {
  padding-top: 8px;
  text-align: center;
}

.rn-link {
  font-size: 12px;
  color: var(--accent);
  text-decoration: none;
}

.rn-link:hover {
  color: var(--accent-hover);
}
</style>
