<template>
  <div class="tool-detail-page">
    <div class="tool-header">
      <el-button text @click="$router.push('/tools')">
        <el-icon><ArrowLeft /></el-icon> 返回工具箱
      </el-button>
      <h2 class="tool-title">翻译器</h2>
    </div>

    <!-- 选项栏 -->
    <div class="tool-options">
      <div class="option-group">
        <label>源语言</label>
        <el-select v-model="sourceLang" style="width: 130px">
          <el-option label="自动检测" value="auto" />
          <el-option label="中文" value="zh" />
          <el-option label="英文" value="en" />
          <el-option label="日文" value="ja" />
          <el-option label="韩文" value="ko" />
          <el-option label="法文" value="fr" />
        </el-select>
      </div>
      <el-icon class="swap-icon" @click="swapLangs"><Switch /></el-icon>
      <div class="option-group">
        <label>目标语言</label>
        <el-select v-model="targetLang" style="width: 130px">
          <el-option label="中文" value="zh" />
          <el-option label="英文" value="en" />
          <el-option label="日文" value="ja" />
          <el-option label="韩文" value="ko" />
          <el-option label="法文" value="fr" />
        </el-select>
      </div>
    </div>

    <!-- 输入 / 输出面板 -->
    <div class="tool-panels">
      <div class="panel input-panel card">
        <textarea
          v-model="inputText"
          class="panel-textarea"
          placeholder="请输入要翻译的文本..."
        />
        <div class="panel-footer">
          <span class="char-count">{{ inputText.length }} 字</span>
        </div>
      </div>

      <div class="panel-action">
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!inputText.trim()"
          @click="handleRun"
        >
          翻译
        </el-button>
      </div>

      <div class="panel output-panel card">
        <div class="panel-textarea output-text" :class="{ placeholder: !outputText }">
          {{ outputText || '翻译结果将在这里显示...' }}
        </div>
        <div class="panel-footer">
          <span class="char-count">{{ outputText.length }} 字</span>
          <el-button v-if="outputText" text size="small" @click="handleCopy">
            <el-icon><DocumentCopy /></el-icon> 复制
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ArrowLeft, Switch, DocumentCopy } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { translateStream } from '../api'

const sourceLang = ref('auto')
const targetLang = ref('en')
const inputText = ref('')
const outputText = ref('')
const loading = ref(false)

function swapLangs() {
  if (sourceLang.value === 'auto') return
  const tmp = sourceLang.value
  sourceLang.value = targetLang.value
  targetLang.value = tmp
}

async function handleRun() {
  if (!inputText.value.trim()) return
  loading.value = true
  outputText.value = ''

  await translateStream(
    {
      text: inputText.value,
      source_lang: sourceLang.value,
      target_lang: targetLang.value,
    },
    {
      onChunk({ chunk }) { outputText.value += chunk },
      onDone() { loading.value = false },
      onError(err) {
        loading.value = false
        ElMessage.error(err)
      },
    },
  )
}

function handleCopy() {
  navigator.clipboard.writeText(outputText.value)
  ElMessage.success('已复制到剪贴板')
}
</script>

<style scoped>
.tool-detail-page {
  max-width: 1100px;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.tool-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.tool-options {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.option-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.option-group label {
  font-size: 12px;
  color: var(--text-secondary);
}
.swap-icon {
  font-size: 20px;
  color: var(--text-secondary);
  cursor: pointer;
  padding-bottom: 8px;
  transition: color 0.15s;
}
.swap-icon:hover {
  color: var(--accent);
}

.tool-panels {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 16px;
  align-items: stretch;
}

.panel {
  display: flex;
  flex-direction: column;
  min-height: 320px;
}
.panel-textarea {
  flex: 1;
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
  background: transparent;
  font-family: inherit;
  padding: 0;
}
.output-text {
  white-space: pre-wrap;
  word-break: break-word;
  overflow-y: auto;
}
.output-text.placeholder {
  color: var(--text-muted);
}

.panel-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid var(--border-light);
  margin-top: 8px;
}
.char-count {
  font-size: 12px;
  color: var(--text-muted);
}

.panel-action {
  display: flex;
  align-items: center;
}

@media (max-width: 767px) {
  .tool-panels {
    grid-template-columns: 1fr;
  }
  .panel-action {
    justify-content: center;
  }
}
</style>
