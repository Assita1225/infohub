<template>
  <div class="overview-page">
    <div class="overview-header">
      <p class="page-subtitle">数据驱动的信息全景</p>
      <div class="header-right">
        <span v-if="updatedAt" class="update-time">数据更新于 {{ updatedAt }}</span>
        <el-button :loading="loading" @click="loadStats">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- 第一行：核心指标卡片 -->
    <div v-if="loading && !stats" class="skeleton-row">
      <div v-for="i in 4" :key="i" class="skeleton-card" />
    </div>
    <div v-else class="stat-cards">
      <div class="stat-card">
        <div class="stat-number">{{ stats?.total_articles ?? '-' }}</div>
        <div class="stat-label">文章总数</div>
        <div v-if="stats?.today_new_articles" class="stat-delta">+{{ stats.today_new_articles }} 今日新增</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ stats?.total_read ?? '-' }}</div>
        <div class="stat-label">已读文章</div>
        <div class="stat-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: (stats?.read_rate ?? 0) * 100 + '%' }" />
          </div>
          <span class="progress-text">{{ ((stats?.read_rate ?? 0) * 100).toFixed(0) }}%</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ stats?.total_feeds ?? '-' }}</div>
        <div class="stat-label">订阅源</div>
        <div class="stat-health">
          <span class="health-dot healthy" />{{ stats?.feeds_health?.healthy ?? 0 }} 正常
          <span v-if="stats?.feeds_health?.error" class="health-sep">·</span>
          <span v-if="stats?.feeds_health?.error" class="health-dot error" />
          <span v-if="stats?.feeds_health?.error">{{ stats.feeds_health.error }} 异常</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ stats?.total_notes ?? '-' }}</div>
        <div class="stat-label">笔记总数</div>
        <div v-if="stats?.today_notes" class="stat-delta">+{{ stats.today_notes }} 今日新建</div>
      </div>
    </div>

    <!-- 第二行：趋势折线图 + 来源饼图 -->
    <div class="chart-row">
      <div class="chart-card">
        <h3 class="chart-title">近 7 天趋势</h3>
        <div ref="lineChartRef" class="chart-container" />
      </div>
      <div class="chart-card">
        <h3 class="chart-title">文章来源占比</h3>
        <div ref="pieChartRef" class="chart-container" />
      </div>
    </div>

    <!-- 第三行：热门标签 + 订阅源健康 -->
    <div class="chart-row">
      <div class="chart-card">
        <h3 class="chart-title">热门标签 Top 10</h3>
        <div ref="barChartRef" class="chart-container" />
      </div>
      <div class="chart-card">
        <h3 class="chart-title">订阅源健康状况</h3>
        <div class="health-section">
          <div class="health-rings">
            <div class="ring-item">
              <div class="ring healthy-ring">
                <span class="ring-num">{{ stats?.feeds_health?.healthy ?? 0 }}</span>
              </div>
              <span class="ring-label">正常</span>
            </div>
            <div class="ring-item">
              <div class="ring warning-ring">
                <span class="ring-num">{{ stats?.feeds_health?.warning ?? 0 }}</span>
              </div>
              <span class="ring-label">警告</span>
            </div>
            <div class="ring-item">
              <div class="ring error-ring">
                <span class="ring-num">{{ stats?.feeds_health?.error ?? 0 }}</span>
              </div>
              <span class="ring-label">异常</span>
            </div>
          </div>
          <div v-if="stats?.feeds_health?.error_feeds?.length" class="error-list">
            <div v-for="(f, i) in stats.feeds_health.error_feeds" :key="i" class="error-item">
              <span class="error-name">{{ f.name }}</span>
              <span class="error-reason">{{ f.last_error || '未知错误' }}</span>
            </div>
          </div>
          <div v-else class="error-list-empty">所有订阅源运行正常</div>
        </div>
      </div>
    </div>

    <!-- 活跃订阅源 -->
    <div v-if="stats?.active_feeds?.length" class="active-feeds-section">
      <h3 class="chart-title">最近活跃的订阅源</h3>
      <div class="active-feeds-grid">
        <div v-for="(f, i) in stats.active_feeds" :key="i" class="active-feed-card">
          <div class="af-name">{{ f.name }}</div>
          <div class="af-meta">
            <span>{{ f.article_count }} 篇文章</span>
            <span class="af-time">{{ formatTime(f.last_fetched) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getOverviewStats } from '../api'

const loading = ref(false)
const stats = ref(null)
const updatedAt = ref('')

const lineChartRef = ref(null)
const pieChartRef = ref(null)
const barChartRef = ref(null)

let lineChart = null
let pieChart = null
let barChart = null

// 获取 CSS 变量值
function getCssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

async function loadStats() {
  loading.value = true
  try {
    const res = await getOverviewStats()
    stats.value = res.data
    updatedAt.value = new Date().toLocaleTimeString('zh-CN')
    await nextTick()
    renderCharts()
  } catch {
    ElMessage.error('加载全景数据失败')
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  renderLineChart()
  renderPieChart()
  renderBarChart()
}

function renderLineChart() {
  if (!lineChartRef.value || !stats.value) return
  if (!lineChart) lineChart = echarts.init(lineChartRef.value)

  const accent = getCssVar('--accent') || '#C45A3C'
  const dates = (stats.value.daily_articles || []).map(d => d.date)
  const articleData = (stats.value.daily_articles || []).map(d => d.count)
  const readData = (stats.value.daily_reads || []).map(d => d.count)

  lineChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['新增文章', '阅读量'],
      textStyle: { color: getCssVar('--text-secondary') || '#666' },
    },
    grid: { left: 40, right: 20, top: 40, bottom: 28 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: getCssVar('--border') || '#ddd' } },
      axisLabel: { color: getCssVar('--text-muted') || '#999' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: getCssVar('--border-light') || '#eee' } },
      axisLabel: { color: getCssVar('--text-muted') || '#999' },
    },
    series: [
      {
        name: '新增文章',
        type: 'line',
        data: articleData,
        smooth: true,
        lineStyle: { color: '#3B82F6', width: 2 },
        itemStyle: { color: '#3B82F6' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59,130,246,0.15)' },
          { offset: 1, color: 'rgba(59,130,246,0)' },
        ]) },
      },
      {
        name: '阅读量',
        type: 'line',
        data: readData,
        smooth: true,
        lineStyle: { color: accent, width: 2 },
        itemStyle: { color: accent },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(196,90,60,0.15)' },
          { offset: 1, color: 'rgba(196,90,60,0)' },
        ]) },
      },
    ],
  })
}

