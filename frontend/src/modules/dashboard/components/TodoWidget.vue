<template>
  <div class="todo-widget">
    <div class="todo-header">
      <span class="todo-title">待办事项</span>
      <span class="todo-count">{{ remaining }} 项待完成</span>
    </div>

    <div class="todo-input">
      <el-input
        v-model="newTitle"
        placeholder="添加新待办..."
        size="small"
        @keyup.enter="handleAdd"
      >
        <template #append>
          <el-button @click="handleAdd" :icon="Plus" />
        </template>
      </el-input>
    </div>

    <div class="todo-list">
      <div
        v-for="item in todos"
        :key="item._id"
        class="todo-item"
        :class="{ completed: item.completed }"
      >
        <el-checkbox
          :model-value="item.completed"
          @change="(val) => handleToggle(item, val)"
        />
        <span class="todo-text">{{ item.title }}</span>
        <el-button
          text
          size="small"
          class="todo-del"
          @click="handleDelete(item._id)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
      <div v-if="todos.length === 0" class="todo-empty">
        <el-icon :size="24" color="var(--text-muted)"><Finished /></el-icon>
        <span>暂无待办</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, Delete, Finished } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getTodos, createTodo, updateTodo, deleteTodo } from '../api'

const todos = ref([])
const newTitle = ref('')

const remaining = computed(() => todos.value.filter(t => !t.completed).length)

async function loadTodos() {
  try {
    const res = await getTodos()
    todos.value = res.data
  } catch { /* 静默 */ }
}

async function handleAdd() {
  const title = newTitle.value.trim()
  if (!title) return
  try {
    const res = await createTodo(title)
    todos.value.unshift(res.data)
    newTitle.value = ''
  } catch {
    ElMessage.error('添加失败')
  }
}

async function handleToggle(item, val) {
  try {
    const res = await updateTodo(item._id, { completed: val })
    Object.assign(item, res.data)
  } catch {
    ElMessage.error('更新失败')
  }
}

async function handleDelete(id) {
  try {
    await deleteTodo(id)
    todos.value = todos.value.filter(t => t._id !== id)
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(loadTodos)
</script>

<style scoped>
.todo-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 12px;
}

.todo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.todo-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.todo-count {
  font-size: 12px;
  color: var(--text-muted);
}

.todo-input {
  margin-bottom: 10px;
}

.todo-list {
  flex: 1;
  overflow-y: auto;
}

.todo-item {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid var(--border-light);
}

.todo-item.completed .todo-text {
  text-decoration: line-through;
  color: var(--text-muted);
}

.todo-text {
  flex: 1;
  font-size: 13px;
  margin-left: 8px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-del {
  opacity: 0;
  transition: opacity 0.2s;
}

.todo-item:hover .todo-del {
  opacity: 1;
}

.todo-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 13px;
  padding: 20px 0;
}
</style>
