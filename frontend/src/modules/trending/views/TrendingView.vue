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

        <!-- 来源标签页 -->
        <el-tabs v-model="activeSource" @tab-change="onSourceChange">
          <el-tab-pane
            v-for="src in sources"
            :key="src.key"
            :label="src.name"
            :name="src.key"
          />
        </el-tabs>

        <!-- 排行列表 -->
        <div v-loading="loading" class="trending-list">
          <el-empty v-if="!loading && currentItems.length === 0" description="暂无数据，点击刷新获取" />
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
                :class="{ top: item.rank <= 3 }"
              >{{ item.rank }}</span>
              <span class="rank-title">{{ item.title }}</span>
              <span class="rank-score">{{ formatScore(item.hot_score) }}</span>
            </a>
          </div>
        </div>

        <!-- 词云 -->
        <div class="wordcloud-section">
          <h3 class="sub-title">热词云</h3>
          <div ref="chartRef" class="wordcloud-chart" />
        </div>
      </div>

      <!-- 右侧：个性化推荐卡片 -->
      <div class="recommend-panel">
        <div class="section-header">
          <h2 class="section-title">我的兴趣</h2>
        </div>

        <!-- 预设标签区 -->
        <div class="tag-section">
          <div class="tag-list">
            <el-check-tag
              v-for="tag in presetTags"
              :key="tag"
              :checked="selectedTags.includes(tag)"
              @change="toggleTag(tag)"
            >{{ tag }}</el-check-tag>
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
            :type="selectedTags.includes(tag) ? '' : 'info'"
            @click="toggleTag(tag)"
            @close="handleDeleteTag(tag)"
          >{{ tag }}</el-tag>
        </div>

        <!-- 推荐内容 -->
        <div class="feed-section">
          <h3 class="sub-title">我关注的趋势</h3>
          <div v-loading="feedLoading" class="feed-list">
            <el-empty
              v-if="!feedLoading && feedItems.length === 0"
              :description="feedHint || '选择标签查看推荐'"
              :image-size="80"
            />
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
                <el-tag v-for="kw in item.matched_keywords" :key="kw" size="small" type="warning" effect="light">{{ kw }}</el-tag>
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

// ── 推荐状态 ──
const presetTags = ref([])
const customTags = ref([])
const selectedTags = ref([])
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

function onSourceChange() {
  // 数据已全部加载，切换标签页即可
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
          const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399',
                          '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']
          return colors[Math.floor(Math.random() * colors.length)]
        },
      },
      data: wordcloudData.value,
    }],
  })
}

// ── 推荐方法 ──
async function loadTags() {
  try {
    const res = await getRecommendTags()
    presetTags.value = res.data.preset_tags || []
    customTags.value = res.data.custom_tags || []
    selectedTags.value = res.data.selected_tags || []
  } catch { /* ignore */ }
}

async function toggleTag(tag) {
  const idx = selectedTags.value.indexOf(tag)
  if (idx >= 0) {
    selectedTags.value.splice(idx, 1)
  } else {
    selectedTags.value.push(tag)
  }
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
    selectedTags.value = selectedTags.value.filter(t => t !== tag)
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

// 标签变化时自动刷新推荐
let feedDebounce = null
watch(selectedTags, () => {
  clearTimeout(feedDebounce)
  feedDebounce = setTimeout(loadFeed, 300)
}, { deep: true })

// ── 生命周期 ──
function handleResize() {
  chartInstance?.resize()
}

onMounted(async () => {
  await loadSources()
  await Promise.all([loadTrendingList(), loadWordcloud(), loadTags()])
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  clearTimeout(feedDebounce)
})
</script>

<style scoped>
.trending-page {
  padding: 0;
}

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
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.last-updated {
  font-size: 12px;
  color: #909399;
}

.sub-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 20px 0 12px;
}

/* 排行列表 */
.rank-list {
  display: flex;
  flex-direction: column;
}

.rank-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  text-decoration: none;
  color: #303133;
  transition: background 0.15s;
  gap: 12px;
}

.rank-item:hover {
  background: #f5f7fa;
}

.rank-num {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  color: #909399;
  background: #f0f2f5;
  flex-shrink: 0;
}

.rank-num.top {
  background: #409EFF;
  color: #fff;
}

.rank-item:nth-child(1) .rank-num.top { background: #F56C6C; }
.rank-item:nth-child(2) .rank-num.top { background: #E6A23C; }
.rank-item:nth-child(3) .rank-num.top { background: #409EFF; }

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
  color: #F56C6C;
  flex-shrink: 0;
  font-weight: 500;
}

/* 词云 */
.wordcloud-section {
  margin-top: 8px;
}

.wordcloud-chart {
  width: 100%;
  height: 300px;
  background: #fafafa;
  border-radius: 8px;
}

/* 标签 */
.tag-section {
  margin-bottom: 12px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-list .el-check-tag {
  cursor: pointer;
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
.feed-list {
  min-height: 100px;
}

.feed-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  text-decoration: none;
  color: #303133;
  gap: 8px;
  transition: background 0.15s;
}

.feed-item:hover {
  background: #f5f7fa;
}

.feed-source-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  background: #ecf5ff;
  color: #409EFF;
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
  color: #F56C6C;
  flex-shrink: 0;
  font-weight: 500;
}

.feed-item-wrap {
  border-bottom: 1px solid #f0f2f5;
}

.feed-item-wrap:last-child {
  border-bottom: none;
}

.feed-item-wrap .feed-item {
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
  color: #909399;
  padding: 12px 0 4px;
}
</style>
