<template>
  <div class="manage-page">
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
      <el-table-column prop="group" label="分组" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.error_count > 0" type="danger" size="small">异常</el-tag>
          <el-tag v-else type="success" size="small">正常</el-tag>
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

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editId ? '编辑订阅源' : '添加订阅源'" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.title" placeholder="如：阮一峰的博客" />
        </el-form-item>
        <el-form-item label="URL">
          <el-input v-model="form.url" placeholder="RSS Feed URL" />
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
import { getFeeds, getFeedGroups, addFeed, updateFeed, deleteFeed } from '../api'

const loading = ref(false)
const saving = ref(false)
const feeds = ref([])
const groups = ref([])
const showAdd = ref(false)
const editId = ref(null)

const form = reactive({ title: '', url: '', group: '未分组' })

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
    form.title = ''; form.url = ''; form.group = '未分组'
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

onMounted(loadData)
</script>

<style scoped>
.manage-page {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
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
}
</style>
