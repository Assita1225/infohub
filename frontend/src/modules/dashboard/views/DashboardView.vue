<template>
  <div class="dashboard-page">
    <div class="dashboard-header">
      <h2 class="greeting">{{ greeting }}</h2>
      <el-button round size="small" @click="showSelector = true">
        <el-icon><Plus /></el-icon>
        <span>添加微件</span>
      </el-button>
    </div>

    <grid-layout
      v-if="layout.length"
      v-model:layout="layout"
      :col-num="6"
      :row-height="36"
      :margin="[16, 16]"
      :is-draggable="true"
      :is-resizable="true"
      @layout-updated="onLayoutUpdated"
    >
      <grid-item
        v-for="item in layout"
        :key="item.i"
        :i="item.i"
        :x="item.x"
        :y="item.y"
        :w="item.w"
        :h="item.h"
        class="widget-card"
      >
        <div class="widget-top-bar">
          <span class="widget-label">{{ widgetNames[item.i] || item.i }}</span>
          <el-button
            text
            size="small"
            class="widget-remove-btn"
            @click.stop="handleRemove(item.i)"
          >
            <el-icon :size="14"><Close /></el-icon>
          </el-button>
        </div>
        <ClockWidget       v-if="item.i === 'clock'" />
        <CalendarWidget    v-else-if="item.i === 'calendar'" />
        <TodoWidget        v-else-if="item.i === 'todo'" />
        <WeatherWidget     v-else-if="item.i === 'weather'" />
        <PomodoroWidget    v-else-if="item.i === 'pomodoro'" />
        <CountdownWidget   v-else-if="item.i === 'countdown'" />
        <RecentNotesWidget v-else-if="item.i === 'recent_notes'" />
      </grid-item>
    </grid-layout>

    <div v-if="!loading && layout.length === 0" class="empty-state">
      <el-icon :size="48" color="var(--text-muted)"><Monitor /></el-icon>
      <p>暂无微件，点击右上角"添加微件"开始配置</p>
    </div>

    <WidgetSelector
      v-model="showSelector"
      :active-widgets="activeWidgetIds"
      @add="handleAddWidget"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { GridLayout, GridItem } from 'grid-layout-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Monitor, Plus, Close } from '@element-plus/icons-vue'
import { getWidgets, saveWidgets, getActiveWidgets, saveActiveWidgets } from '../api'
import ClockWidget from '../components/ClockWidget.vue'
import CalendarWidget from '../components/CalendarWidget.vue'
import TodoWidget from '../components/TodoWidget.vue'
import WeatherWidget from '../components/WeatherWidget.vue'
import PomodoroWidget from '../components/PomodoroWidget.vue'
import CountdownWidget from '../components/CountdownWidget.vue'
import RecentNotesWidget from '../components/RecentNotesWidget.vue'
import WidgetSelector from '../components/WidgetSelector.vue'

const widgetNames = {
  clock: '时钟',
  calendar: '日历',
  todo: '待办事项',
  weather: '天气',
  pomodoro: '番茄钟',
  countdown: '倒计时',
  recent_notes: '最近笔记',
}

// 新微件的默认尺寸
const defaultSizes = {
  clock:        { w: 2, h: 5 },
  calendar:     { w: 2, h: 8 },
  todo:         { w: 2, h: 8 },
  weather:      { w: 2, h: 5 },
  pomodoro:     { w: 2, h: 8 },
  countdown:    { w: 2, h: 8 },
  recent_notes: { w: 2, h: 7 },
}

const layout = ref([])
const activeWidgetIds = ref([])
const loading = ref(true)
const showSelector = ref(false)
let saveTimer = null

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了，注意休息'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

async function loadLayout() {
  loading.value = true
  try {
    const [widgetRes, activeRes] = await Promise.all([
      getWidgets(),
      getActiveWidgets(),
    ])
    activeWidgetIds.value = activeRes.data
    // 只展示活跃微件中存在的布局项
    const activeSet = new Set(activeRes.data)
    layout.value = widgetRes.data.filter(item => activeSet.has(item.i))
  } catch {
    ElMessage.error('加载布局失败')
  } finally {
    loading.value = false
  }
}

function onLayoutUpdated(newLayout) {
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      const data = newLayout.map(({ i, x, y, w, h }) => ({ i, x, y, w, h }))
      await saveWidgets(data)
    } catch { /* 静默 */ }
  }, 800)
}

async function handleAddWidget(id) {
  if (activeWidgetIds.value.includes(id)) return
  // 更新活跃列表
  activeWidgetIds.value.push(id)
  await saveActiveWidgets(activeWidgetIds.value).catch(() => {})

  // 找一个空位（放在最底部）
  const maxY = layout.value.reduce((max, item) => Math.max(max, item.y + item.h), 0)
  const size = defaultSizes[id] || { w: 2, h: 5 }
  const newItem = { i: id, x: 0, y: maxY, ...size }
  layout.value.push(newItem)

  // 保存布局
  const data = layout.value.map(({ i, x, y, w, h }) => ({ i, x, y, w, h }))
  await saveWidgets(data).catch(() => {})
  ElMessage.success(`已添加「${widgetNames[id]}」`)
}

async function handleRemove(id) {
  try {
    await ElMessageBox.confirm('确定移除此微件？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return // 取消
  }

  // 从活跃列表移除
  activeWidgetIds.value = activeWidgetIds.value.filter(w => w !== id)
  await saveActiveWidgets(activeWidgetIds.value).catch(() => {})

  // 从布局移除
  layout.value = layout.value.filter(item => item.i !== id)
  const data = layout.value.map(({ i, x, y, w, h }) => ({ i, x, y, w, h }))
  await saveWidgets(data).catch(() => {})
  ElMessage.success(`已移除「${widgetNames[id]}」`)
}

onMounted(loadLayout)
</script>

<style scoped>
.dashboard-page {
  min-height: calc(100vh - 120px);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.greeting {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.widget-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s;
}

.widget-card:hover {
  box-shadow: var(--shadow-md);
}

.widget-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px 0;
}

.widget-label {
  font-size: 12px;
  color: var(--text-muted);
  user-select: none;
}

.widget-remove-btn {
  opacity: 0;
  transition: opacity 0.2s;
  padding: 2px;
  color: var(--text-muted);
}

.widget-card:hover .widget-remove-btn {
  opacity: 1;
}

.widget-remove-btn:hover {
  color: #f56c6c;
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
</style>
