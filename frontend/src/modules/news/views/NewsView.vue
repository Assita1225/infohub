<template>
  <div class="news-page">
    <!-- 顶部操作栏 -->
    <div class="news-header">
      <div class="category-tabs">
        <el-radio-group v-model="activeCategory" size="default" @change="onCategoryChange">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button
            v-for="cat in categories"
            :key="cat.key"
            :label="cat.key"
          >
            {{ cat.name }}
            <el-badge v-if="cat.count" :value="cat.count" :max="999" class="cat-badge" />
          </el-radio-button>
        </el-radio-group>
      </div>
      <div class="header-actions">
        <el-button @click="$router.push('/news/read-later')">
          <el-icon><Clock /></el-icon> 稍后读
        </el-button>
        <el-button type="primary" :loading="refreshing" @click="handleRefresh">
          <el-icon><Refresh /></el-icon> 刷新新闻
        </el-button>
      </div>
    </div>

    <!-- 文章卡片流 -->
    <div v-loading="loading" class="news-list">
      <el-empty v-if="!loading && articles.length === 0" description="暂无新闻，点击刷新获取最新内容" />

      <div v-else class="card-grid">
        <div
          v-for="article in articles"
          :key="article._id"
          class="news-card"
          @click="goArticle(article._id)"
        >
          <div class="card-body">
            <h3 class="card-title">{{ article.title }}</h3>
            <p class="card-summary" v-if="article.summary">{{ article.summary }}</p>
            <p class="card-summary" v-else-if="article.content">{{ truncate(article.content, 120) }}</p>
          </div>
          <div class="card-footer">
            <span class="card-source">{{ article.author || '未知来源' }}</span>
            <span class="card-time">{{ formatTime(article.published_at) }}</span>
            <div class="card-actions" @click.stop>
              <el-button
                text
                size="small"
                :type="article.is_read_later ? 'warning' : ''"
                @click="toggleReadLater(article)"
              >
                <el-icon><Clock /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadArticles"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Clock, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  getCategories,
  getNewsArticles,
  addReadLater,
  removeReadLater,
  refreshNews,
} from '../api'

const router = useRouter()

const categories = ref([])
const activeCategory = ref('')
const articles = ref([])
const loading = ref(false)
const refreshing = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)

async function loadCategories() {
  try {
    const res = await getCategories()
    categories.value = res.data
  } catch { /* ignore */ }
}

async function loadArticles() {
  loading.value = true
  try {
    const res = await getNewsArticles(activeCategory.value || undefined, page.value, pageSize)
    articles.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('加载新闻失败')
  } finally {
    loading.value = false
  }
}

function onCategoryChange() {
  page.value = 1
  loadArticles()
}

async function handleRefresh() {
  refreshing.value = true
  try {
    const res = await refreshNews()
    ElMessage.success(res.message)
    await loadCategories()
    await loadArticles()
  } catch {
    ElMessage.error('刷新失败')
  } finally {
    refreshing.value = false
  }
}

async function toggleReadLater(article) {
  try {
    if (article.is_read_later) {
      await removeReadLater(article._id)
      article.is_read_later = false
      ElMessage.success('已移出稍后读')
    } else {
      await addReadLater(article._id)
      article.is_read_later = true
      ElMessage.success('已添加到稍后读')
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

function goArticle(id) {
  router.push(`/news/article/${id}`)
}

function truncate(text, len) {
  if (!text) return ''
  const plain = text.replace(/<[^>]+>/g, '')
  return plain.length > len ? plain.slice(0, len) + '...' : plain
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diff = (now - d) / 1000
  if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前'
  if (diff < 604800) return Math.floor(diff / 86400) + ' 天前'
  return d.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadCategories()
  loadArticles()
})
</script>

<style scoped>
.news-page {
  padding: 0;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.category-tabs {
  flex: 1;
  min-width: 0;
  overflow-x: auto;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.cat-badge {
  margin-left: 4px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.news-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: box-shadow 0.2s;
  border: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.news-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  line-height: 1.5;
  margin: 0 0 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-summary {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
}

.card-source {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-actions {
  margin-left: auto;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
