<template>
  <div class="trending-page">
    <div class="trending-layout">
      <!-- 左侧：热榜主区域 -->
      <div class="trending-main">
        <!-- 顶部操作 -->
        <div class="section-header">
          <h2 class="section-title">热度榜</h2>
          <div class="header-actions">
            <span v-if="lastUpdated" class="last-updated">
              更新于 {{ formatTime(lastUpdated) }}
            </span>
            <el-button type="primary" :loading="refreshing" @click="handleRefresh">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
        </div>

        <!-- 来源切换（胶囊标签） -->
        <div class="source-tabs">
          <button
            v-for="src in sources"
            :key="src.key"
            :class="['pill-btn', { active: activeSource === src.key }]"
            @click="activeSource = src.key"
          >{{ src.name }}</button>
        </div>

        <!-- 排行列表 -->
        <div v-loading="loading" class="trending-list card">
          <div v-if="!loading && currentItems.length === 0" class="empty-state-inline">
            暂无数据，点击刷新获取
          </div>
          <div v-else class="rank-list">
            <a
              v-for="item in currentItems"
              :key="item.rank"
              :href="item.url"
              target="_blank"
              rel="noopener"
              class="rank-item"
            >
              <span
                class="rank-num"
                :class="{
                  gold: item.rank === 1,
                  silver: item.rank === 2,
                  bronze: item.rank === 3,
                }"
              >{{ item.rank }}</span>
              <span class="rank-title">{{ item.title }}</span>
              <span class="rank-score">{{ formatScore(item.hot_score) }}</span>
            </a>
          </div>
        </div>

        <!-- 词云 -->
        <div class="wordcloud-section card">
          <h3 class="sub-title">热词云</h3>
          <div ref="chartRef" class="wordcloud-chart" />
        </div>
      </div>

      <!-- 右侧：个性化推荐卡片 -->
      <div class="recommend-panel">
        <div class="section-header">
          <h2 class="section-title">我的兴趣</h2>
        </div>

        <!-- 兴趣雷达图 -->
        <div v-if="selectedTags.length >= 3" class="radar-section card">
          <h3 class="sub-title">兴趣模型</h3>
          <div ref="radarRef" class="radar-chart" />
        </div>

        <!-- 预设标签区 -->
        <div class="tag-section">
          <div class="tag-list">
            <button
              v-for="tag in presetTags"
              :key="tag"
              :class="['pill-tag', weightClass(tag)]"
              @click="toggleTag(tag)"
              @contextmenu.prevent="cycleWeight(tag)"
            >{{ tag }}
              <span v-if="getTagWeight(tag)" class="weight-dot" :class="weightLevel(tag)" />
            </button>
          </div>
        </div>

        <!-- 选中标签的权重调节 -->
        <div v-if="selectedTags.length" class="weight-section">
          <div class="weight-hint">右键点击标签切换权重档位，或使用滑块微调</div>
          <div v-for="st in selectedTags" :key="st.name" class="weight-row">
            <span class="weight-tag-name">{{ st.name }}</span>
            <el-slider
              v-model="st.weight"
              :min="0.1"
              :max="1.0"
              :step="0.1"
              :show-tooltip="true"
              :format-tooltip="v => v.toFixed(1)"
              style="flex: 1; margin: 0 12px"
              @change="handleWeightChange"
            />
            <span class="weight-value">{{ st.weight.toFixed(1) }}</span>
          </div>
        </div>

        <!-- 自定义标签 -->
        <div class="custom-tag-input">
          <el-input
            v-model="newTag"
            placeholder="添加自定义标签"
            size="small"
            @keyup.enter="handleAddTag"
          >
            <template #append>
              <el-button @click="handleAddTag">添加</el-button>
            </template>
          </el-input>
        </div>

        <!-- 自定义标签展示（可删除） -->
        <div v-if="customTags.length" class="custom-tags">
          <el-tag
            v-for="tag in customTags"
            :key="tag"
            closable
            :type="isTagSelected(tag) ? '' : 'info'"
            effect="plain"
            round
            @click="toggleTag(tag)"
            @close="handleDeleteTag(tag)"
          >{{ tag }}</el-tag>
        </div>

        <!-- 推荐内容 -->
        <div class="feed-section card">
          <h3 class="sub-title">我关注的趋势</h3>
          <div v-loading="feedLoading" class="feed-list">
            <div
              v-if="!feedLoading && feedItems.length === 0"
              class="empty-state-inline"
            >
              {{ feedHint || '选择标签查看推荐' }}
            </div>
            <div
              v-for="(item, i) in feedItems"
              :key="i"
              class="feed-item-wrap"
            >
              <a
                :href="item.url"
                target="_blank"
                rel="noopener"
                class="feed-item"
              >
                <span class="feed-source-badge" :class="'source-' + item.source">{{ item.source_label }}</span>
                <span class="feed-title">{{ item.title }}</span>
                <span class="feed-score">{{ formatScore(item.hot_score) }}</span>
              </a>
              <div v-if="item.matched_keywords && item.matched_keywords.length" class="feed-matched">
                <el-tag v-for="kw in item.matched_keywords" :key="kw" size="small" type="warning" effect="light" round>{{ kw }}</el-tag>
              </div>
            </div>
            <div v-if="!feedLoading && feedItems.length > 0 && feedItems.length < 3 && !feedHint" class="feed-hint">
              匹配结果较少，试试选择更多标签
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import {
  getTrendingSources,
  getTrendingList,
  getWordcloudData,
  refreshTrending,
  getRecommendTags,
  updateSelectedTags,
  addCustomTag,
  deleteCustomTag,
  getRecommendFeed,
} from '../api'

