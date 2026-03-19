<template>
  <div class="countdown-widget">
    <div class="countdown-header">
      <span class="countdown-title">倒计时</span>
      <el-button text size="small" @click="showAdd = true">
        <el-icon><Plus /></el-icon>
      </el-button>
    </div>

    <div class="countdown-list">
      <div v-for="item in countdowns" :key="item._id" class="countdown-item">
        <div class="countdown-name">{{ item.name }}</div>
        <div class="countdown-remaining" :class="{ expired: isExpired(item.target_date) }">
          {{ formatRemaining(item.target_date) }}
        </div>
        <el-button text size="small" class="countdown-del" @click="handleDelete(item._id)">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
      <div v-if="countdowns.length === 0" class="countdown-empty">
        <span>暂无倒计时</span>
      </div>
    </div>

    <!-- 添加对话框 -->
    <el-dialog v-model="showAdd" title="添加倒计时" width="360px" append-to-body>
      <el-form label-position="top" @submit.prevent="handleAdd">
        <el-form-item label="事件名称">
          <el-input v-model="newName" placeholder="如：毕业答辩" />
        </el-form-item>
        <el-form-item label="目标日期">
          <el-date-picker
            v-model="newDate"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd = false">取消</el-button>
        <el-button type="primary" @click="handleAdd" :disabled="!newName.trim() || !newDate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getCountdowns, createCountdown, deleteCountdown } from '../api'

const countdowns = ref([])
const showAdd = ref(false)
const newName = ref('')
const newDate = ref('')
let tickTimer = null

function isExpired(target) {
  return new Date(target).getTime() <= Date.now()
}

function formatRemaining(target) {
  const diff = new Date(target).getTime() - Date.now()
  if (diff <= 0) return '已到期'
  const days = Math.floor(diff / 86400000)
  const hours = Math.floor((diff % 86400000) / 3600000)
  const mins = Math.floor((diff % 3600000) / 60000)
  if (days > 0) return `${days} 天 ${hours} 时`
  return `${hours} 时 ${mins} 分`
}

async function loadCountdowns() {
  try {
    const res = await getCountdowns()
    countdowns.value = res.data
  } catch { /* 静默 */ }
}

async function handleAdd() {
  const name = newName.value.trim()
  if (!name || !newDate.value) return
  try {
    const res = await createCountdown(name, newDate.value)
    countdowns.value.push(res.data)
    countdowns.value.sort((a, b) => new Date(a.target_date) - new Date(b.target_date))
    newName.value = ''
    newDate.value = ''
    showAdd.value = false
  } catch {
    ElMessage.error('添加失败')
  }
}

async function handleDelete(id) {
  try {
    await deleteCountdown(id)
    countdowns.value = countdowns.value.filter(c => c._id !== id)
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadCountdowns()
  // 每分钟刷新显示
  tickTimer = setInterval(() => {
    countdowns.value = [...countdowns.value]
  }, 60000)
})

onBeforeUnmount(() => {
  clearInterval(tickTimer)
})
</script>

<style scoped>
.countdown-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 12px;
}

.countdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.countdown-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.countdown-list {
  flex: 1;
  overflow-y: auto;
}

.countdown-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
  gap: 8px;
}

.countdown-name {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.countdown-remaining {
  font-size: 12px;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.countdown-remaining.expired {
  color: var(--text-muted);
}

.countdown-del {
  opacity: 0;
  transition: opacity 0.2s;
}

.countdown-item:hover .countdown-del {
  opacity: 1;
}

.countdown-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 13px;
  padding: 20px 0;
}
</style>
