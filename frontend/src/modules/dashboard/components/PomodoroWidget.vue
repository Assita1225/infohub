<template>
  <div class="pomodoro-widget">
    <div class="pomodoro-ring">
      <svg viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="44" class="ring-bg" />
        <circle
          cx="50" cy="50" r="44"
          class="ring-progress"
          :class="{ 'is-break': isBreak }"
          :style="{ strokeDashoffset: dashOffset }"
        />
      </svg>
      <div class="ring-content">
        <span class="time-display">{{ displayTime }}</span>
        <span class="phase-label">{{ isBreak ? '休息' : '工作' }}</span>
      </div>
    </div>

    <div class="pomodoro-controls">
      <el-button
        size="small"
        :type="running ? 'warning' : 'primary'"
        @click="toggleTimer"
        round
      >
        {{ running ? '暂停' : '开始' }}
      </el-button>
      <el-button size="small" @click="resetTimer" round>重置</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'

const WORK_SECONDS = 25 * 60
const BREAK_SECONDS = 5 * 60
const CIRCUMFERENCE = 2 * Math.PI * 44

const isBreak = ref(false)
const totalSeconds = ref(WORK_SECONDS)
const remaining = ref(WORK_SECONDS)
const running = ref(false)
let timer = null

const displayTime = computed(() => {
  const m = Math.floor(remaining.value / 60)
  const s = remaining.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const dashOffset = computed(() => {
  const progress = remaining.value / totalSeconds.value
  return CIRCUMFERENCE * (1 - progress)
})

function toggleTimer() {
  if (running.value) {
    clearInterval(timer)
    timer = null
    running.value = false
  } else {
    running.value = true
    timer = setInterval(tick, 1000)
  }
}

function tick() {
  if (remaining.value <= 0) {
    clearInterval(timer)
    timer = null
    running.value = false
    notify()
    // 切换阶段
    isBreak.value = !isBreak.value
    totalSeconds.value = isBreak.value ? BREAK_SECONDS : WORK_SECONDS
    remaining.value = totalSeconds.value
    return
  }
  remaining.value--
}

function resetTimer() {
  clearInterval(timer)
  timer = null
  running.value = false
  isBreak.value = false
  totalSeconds.value = WORK_SECONDS
  remaining.value = WORK_SECONDS
}

function notify() {
  const msg = isBreak.value ? '休息结束，开始工作！' : '工作结束，休息一下！'
  if ('Notification' in window) {
    if (Notification.permission === 'granted') {
      new Notification('番茄钟', { body: msg })
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(p => {
        if (p === 'granted') new Notification('番茄钟', { body: msg })
      })
    }
  }
}

onBeforeUnmount(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.pomodoro-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px;
  gap: 12px;
}

.pomodoro-ring {
  position: relative;
  width: 120px;
  height: 120px;
}

.pomodoro-ring svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: var(--border-light, #E5E0DA);
  stroke-width: 6;
}

.ring-progress {
  fill: none;
  stroke: var(--accent);
  stroke-width: 6;
  stroke-linecap: round;
  stroke-dasharray: 276.46;
  transition: stroke-dashoffset 0.5s ease;
}

.ring-progress.is-break {
  stroke: #67c23a;
}

.ring-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.time-display {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.phase-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.pomodoro-controls {
  display: flex;
  gap: 8px;
}
</style>