// ── 热榜状态 ──
const sources = ref([])
const activeSource = ref('')
const trendingData = ref({})
const loading = ref(false)
const refreshing = ref(false)
const lastUpdated = ref('')

const currentItems = computed(() => {
  return trendingData.value[activeSource.value] || []
})

// ── 词云 ──
const chartRef = ref(null)
let chartInstance = null
const wordcloudData = ref([])

// ── 雷达图 ──
const radarRef = ref(null)
let radarInstance = null

// ── 推荐状态 ──
const presetTags = ref([])
const customTags = ref([])
const selectedTags = ref([])   // [{name, weight}]
const newTag = ref('')
const feedItems = ref([])
const feedHint = ref('')
const feedLoading = ref(false)

// ── 热榜方法 ──
async function loadSources() {
  try {
    const res = await getTrendingSources()
    sources.value = res.data
    if (sources.value.length && !activeSource.value) {
      activeSource.value = sources.value[0].key
    }
  } catch { /* ignore */ }
}

async function loadTrendingList() {
  loading.value = true
  try {
    const res = await getTrendingList()
    trendingData.value = res.data
    const firstSource = Object.values(res.data)[0]
    if (firstSource && firstSource.length) {
      lastUpdated.value = firstSource[0].fetched_at
    }
  } catch {
    ElMessage.error('加载热榜失败')
  } finally {
    loading.value = false
  }
}

async function loadWordcloud() {
  try {
    const res = await getWordcloudData()
    wordcloudData.value = res.data || []
    renderWordcloud()
  } catch { /* ignore */ }
}

async function handleRefresh() {
  refreshing.value = true
  try {
    const res = await refreshTrending()
    ElMessage.success(res.message)
    await loadTrendingList()
    await loadWordcloud()
  } catch {
    ElMessage.error('刷新失败')
  } finally {
    refreshing.value = false
  }
}

function formatScore(score) {
  if (!score) return ''
  if (score >= 10000) return (score / 10000).toFixed(1) + '万'
  return String(score)
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = (now - d) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前'
  return d.toLocaleString('zh-CN')
}

// ── 词云渲染 ──
function renderWordcloud() {
  if (!chartRef.value || !wordcloudData.value.length) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  chartInstance.setOption({
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      gridSize: 8,
      sizeRange: [14, 60],
      rotationRange: [-45, 45],
      rotationStep: 15,
      textStyle: {
        fontFamily: 'sans-serif',
        color() {
          const colors = ['#C45A3C', '#B04E32', '#D4826E', '#E6A23C', '#67C23A',
                          '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']
          return colors[Math.floor(Math.random() * colors.length)]
        },
      },
      data: wordcloudData.value,
    }],
  })
}

// ── 推荐方法 ──

function isTagSelected(tag) {
  return selectedTags.value.some(t => t.name === tag)
}

function getTagWeight(tag) {
  const t = selectedTags.value.find(t => t.name === tag)
  return t ? t.weight : 0
}

