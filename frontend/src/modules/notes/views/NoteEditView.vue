<template>
  <div class="note-edit-page">
    <!-- 顶部操作栏 -->
    <div class="edit-toolbar">
      <el-button @click="$router.push('/notes')">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <div class="toolbar-actions">
        <span v-if="saving" class="save-hint">保存中...</span>
        <span v-else-if="lastSaved" class="save-hint">已保存</span>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
        <el-popconfirm
          v-if="noteId"
          title="确认删除此笔记？"
          @confirm="handleDelete"
        >
          <template #reference>
            <el-button type="danger">删除</el-button>
          </template>
        </el-popconfirm>
      </div>
    </div>

    <!-- 来源信息 -->
    <div v-if="source.type !== 'manual'" class="source-banner">
      <el-icon><Link /></el-icon>
      <span>来源：{{ source.type === 'rss' ? 'RSS 文章' : '新闻' }}</span>
      <a v-if="source.article_url" :href="source.article_url" target="_blank" class="source-link">查看原文</a>
    </div>

    <!-- 标题输入 -->
    <el-input
      v-model="title"
      placeholder="输入笔记标题..."
      class="title-input"
      size="large"
    />

    <!-- 标签管理 -->
    <div class="tags-row">
      <el-tag
        v-for="tag in tags"
        :key="tag"
        closable
        @close="removeTag(tag)"
        size="default"
      >
        {{ tag }}
      </el-tag>
      <el-input
        v-if="showTagInput"
        ref="tagInputRef"
        v-model="newTag"
        size="small"
        style="width: 100px"
        @keyup.enter="addTag"
        @blur="addTag"
        placeholder="新标签"
      />
      <el-button v-else text size="small" @click="showTagInput = true; $nextTick(() => tagInputRef?.focus())">
        + 标签
      </el-button>
    </div>

    <!-- Markdown 编辑器 -->
    <div class="editor-container">
      <MdEditor
        v-model="content"
        language="zh-CN"
        :theme="'light'"
        style="height: 100%"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { getNote, createNote, updateNote, deleteNote } from '../api'

const route = useRoute()
const router = useRouter()

// 笔记数据
const noteId = ref(route.params.id || null)
const title = ref('')
const content = ref('')
const tags = ref([])
const source = ref({ type: 'manual', article_id: null, article_url: '', selected_text: '' })

// 状态
const saving = ref(false)
const lastSaved = ref(false)

// 标签输入
const showTagInput = ref(false)
const newTag = ref('')
const tagInputRef = ref(null)

function addTag() {
  const t = newTag.value.trim()
  if (t && !tags.value.includes(t)) {
    tags.value.push(t)
  }
  newTag.value = ''
  showTagInput.value = false
}

function removeTag(tag) {
  tags.value = tags.value.filter(t => t !== tag)
}

// 加载已有笔记
async function loadNote() {
  if (!noteId.value) return
  try {
    const res = await getNote(noteId.value)
    const data = res.data
    title.value = data.title || ''
    content.value = data.content || ''
    tags.value = data.tags || []
    source.value = data.source || { type: 'manual' }
  } catch {
    ElMessage.error('笔记不存在')
    router.push('/notes')
  }
}

// 从文章页过来的参数预填
function prefillFromQuery() {
  const q = route.query
  if (q.source_type) {
    source.value = {
      type: q.source_type,
      article_id: q.article_id || null,
      article_url: q.article_url || '',
      selected_text: q.selected_text || '',
    }
  }
  if (q.title) {
    title.value = q.title
  }
  // 如果有选中文本，作为初始内容
  if (q.selected_text) {
    content.value = `> ${q.selected_text}\n\n`
  }
  // 如果有文章摘要，附加到内容中
  if (q.summary) {
    content.value += `**AI 摘要：**\n${q.summary}\n\n`
  }
  // 来源链接
  if (q.article_url) {
    content.value += `[原文链接](${q.article_url})\n\n`
  }
}

async function handleSave() {
  if (!title.value.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  saving.value = true
  try {
    const data = {
      title: title.value,
      content: content.value,
      tags: tags.value,
      source: source.value,
    }
    if (noteId.value) {
      await updateNote(noteId.value, data)
    } else {
      const res = await createNote(data)
      noteId.value = res.data._id
      // 替换 URL 但不重新加载
      router.replace(`/notes/${noteId.value}`)
    }
    lastSaved.value = true
    setTimeout(() => { lastSaved.value = false }, 2000)
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  try {
    await deleteNote(noteId.value)
    ElMessage.success('已移入回收站')
    router.push('/notes')
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  if (noteId.value) {
    loadNote()
  } else {
    prefillFromQuery()
  }
})
</script>

<style scoped>
.note-edit-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.edit-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.save-hint {
  font-size: 12px;
  color: #909399;
}

.source-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #ecf5ff;
  border-radius: 4px;
  padding: 8px 12px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #409eff;
}

.source-link {
  margin-left: auto;
  color: #409eff;
  text-decoration: none;
}

.source-link:hover {
  text-decoration: underline;
}

.title-input {
  margin-bottom: 12px;
}

.title-input :deep(.el-input__inner) {
  font-size: 18px;
  font-weight: 600;
}

.tags-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.editor-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
