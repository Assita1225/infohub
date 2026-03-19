<template>
  <el-drawer
    v-model="visible"
    title="添加微件"
    size="360px"
    append-to-body
  >
    <div class="widget-list">
      <div
        v-for="w in allWidgets"
        :key="w.id"
        class="widget-option"
      >
        <span class="widget-option-icon">{{ w.icon }}</span>
        <div class="widget-option-info">
          <div class="widget-option-name">{{ w.name }}</div>
          <div class="widget-option-desc">{{ w.desc }}</div>
        </div>
        <el-button
          v-if="activeSet.has(w.id)"
          size="small"
          disabled
          round
        >
          已添加
        </el-button>
        <el-button
          v-else
          size="small"
          type="primary"
          round
          @click="$emit('add', w.id)"
        >
          添加
        </el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: Boolean,
  activeWidgets: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue', 'add'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const activeSet = computed(() => new Set(props.activeWidgets))

const allWidgets = [
  { id: 'weather', icon: '🌤️', name: '天气', desc: '实时天气与温度' },
  { id: 'clock', icon: '🕐', name: '时钟', desc: '当前时间与日期' },
  { id: 'calendar', icon: '📅', name: '日历', desc: '月历视图' },
  { id: 'todo', icon: '✅', name: '待办事项', desc: '管理日常待办' },
  { id: 'pomodoro', icon: '🍅', name: '番茄钟', desc: '25分钟专注工作计时' },
  { id: 'countdown', icon: '⏳', name: '倒计时', desc: '追踪重要日期' },
  { id: 'recent_notes', icon: '📝', name: '最近笔记', desc: '快速访问最近编辑的笔记' },
]
</script>

<style scoped>
.widget-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.widget-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius-md);
  transition: background 0.15s;
}

.widget-option:hover {
  background: var(--bg-primary);
}

.widget-option-icon {
  font-size: 28px;
  line-height: 1;
  flex-shrink: 0;
}

.widget-option-info {
  flex: 1;
  min-width: 0;
}

.widget-option-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.widget-option-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}
</style>
