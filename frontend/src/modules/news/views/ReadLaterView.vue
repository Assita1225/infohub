<template>
  <div class="read-later-page">
    <div class="page-header">
      <el-button @click="$router.push('/news')">
        <el-icon><ArrowLeft /></el-icon> 返回新闻
      </el-button>
      <h2 class="page-title">稍后读</h2>
    </div>

    <div v-loading="loading" class="article-list">
      <div v-if="!loading && articles.length === 0" class="empty-state">
        <el-icon :size="48" color="var(--text-muted)"><Collection /></el-icon>
        <p>暂无稍后读文章</p>
      </div>

      <div
        v-for="article in articles"
        :key="article._id"
        class="article-item card"
        @click="$router.push(`/news/article/${article._id}`)"
      >
        <div class="item-content">
          <h3 class="item-title">{{ article.title }}</h3>
          <div class="item-meta">
            <span>{{ article.author || '未知来源' }}</span>
            <span>{{ formatDate(article.published_at) }}</span>
          </div>
        </div>
        <el-button
          text
          type="danger"
          size="small"
          @click.stop="handleRemove(article)"
        >
          移除
        </el-button>
      </div>

      <div class="pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadList"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ArrowLeft, Collection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getReadLaterList, removeReadLater } from '../api'

const articles = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)

async function loadList() {
  loading.value = true
  try {
    const res = await getReadLaterList(page.value, pageSize)
    articles.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleRemove(article) {
  try {
    await removeReadLater(article._id)
    articles.value = articles.value.filter(a => a._id !== article._id)
    total.value--
    ElMessage.success('已移出稍后读')
  } catch {
    ElMessage.error('操作失败')
  }
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}

onMounted(loadList)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.article-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  margin-bottom: 8px;
  cursor: pointer;
}

.item-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.item-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: var(--text-muted);
  font-size: 14px;
  gap: 12px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
