<template>
  <div class="clock-widget">
    <div class="time">{{ time }}</div>
    <div class="date">{{ date }}</div>
    <div class="weekday">{{ weekday }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const time = ref('')
const date = ref('')
const weekday = ref('')
let timer = null

const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']

function tick() {
  const now = new Date()
  time.value = now.toLocaleTimeString('zh-CN', { hour12: false })
  date.value = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`
  weekday.value = weekdays[now.getDay()]
}

onMounted(() => {
  tick()
  timer = setInterval(tick, 1000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.clock-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  user-select: none;
}

.time {
  font-family: var(--font-display);
  font-size: 42px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
  line-height: 1.2;
}

.date {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.weekday {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}
</style>
