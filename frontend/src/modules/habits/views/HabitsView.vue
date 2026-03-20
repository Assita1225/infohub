<template>
  <div class="habits-page">
    <p class="page-subtitle">坚持的力量</p>

    <!-- 顶部操作栏 -->
    <div class="habits-toolbar">
      <div class="toolbar-left">
        <span class="habit-count">共 {{ habits.length }} 个习惯</span>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon> 添加习惯
        </el-button>
      </div>
    </div>

    <!-- 习惯列表 -->
    <div class="habits-list" v-loading="loading">
      <div v-for="habit in habits" :key="habit._id" class="habit-card card">
        <!-- 头部：icon + 名称 + 打卡按钮 + 连续天数 -->
        <div class="habit-header">
          <div class="habit-info">
            <span class="habit-icon">{{ habit.icon }}</span>
            <span class="habit-name">{{ habit.name }}</span>
            <span v-if="getStreak(habit._id) > 0" class="habit-streak">
              🔥 {{ getStreak(habit._id) }} 天
            </span>
          </div>
          <div class="habit-actions">
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, habit)">
              <el-button text size="small" class="more-btn">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <button
              :class="['checkin-btn', { checked: habit.checked_today, animating: animatingId === habit._id }]"
              :style="habit.checked_today ? { background: habit.color, borderColor: habit.color } : {}"
              @click="toggleCheckIn(habit)"
            >
              <el-icon v-if="habit.checked_today" :size="22"><Check /></el-icon>
              <el-icon v-else :size="22"><CircleCheck /></el-icon>
            </button>
          </div>
        </div>

        <!-- 热力图 -->
        <div class="heatmap-wrapper">
          <div :ref="(el) => { if (el) heatmapRefs[habit._id] = el }" class="heatmap-chart" />
        </div>
      </div>

      <div v-if="!loading && habits.length === 0" class="empty-state">
        <el-icon :size="48" color="var(--text-muted)"><Calendar /></el-icon>
        <p>还没有习惯，添加一个开始打卡吧</p>
        <el-button type="primary" @click="showAddDialog = true">添加习惯</el-button>
      </div>
    </div>

    <!-- 底部统计卡片 -->
    <div v-if="stats.length > 0" class="stats-section">
      <h3 class="stats-title">打卡统计</h3>
      <div class="stats-grid">
        <div v-for="s in stats" :key="s.habit_id" class="stat-card card">
          <div class="stat-header">
            <span class="stat-icon">{{ s.icon }}</span>
            <span class="stat-name">{{ s.name }}</span>
          </div>
          <div class="stat-items">
            <div class="stat-item">
              <span class="stat-value">{{ s.total }}</span>
              <span class="stat-label">总打卡</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ s.max_streak }}</span>
              <span class="stat-label">最长连续</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ s.month_rate }}%</span>
              <span class="stat-label">本月完成</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加 / 编辑弹窗 -->
    <el-dialog v-model="showAddDialog" :title="editingHabit ? '编辑习惯' : '添加习惯'" width="400px" :append-to-body="true">
      <el-form :model="form" label-position="top">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如：阅读、运动、学习" maxlength="20" />
        </el-form-item>
        <el-form-item label="图标（emoji）">
          <div class="emoji-picker">
            <span
              v-for="e in emojiOptions"
              :key="e"
              :class="['emoji-option', { selected: form.icon === e }]"
              @click="form.icon = e"
            >{{ e }}</span>
          </div>
        </el-form-item>
        <el-form-item label="颜色">
          <div class="color-picker">
            <span
              v-for="c in colorOptions"
              :key="c"
              :class="['color-option', { selected: form.color === c }]"
              :style="{ background: c }"
              @click="form.color = c"
            />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { Plus, Check, CircleCheck, Calendar, MoreFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import {
  getHabits, createHabit, updateHabit, deleteHabit,
  checkIn, cancelCheckIn, getHistory, getStats,
} from '../api'

const loading = ref(false)
const habits = ref([])
const stats = ref([])
const heatmapRefs = reactive({})
const chartInstances = {}
const animatingId = ref(null)

const showAddDialog = ref(false)
const editingHabit = ref(null)
const saving = ref(false)
const form = reactive({ name: '', icon: '📖', color: '#C45A3C' })

const emojiOptions = ['📖', '🏃', '💻', '🧘', '✍️', '🎵', '💪', '🌱', '🎨', '💊', '🛌', '💧']
const colorOptions = ['#C45A3C', '#E8A735', '#4CAF50', '#2196F3', '#9C27B0', '#FF5722', '#009688', '#607D8B']

function getStreak(habitId) {
  const s = stats.value.find(s => s.habit_id === habitId)
  return s ? s.streak : 0
}

async function loadAll() {
  loading.value = true
  try {
    const [habitsRes, statsRes] = await Promise.all([getHabits(), getStats()])
    habits.value = habitsRes.data
    stats.value = statsRes.data
    await nextTick()
    for (const h of habits.value) {
      await loadHeatmap(h)
    }
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function loadHeatmap(habit) {
  const now = new Date()
  const year = now.getFullYear()
  try {
    const res = await getHistory(habit._id, year)
    const dates = res.data || []
    renderHeatmap(habit, dates)
  } catch {
    // silent
  }
}

function renderHeatmap(habit, dates) {
  const el = heatmapRefs[habit._id]
  if (!el) return

  if (chartInstances[habit._id]) {
    chartInstances[habit._id].dispose()
  }

  const chart = echarts.init(el)
  chartInstances[habit._id] = chart

  // 生成最近6个月的日期范围
  const now = new Date()
  const end = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const start = new Date(end)
  start.setMonth(start.getMonth() - 5)
  start.setDate(1)

  const dateSet = new Set(dates)
  const data = []
  const d = new Date(start)
  while (d <= end) {
    const ds = d.toISOString().slice(0, 10)
    data.push([ds, dateSet.has(ds) ? 1 : 0])
    d.setDate(d.getDate() + 1)
  }

  const startStr = start.toISOString().slice(0, 10)
  const endStr = end.toISOString().slice(0, 10)

  const option = {
    tooltip: {
      formatter(params) {
        return `${params.value[0]}<br/>${params.value[1] ? '✅ 已打卡' : '未打卡'}`
      },
    },
    visualMap: {
      show: false,
      min: 0,
      max: 1,
      inRange: {
        color: ['#ebedf0', habit.color],
      },
    },
    calendar: {
      top: 8,
      left: 36,
      right: 8,
      bottom: 4,
      cellSize: [14, 14],
      range: [startStr, endStr],
      itemStyle: {
        borderWidth: 2,
        borderColor: 'var(--bg-card, #fff)',
        borderRadius: 2,
      },
      yearLabel: { show: false },
      dayLabel: {
        firstDay: 1,
        nameMap: ['日', '一', '二', '三', '四', '五', '六'],
        fontSize: 10,
        color: '#999',
      },
      monthLabel: {
        fontSize: 10,
        color: '#999',
      },
      splitLine: { show: false },
    },
    series: [{
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data,
    }],
  }

  chart.setOption(option)
}

async function toggleCheckIn(habit) {
  try {
    if (habit.checked_today) {
      await cancelCheckIn(habit._id)
      habit.checked_today = false
      ElMessage.success('已取消打卡')
    } else {
      await checkIn(habit._id)
      habit.checked_today = true
      animatingId.value = habit._id
      setTimeout(() => { animatingId.value = null }, 600)
      ElMessage.success('打卡成功！')
    }
    // 刷新统计和热力图
    const [statsRes] = await Promise.all([getStats(), loadHeatmap(habit)])
    stats.value = statsRes.data
  } catch {
    ElMessage.error('操作失败')
  }
}

function handleCommand(cmd, habit) {
  if (cmd === 'edit') {
    editingHabit.value = habit
    form.name = habit.name
    form.icon = habit.icon
    form.color = habit.color
    showAddDialog.value = true
  } else if (cmd === 'delete') {
    ElMessageBox.confirm(`确定删除「${habit.name}」？所有打卡记录将一并删除。`, '删除习惯', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(async () => {
      try {
        await deleteHabit(habit._id)
        ElMessage.success('已删除')
        loadAll()
      } catch {
        ElMessage.error('删除失败')
      }
    }).catch(() => {})
  }
}

async function handleSave() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入名称')
    return
  }
  saving.value = true
  try {
    if (editingHabit.value) {
      await updateHabit(editingHabit.value._id, { name: form.name, icon: form.icon, color: form.color })
      ElMessage.success('已更新')
    } else {
      await createHabit({ name: form.name, icon: form.icon, color: form.color })
      ElMessage.success('已添加')
    }
    showAddDialog.value = false
    editingHabit.value = null
    form.name = ''
    form.icon = '📖'
    form.color = '#C45A3C'
    loadAll()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function handleResize() {
  Object.values(chartInstances).forEach(c => c.resize())
}

onMounted(() => {
  loadAll()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  Object.values(chartInstances).forEach(c => c.dispose())
})
</script>

<style scoped>
.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 16px;
}

.habits-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.habit-count {
  font-size: 13px;
  color: var(--text-muted);
}

.habits-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 习惯卡片 */
.habit-card {
  padding: 20px;
}

.habit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.habit-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.habit-icon {
  font-size: 24px;
}

.habit-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.habit-streak {
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  padding: 2px 10px;
  border-radius: 12px;
}

.habit-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.more-btn {
  color: var(--text-muted);
}

/* 打卡按钮 */
.checkin-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid var(--border);
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-muted);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.checkin-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  transform: scale(1.05);
}

.checkin-btn.checked {
  color: #fff;
  transform: scale(1);
}

.checkin-btn.checked:hover {
  opacity: 0.85;
  color: #fff;
}

.checkin-btn.animating {
  animation: checkin-pop 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes checkin-pop {
  0% { transform: scale(1); }
  40% { transform: scale(1.3); }
  100% { transform: scale(1); }
}

/* 热力图 */
.heatmap-wrapper {
  overflow-x: auto;
}

.heatmap-chart {
  width: 100%;
  height: 140px;
  min-width: 680px;
}

/* 统计 */
.stats-section {
  margin-top: 32px;
}

.stats-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.stat-card {
  padding: 16px 20px;
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.stat-icon {
  font-size: 20px;
}

.stat-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-items {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* emoji & color picker */
.emoji-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.emoji-option {
  font-size: 24px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 8px;
  border: 2px solid transparent;
  transition: border-color 0.15s;
}

.emoji-option.selected {
  border-color: var(--accent);
  background: var(--bg-secondary);
}

.color-picker {
  display: flex;
  gap: 8px;
}

.color-option {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  border: 3px solid transparent;
  transition: border-color 0.15s, transform 0.15s;
}

.color-option:hover {
  transform: scale(1.1);
}

.color-option.selected {
  border-color: var(--text-primary);
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

@media (max-width: 767px) {
  .habits-toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .toolbar-right {
    display: flex;
    justify-content: flex-end;
  }
  .heatmap-chart {
    min-width: 600px;
  }
  .stat-items {
    gap: 16px;
  }
}
</style>
