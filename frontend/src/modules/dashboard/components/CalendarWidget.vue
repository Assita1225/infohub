<template>
  <div class="calendar-widget">
    <div class="cal-header">
      <el-button text size="small" @click="changeMonth(-1)">&lt;</el-button>
      <span class="cal-title">{{ year }}年{{ month }}月</span>
      <el-button text size="small" @click="changeMonth(1)">&gt;</el-button>
    </div>
    <div class="cal-weekdays">
      <span v-for="d in weekLabels" :key="d">{{ d }}</span>
    </div>
    <div class="cal-days">
      <span
        v-for="(day, idx) in days"
        :key="idx"
        :class="{
          'other-month': !day.current,
          'today': day.isToday,
        }"
      >
        {{ day.num }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const weekLabels = ['日', '一', '二', '三', '四', '五', '六']
const now = new Date()
const year = ref(now.getFullYear())
const month = ref(now.getMonth() + 1)

function changeMonth(delta) {
  let m = month.value + delta
  let y = year.value
  if (m < 1) { m = 12; y-- }
  if (m > 12) { m = 1; y++ }
  month.value = m
  year.value = y
}

const days = computed(() => {
  const y = year.value
  const m = month.value - 1
  const firstDay = new Date(y, m, 1).getDay()
  const daysInMonth = new Date(y, m + 1, 0).getDate()
  const daysInPrev = new Date(y, m, 0).getDate()
  const today = new Date()

  const result = []

  for (let i = firstDay - 1; i >= 0; i--) {
    result.push({ num: daysInPrev - i, current: false, isToday: false })
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const isToday = d === today.getDate() && m === today.getMonth() && y === today.getFullYear()
    result.push({ num: d, current: true, isToday })
  }

  const remaining = 42 - result.length
  for (let d = 1; d <= remaining; d++) {
    result.push({ num: d, current: false, isToday: false })
  }

  return result
})
</script>

<style scoped>
.calendar-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px;
  user-select: none;
}

.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.cal-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.cal-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.cal-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 12px;
  gap: 2px;
  flex: 1;
}

.cal-days span {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  color: var(--text-primary);
}

.cal-days .other-month {
  color: var(--border);
}

.cal-days .today {
  background: var(--accent);
  color: #fff;
  font-weight: 700;
}
</style>