function weightClass(tag) {
  const t = selectedTags.value.find(t => t.name === tag)
  if (!t) return ''
  return 'active'
}

function weightLevel(tag) {
  const w = getTagWeight(tag)
  if (w >= 0.7) return 'high'
  if (w >= 0.4) return 'mid'
  return 'low'
}

async function loadTags() {
  try {
    const res = await getRecommendTags()
    presetTags.value = res.data.preset_tags || []
    customTags.value = res.data.custom_tags || []
    // 兼容旧格式
    const raw = res.data.selected_tags || []
    selectedTags.value = raw.map(t =>
      typeof t === 'string' ? { name: t, weight: 0.5 } : t
    )
  } catch { /* ignore */ }
}

async function toggleTag(tag) {
  const idx = selectedTags.value.findIndex(t => t.name === tag)
  if (idx >= 0) {
    selectedTags.value.splice(idx, 1)
  } else {
    selectedTags.value.push({ name: tag, weight: 0.5 })
  }
  try {
    await updateSelectedTags(selectedTags.value)
  } catch { /* ignore */ }
}

function cycleWeight(tag) {
  const t = selectedTags.value.find(t => t.name === tag)
  if (!t) {
    // 未选中，先选中并设为低权重
    selectedTags.value.push({ name: tag, weight: 0.3 })
  } else if (t.weight < 0.4) {
    t.weight = 0.6
  } else if (t.weight < 0.8) {
    t.weight = 1.0
  } else {
    t.weight = 0.3
  }
  updateSelectedTags(selectedTags.value).catch(() => {})
}

async function handleWeightChange() {
  try {
    await updateSelectedTags(selectedTags.value)
  } catch { /* ignore */ }
}

async function handleAddTag() {
  const tag = newTag.value.trim()
  if (!tag) return
  try {
    await addCustomTag(tag)
    customTags.value.push(tag)
    newTag.value = ''
    ElMessage.success('标签已添加')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '添加失败')
  }
}