function renderPieChart() {
  if (!pieChartRef.value || !stats.value) return
  if (!pieChart) pieChart = echarts.init(pieChartRef.value)

  const data = (stats.value.articles_by_source || []).map(d => ({
    name: d.source,
    value: d.count,
  }))
  const total = data.reduce((s, d) => s + d.value, 0)

  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      bottom: 0,
      textStyle: { color: getCssVar('--text-secondary') || '#666' },
    },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      label: {
        show: true,
        formatter: '{b}\n{d}%',
        color: getCssVar('--text-secondary') || '#666',
      },
      itemStyle: { borderRadius: 6, borderColor: getCssVar('--bg-card') || '#fff', borderWidth: 2 },
      data,
      color: ['#C45A3C', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6'],
      emphasis: {
        label: { fontSize: 14, fontWeight: 'bold' },
      },
    }],
    graphic: [{
      type: 'text',
      left: 'center',
      top: '40%',
      style: {
        text: String(total),
        textAlign: 'center',
        fill: getCssVar('--text-primary') || '#333',
        fontSize: 24,
        fontWeight: 'bold',
      },
    }, {
      type: 'text',
      left: 'center',
      top: '48%',
      style: {
        text: '总计',
        textAlign: 'center',
        fill: getCssVar('--text-muted') || '#999',
        fontSize: 12,
      },
    }],
  })
}

