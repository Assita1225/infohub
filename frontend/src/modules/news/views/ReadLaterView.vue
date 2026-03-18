<template>
  <div class="read-later-page">
    <div class="page-header">
      <el-button @click="$router.push('/news')">
        <el-icon><ArrowLeft /></el-icon> 返回新闻
      </el-button>
      <h2 class="page-title">稍后读</h2>
    </div>

    <div v-loading="loading" class="article-list">
      <el-empty v-if="!loading && articles.length === 0" description="暂无稍后读文章" />

      <div
        v-for="article in articles"
        :key="article._id"
        class="article-item"
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
import { ArrowLeft } from '@element-plus/icons-vue'
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
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.article-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  margin-bottom: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.article-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.item-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px;
}

.item-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