async function handleDeleteTag(tag) {
  try {
    await deleteCustomTag(tag)
    customTags.value = customTags.value.filter(t => t !== tag)
    selectedTags.value = selectedTags.value.filter(t => t.name !== tag)
    ElMessage.success('标签已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

async function loadFeed() {
  if (!selectedTags.value.length) {
    feedItems.value = []
    feedHint.value = '请选择兴趣标签以获取个性化推荐'
    return
  }
  feedLoading.value = true
  try {
    const res = await getRecommendFeed(selectedTags.value)
    feedItems.value = res.data.items || []
    feedHint.value = res.data.hint || ''
  } catch { /* ignore */ }
  finally {
    feedLoading.value = false
  }
}

// ── 雷达图渲染 ──
function renderRadar() {
  if (!radarRef.value || selectedTags.value.length < 3) return
  if (!radarInstance) {
    radarInstance = echarts.init(radarRef.value)
  }
  // 取最多 8 个标签
  const items = selectedTags.value.slice(0, 8)
  radarInstance.setOption({
    radar: {
      indicator: items.map(t => ({ name: t.name, max: 1.0 })),
      shape: 'polygon',
      axisName: { color: 'var(--text-secondary)', fontSize: 12 },
      splitArea: { areaStyle: { color: ['rgba(196,90,60,0.02)', 'rgba(196,90,60,0.05)'] } },
      splitLine: { lineStyle: { color: 'var(--border-light)' } },
      axisLine: { lineStyle: { color: 'var(--border)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: items.map(t => t.weight),
        name: '兴趣权重',
        areaStyle: { color: 'rgba(196,90,60,0.2)' },
        lineStyle: { color: '#C45A3C', width: 2 },
        itemStyle: { color: '#C45A3C' },
      }],
    }],
    tooltip: {},
  })
}

let feedDebounce = null
watch(selectedTags, () => {
  clearTimeout(feedDebounce)
  feedDebounce = setTimeout(() => {
    loadFeed()
    renderRadar()
  }, 300)
}, { deep: true })

// ── 生命周期 ──
function handleResize() {
  chartInstance?.resize()
  radarInstance?.resize()
}

onMounted(async () => {
  await loadSources()
  await Promise.all([loadTrendingList(), loadWordcloud(), loadTags()])
  window.addEventListener('resize', handleResize)
  // 初始渲染雷达图
  setTimeout(renderRadar, 100)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  radarInstance?.dispose()
  clearTimeout(feedDebounce)
})
</script>

<style scoped>
.trending-layout {
  display: flex;
  gap: 24px;
}

.trending-main {
  flex: 1;
  min-width: 0;
}

.recommend-panel {
  width: 360px;
  flex-shrink: 0;
}

@media (max-width: 960px) {
  .trending-layout {
    flex-direction: column;
  }
  .recommend-panel {
    width: 100%;
  }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.last-updated {
  font-size: 12px;
  color: var(--text-muted);
}

.sub-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px;
}

/* 胶囊来源切换 */
.source-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.pill-btn {
  padding: 5px 14px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.pill-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.pill-btn.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

/* 排行列表 */
.trending-list {
  padding: 8px 16px;
  margin-bottom: 16px;
}

.rank-list {
  display: flex;
  flex-direction: column;
}

.rank-item {
  display: flex;
  align-items: center;
  padding: 10px 4px;
  border-radius: var(--radius-sm);
  text-decoration: none;
  color: var(--text-primary);
  transition: background 0.15s;
  gap: 12px;
  border-bottom: 1px solid var(--border-light);
}

.rank-item:last-child {
  border-bottom: none;
}

.rank-item:hover {
  background: var(--bg-hover);
}

.rank-num {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-muted);
  background: var(--bg-secondary);
  flex-shrink: 0;
}

.rank-num.gold {
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: #fff;
}
.rank-num.silver {
  background: linear-gradient(135deg, #C0C0C0, #A8A8A8);
  color: #fff;
}
.rank-num.bronze {
  background: linear-gradient(135deg, #CD7F32, #A0522D);
  color: #fff;
}

.rank-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  line-height: 1.4;
}

.rank-score {
  font-size: 12px;
  color: var(--accent);
  flex-shrink: 0;
  font-weight: 600;
}

/* 词云 */
.wordcloud-section {
  padding: 16px 20px;
}

.wordcloud-chart {
  width: 100%;
  height: 300px;
}

/* 兴趣标签 */
.tag-section {
  margin-bottom: 12px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pill-tag {
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.pill-tag:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.pill-tag.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

/* 雷达图 */
.radar-section {
  padding: 16px 20px;
  margin-bottom: 12px;
}

.radar-chart {
  width: 100%;
  height: 240px;
}

/* 权重指示圆点 */
.weight-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-left: 4px;
  vertical-align: middle;
}
.weight-dot.low { background: #67C23A; }
.weight-dot.mid { background: #E6A23C; }
.weight-dot.high { background: #F56C6C; }

/* 权重调节区 */
.weight-section {
  margin-bottom: 12px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.weight-hint {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.weight-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.weight-tag-name {
  font-size: 12px;
  color: var(--text-secondary);
  width: 60px;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.weight-value {
  font-size: 12px;
  color: var(--accent);
  font-weight: 600;
  width: 28px;
  text-align: right;
  flex-shrink: 0;
}

.custom-tag-input {
  margin-bottom: 12px;
}

.custom-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.custom-tags .el-tag {
  cursor: pointer;
}

/* 推荐 feed */
.feed-section {
  padding: 16px 20px;
}

.feed-list {
  min-height: 80px;
}

.feed-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  text-decoration: none;
  color: var(--text-primary);
  gap: 8px;
  transition: color 0.15s;
}

.feed-item:hover {
  color: var(--accent);
}

.feed-source-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  flex-shrink: 0;
  white-space: nowrap;
}

.feed-source-badge.source-github { background: #f0f0f0; color: #333; }
.feed-source-badge.source-baidu { background: #e6f0ff; color: #306cce; }
.feed-source-badge.source-weibo { background: #fff0f0; color: #e6162d; }
.feed-source-badge.source-google_trends { background: #fef3e2; color: #ea8600; }

.feed-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.feed-score {
  font-size: 11px;
  color: var(--accent);
  flex-shrink: 0;
  font-weight: 600;
}

.feed-item-wrap {
  border-bottom: 1px solid var(--border-light);
}

.feed-item-wrap:last-child {
  border-bottom: none;
}

.feed-matched {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 0 0 8px;
}

.feed-hint {
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  padding: 12px 0 4px;
}

.empty-state-inline {
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  padding: 24px 0;
}
</style>
