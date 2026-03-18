<template>
  <div class="dashboard-page">
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
        <div class="widget-label">{{ widgetNames[item.i] || item.i }}</div>
        <ClockWidget    v-if="item.i === 'clock'" />
        <CalendarWidget v-else-if="item.i === 'calendar'" />
        <TodoWidget     v-else-if="item.i === 'todo'" />
        <WeatherWidget  v-else-if="item.i === 'weather'" />
      </grid-item>
    </grid-layout>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { GridLayout, GridItem } from 'grid-layout-plus'
import { ElMessage } from 'element-plus'
import { getWidgets, saveWidgets } from '../api'
import ClockWidget from '../components/ClockWidget.vue'
import CalendarWidget from '../components/CalendarWidget.vue'
import TodoWidget from '../components/TodoWidget.vue'
import WeatherWidget from '../components/WeatherWidget.vue'

const widgetNames = {
  clock: '时钟',
  calendar: '日历',
  todo: '待办事项',
  weather: '天气',
}

const layout = ref([])
let saveTimer = null

async function loadLayout() {
  try {
    const res = await getWidgets()
    layout.value = res.data
  } catch {
    ElMessage.error('加载布局失败')
  }
}

function onLayoutUpdated(newLayout) {
  // 防抖：拖拽结束后 800ms 自动保存
  clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    try {
      const data = newLayout.map(({ i, x, y, w, h }) => ({ i, x, y, w, h }))
      await saveWidgets(data)
    } catch { /* 静默 */ }
  }, 800)
}

onMounted(loadLayout)
</script>

<style scoped>
.dashboard-page {
  min-height: calc(100vh - 60px);
}

.widget-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.widget-label {
  font-size: 12px;
  color: #909399;
  padding: 8px 12px 0;
  user-select: none;
}
</style>
