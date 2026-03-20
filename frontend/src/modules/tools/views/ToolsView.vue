<template>
  <div class="tools-page">
    <p class="page-subtitle">AI 驱动的效率工具</p>

    <div class="tools-grid">
      <div class="tool-card card" @click="$router.push('/tools/translate')">
        <div class="tool-icon translate-icon">
          <el-icon :size="32"><Switch /></el-icon>
        </div>
        <h3 class="tool-name">翻译器</h3>
        <p class="tool-desc">支持中英日韩法多语言互译，自动检测源语言</p>
        <div class="tool-tags">
          <span class="tool-tag">多语言</span>
          <span class="tool-tag">自动检测</span>
        </div>
      </div>

      <div class="tool-card card" @click="$router.push('/tools/polish')">
        <div class="tool-icon polish-icon">
          <el-icon :size="32"><MagicStick /></el-icon>
        </div>
        <h3 class="tool-name">润色器</h3>
        <p class="tool-desc">智能优化文本表达，支持正式、口语化、学术多种风格</p>
        <div class="tool-tags">
          <span class="tool-tag">多风格</span>
          <span class="tool-tag">修改标注</span>
        </div>
      </div>

      <div class="tool-card card" @click="$router.push('/tools/summarize')">
        <div class="tool-icon summarize-icon">
          <el-icon :size="32"><Document /></el-icon>
        </div>
        <h3 class="tool-name">总结器</h3>
        <p class="tool-desc">快速提取长文核心观点，支持自定义摘要长度</p>
        <div class="tool-tags">
          <span class="tool-tag">长文处理</span>
          <span class="tool-tag">要点提取</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Switch, MagicStick, Document } from '@element-plus/icons-vue'
</script>

<style scoped>
.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 24px;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.tool-card {
  cursor: pointer;
  text-align: center;
  padding: 32px 24px;
  transition: box-shadow 0.2s, transform 0.2s;
}
.tool-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.tool-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: #fff;
}
.translate-icon { background: linear-gradient(135deg, #667eea, #764ba2); }
.polish-icon    { background: linear-gradient(135deg, #f093fb, #f5576c); }
.summarize-icon { background: linear-gradient(135deg, #4facfe, #00f2fe); }

.tool-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.tool-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 16px;
}

.tool-tags {
  display: flex;
  justify-content: center;
  gap: 6px;
}
.tool-tag {
  padding: 2px 10px;
  border-radius: 10px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 11px;
}

@media (max-width: 767px) {
  .tools-grid {
    grid-template-columns: 1fr;
  }
}
</style>
