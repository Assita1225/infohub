<template>
  <div class="timeline-page card">
    <div class="timeline-header">
      <el-button @click="$router.push('/rss')">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <h3>阅读时间线</h3>
      <div class="range-btns">
        <el-radio-group v-model="days" size="small" @change="loadTimeline">
          <el-radio-button :value="7">最近7天</el-radio-button>
          <el-radio-button :value="30">最近30天</el-radio-button>
          <el-radio-button :value="365">全部</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div v-loading="loading" class="timeline-body">
      <div v-if="!loading && timeline.length === 0" class="empty-state">
        <el-empty description="暂无阅读记录" />
      </div>

      <div v-for="group in timeline" :key="group.date" class="day-group">
        <!-- 日期标题 -->
        <div class="day-header">
          <div class="day-dot"></div>
          <div class="day-date">{{ formatDate(group.date) }}</div>
          <el-tag size="small" round effect="plain">{{ group.count }} 篇</el-tag>
        </div>

        <!-- 文章卡片 -->
        <div class="day-articles">
          <div
            v-for="article in group.articles"
            :key="article._id"
            class="timeline-card"
            @click="goArticle(article._id)"
          >
            <div class="card-time">{{ formatTime(article.published_at) }}</div>
            <div class="card-main">
              <div class="card-title">{{ article.title }}</div>
              <div class="card-meta">
                <span class="card-source">{{ article.source }}</span>
                <el-tag
                  v-for="tag in article.tags.slice(0, 3)"
                  :key="tag"
                  size="small"
                  effect="plain"
                  round
                  class="card-tag"
                >{{ tag }}</el-tag>
              </div>
              <div v-if="article.summary" class="card-summary">{{ article.summary.slice(0, 80) }}...</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getTimeline } from '../api'

const router = useRouter()
const loading = ref(false)
const days = ref(7)
const timeline = ref([])

async function loadTimeline() {
  loading.value = true
  try {
    const res = await getTimeline(days.value)
    timeline.value = res.data
  } catch {
    ElMessage.error('加载时间线失败')
  }
  loading.value = false
}

function formatDate(dateStr) {
  const today = new Date().toISOString().slice(0, 10)
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
  if (dateStr === today) return '今天'
  if (dateStr === yesterday) return '昨天'
  return dateStr
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  return isoStr.slice(11, 16) || ''
}

function goArticle(id) {
  router.push(`/rss/article/${id}`)
}

onMounted(loadTimeline)
</script>

<style scoped>
.timeline-page {
  padding: 20px 24px;
  max-width: 800px;
  margin: 0 auto;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.timeline-header h3 {
  flex: 1;
  margin: 0;
  font-size: 16px;
  color: var(--text-primary);
}

.timeline-body {
  position: relative;
  padding-left: 20px;
  border-left: 2px solid var(--border-light, #e4e7ed);
}

.day-group {
  margin-bottom: 28px;
}

.day-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  position: relative;
}

.day-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--accent, #409eff);
  position: absolute;
  left: -27px;
  top: 4px;
}

.day-date {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.day-articles {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.timeline-card {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-card, #fff);
  border: 1px solid var(--border-light, #e4e7ed);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.timeline-card:hover {
  border-color: var(--accent, #409eff);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-time {
  font-size: 12px;
  color: var(--text-muted, #909399);
  min-width: 40px;
  padding-top: 2px;
}

.card-main {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.card-source {
  font-size: 12px;
  color: var(--accent, #409eff);
}

.card-tag {
  font-size: 11px;
}

.card-summary {
  font-size: 12px;
  color: var(--text-secondary, #606266);
  margin-top: 6px;
  line-height: 1.5;
}

.empty-state {
  padding: 40px 0;
}

@media (max-width: 767px) {
  .timeline-page {
    padding: 12px;
  }
  .timeline-header {
    flex-wrap: wrap;
  }
}
</style>
