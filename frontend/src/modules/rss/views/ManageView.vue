<template>
  <div class="manage-page card">
    <div class="manage-header">
      <el-button @click="$router.push('/rss')">
        <el-icon><ArrowLeft /></el-icon> 返回
      </el-button>
      <h3>管理订阅源</h3>
      <el-button type="primary" @click="showAdd = true">添加订阅源</el-button>
    </div>

    <!-- 列表 -->
    <el-table :data="feeds" v-loading="loading" stripe>
      <el-table-column prop="title" label="名称" min-width="160" />
      <el-table-column prop="url" label="URL" min-width="240" show-overflow-tooltip />
      <el-table-column label="类型" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.feed_type === 'web_monitor'" type="warning" size="small" round>网页监控</el-tag>
          <el-tag v-else type="" size="small" round>RSS</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="group" label="分组" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.error_count > 0" type="danger" size="small" round>异常</el-tag>
          <el-tag v-else type="success" size="small" round>正常</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" @click="startEdit(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row._id)">
            <template #reference>
              <el-button text size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 源健康状态 -->
    <div class="health-section">
      <h4 class="health-title">源健康状态</h4>
      <div v-loading="healthLoading" class="health-grid">
        <div
          v-for="h in healthData"
          :key="h._id"
          :class="['health-card', `health-${h.status}`]"
        >
          <div class="health-indicator" />
          <div class="health-info">
            <div class="health-name">{{ h.title }}</div>
            <div class="health-detail">
              <span>成功率：{{ h.success_rate }}%</span>
              <span v-if="h.error_count > 0">连续失败：{{ h.error_count }} 次</span>
              <span v-if="h.last_fetched_at">上次抓取：{{ formatTime(h.last_fetched_at) }}</span>
              <span v-else>尚未抓取</span>
            </div>
            <div v-if="h.last_error" class="health-error">{{ h.last_error }}</div>
          </div>
        </div>
        <div v-if="!healthLoading && healthData.length === 0" class="health-empty">暂无订阅源</div>
      </div>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editId ? '编辑订阅源' : '添加订阅源'" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="类型">
          <el-radio-group v-model="form.feed_type">
            <el-radio value="rss">RSS Feed</el-radio>
            <el-radio value="web_monitor">网页监控</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="form.title" placeholder="如：xxx的博客" />
        </el-form-item>
        <el-form-item label="URL">
          <el-input v-model="form.url" :placeholder="form.feed_type === 'web_monitor' ? '网页地址，如 https://example.com/blog' : 'RSS Feed URL'" />
        </el-form-item>
        <el-form-item v-if="form.feed_type === 'web_monitor'" label="CSS选择器">
          <el-input v-model="form.css_selector" placeholder="可选，如 .article-list 精准定位文章区域" />
          <div class="form-tip">不填则自动提取页面中标题长度大于10字符的链接</div>
        </el-form-item>
        <el-form-item label="分组">
          <el-select v-model="form.group" filterable allow-create placeholder="选择或新建分组">
            <el-option v-for="g in groups" :key="g.name" :label="g.name" :value="g.name" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getFeeds, getFeedGroups, addFeed, updateFeed, deleteFeed, getFeedsHealth } from '../api'

const loading = ref(false)
const saving = ref(false)
const feeds = ref([])
const groups = ref([])
const showAdd = ref(false)
const editId = ref(null)

const healthLoading = ref(false)
const healthData = ref([])

const form = reactive({ title: '', url: '', group: '未分组', feed_type: 'rss', css_selector: '' })

const showDialog = computed({
  get: () => showAdd.value || !!editId.value,
  set: (v) => { if (!v) { showAdd.value = false; editId.value = null } },
})

async function loadData() {
  loading.value = true
  try {
    const [feedRes, groupRes] = await Promise.all([getFeeds(), getFeedGroups()])
    feeds.value = feedRes.data
    groups.value = groupRes.data
  } catch { ElMessage.error('加载失败') }
  loading.value = false
}

function startEdit(row) {
  editId.value = row._id
  form.title = row.title
  form.url = row.url
  form.group = row.group
  form.feed_type = row.feed_type || 'rss'
  form.css_selector = row.css_selector || ''
}

async function handleSave() {
  if (!form.title || !form.url) {
    ElMessage.warning('名称和 URL 不能为空')
    return
  }
  saving.value = true
  try {
    if (editId.value) {
      await updateFeed(editId.value, { ...form })
      ElMessage.success('更新成功')
    } else {
      await addFeed({ ...form })
      ElMessage.success('添加成功')
    }
    showDialog.value = false
    form.title = ''; form.url = ''; form.group = '未分组'; form.feed_type = 'rss'; form.css_selector = ''
    await loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '操作失败')
  }
  saving.value = false
}

async function handleDelete(id) {
  try {
    await deleteFeed(id)
    ElMessage.success('已删除')
    await loadData()
  } catch { ElMessage.error('删除失败') }
}

async function loadHealth() {
  healthLoading.value = true
  try {
    const res = await getFeedsHealth()
    healthData.value = res.data
  } catch { /* ignore */ }
  healthLoading.value = false
}

function formatTime(iso) {
  if (!iso) return ''
  return iso.replace('T', ' ').slice(0, 16)
}

onMounted(() => {
  loadData()
  loadHealth()
})
</script>

<style scoped>
.manage-page {
  padding: 20px 24px;
}

.manage-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.manage-header h3 {
  flex: 1;
  margin: 0;
  font-size: 16px;
  color: var(--text-primary);
}

.form-tip {
  font-size: 12px;
  color: var(--text-secondary, #909399);
  line-height: 1.4;
  margin-top: 4px;
}

.health-section {
  margin-top: 32px;
  border-top: 1px solid var(--border-light, #e4e7ed);
  padding-top: 20px;
}

.health-title {
  margin: 0 0 16px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.health-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 10px;
}

.health-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--border-light, #e4e7ed);
  background: var(--bg-card, #fff);
}

.health-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}

.health-healthy .health-indicator { background: #67c23a; }
.health-warning .health-indicator { background: #e6a23c; }
.health-danger .health-indicator { background: #f56c6c; }

.health-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.health-detail {
  font-size: 12px;
  color: var(--text-secondary, #909399);
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.health-error {
  font-size: 11px;
  color: #f56c6c;
  margin-top: 4px;
  word-break: break-all;
}

.health-empty {
  color: var(--text-muted, #c0c4cc);
  font-size: 13px;
  padding: 20px;
  text-align: center;
}
</style>