function renderBarChart() {
  if (!barChartRef.value || !stats.value) return
  if (!barChart) barChart = echarts.init(barChartRef.value)

  const tags = (stats.value.top_tags || []).slice().reverse()
  const accent = getCssVar('--accent') || '#C45A3C'

  barChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 80, right: 30, top: 10, bottom: 20 },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: getCssVar('--border-light') || '#eee' } },
      axisLabel: { color: getCssVar('--text-muted') || '#999' },
    },
    yAxis: {
      type: 'category',
      data: tags.map(t => t.tag),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: getCssVar('--text-secondary') || '#666',
        width: 70,
        overflow: 'truncate',
      },
    },
    series: [{
      type: 'bar',
      data: tags.map(t => t.count),
      barWidth: 16,
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: accent },
          { offset: 1, color: '#E6A23C' },
        ]),
      },
    }],
  })
}

function handleResize() {
  lineChart?.resize()
  pieChart?.resize()
  barChart?.resize()
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = (now - d) / 1000 / 60
  if (diff < 1) return '刚刚'
  if (diff < 60) return `${Math.floor(diff)}分钟前`
  if (diff < 1440) return `${Math.floor(diff / 60)}小时前`
  return d.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  lineChart?.dispose()
  pieChart?.dispose()
  barChart?.dispose()
})
</script>

<style scoped>
.overview-page {
  min-height: calc(100vh - 120px);
  background: var(--bg-secondary);
  margin: -24px -32px;
  padding: 24px 32px;
}

.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.update-time {
  font-size: 12px;
  color: var(--text-muted);
}

/* 骨架屏 */
.skeleton-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.skeleton-card {
  height: 120px;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 核心指标卡片 */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
}

.stat-number {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-display);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

.stat-delta {
  font-size: 12px;
  color: #10B981;
  margin-top: 8px;
  font-weight: 600;
}

.stat-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #E6A23C);
  border-radius: 3px;
  transition: width 0.6s ease;
}

.progress-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  flex-shrink: 0;
}

.stat-health {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.health-dot.healthy { background: #10B981; }
.health-dot.error { background: #F56C6C; }
.health-sep { margin: 0 4px; color: var(--text-muted); }

/* 图表行 */
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px;
}

.chart-container {
  width: 100%;
  height: 280px;
}

/* 健康状况 */
.health-section {
  padding: 8px 0;
}

.health-rings {
  display: flex;
  justify-content: center;
  gap: 32px;
  margin-bottom: 20px;
}

.ring-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.ring {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid;
}

.healthy-ring { border-color: #10B981; background: rgba(16,185,129,0.08); }
.warning-ring { border-color: #E6A23C; background: rgba(230,162,60,0.08); }
.error-ring { border-color: #F56C6C; background: rgba(245,108,108,0.08); }

.ring-num {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.ring-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.error-list {
  border-top: 1px solid var(--border-light);
  padding-top: 12px;
}

.error-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
}

.error-item:last-child { border-bottom: none; }

.error-name {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.error-reason {
  font-size: 12px;
  color: #F56C6C;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.error-list-empty {
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
  padding: 8px 0;
}

/* 活跃订阅源 */
.active-feeds-section {
  margin-bottom: 20px;
}

.active-feeds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.active-feed-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
}

.af-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.af-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
}

.af-time {
  color: var(--text-muted);
}

/* 移动端适配 */
@media (max-width: 767px) {
  .overview-page {
    margin: -16px;
    padding: 16px;
  }

  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .skeleton-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .chart-row {
    grid-template-columns: 1fr;
  }

  .overview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .stat-number {
    font-size: 28px;
  }
}
</style>
