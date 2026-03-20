<template>
  <div class="finance-page">
    <p class="page-subtitle">清晰掌控每一笔</p>

    <!-- 月份选择 -->
    <div class="month-nav">
      <el-button text @click="changeMonth(-1)">
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
      <span class="month-label">{{ currentMonth }}</span>
      <el-button text @click="changeMonth(1)">
        <el-icon><ArrowRight /></el-icon>
      </el-button>
    </div>

    <!-- 汇总卡片 -->
    <div class="summary-cards">
      <div class="summary-card income-card card">
        <span class="summary-label">收入</span>
        <span class="summary-value income">+{{ summary.income.toFixed(2) }}</span>
      </div>
      <div class="summary-card expense-card card">
        <span class="summary-label">支出</span>
        <span class="summary-value expense">-{{ summary.expense.toFixed(2) }}</span>
      </div>
      <div class="summary-card balance-card card">
        <span class="summary-label">结余</span>
        <span :class="['summary-value', summary.balance >= 0 ? 'income' : 'expense']">
          {{ summary.balance >= 0 ? '+' : '' }}{{ summary.balance.toFixed(2) }}
        </span>
      </div>
    </div>

    <!-- 图表区 -->
    <div class="charts-section">
      <div class="chart-wrapper card">
        <h4 class="chart-title">本月支出分类</h4>
        <div ref="pieChartRef" class="chart-container" />
        <div v-if="!hasExpenseData" class="chart-empty">暂无支出数据</div>
      </div>
      <div class="chart-wrapper card">
        <h4 class="chart-title">近 6 个月收支趋势</h4>
        <div ref="lineChartRef" class="chart-container" />
      </div>
    </div>

    <!-- 类型筛选 -->
    <div class="filter-bar">
      <el-radio-group v-model="filterType" size="small" @change="loadRecords">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="expense">支出</el-radio-button>
        <el-radio-button value="income">收入</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 记录列表 -->
    <div class="records-section" v-loading="loading">
      <template v-for="(group, date) in groupedRecords" :key="date">
        <div class="date-group">
          <div class="date-header">
            <span class="date-text">{{ date }}</span>
            <span class="date-summary">
              {{ getDaySummary(group) }}
            </span>
          </div>
          <div class="record-list">
            <div v-for="r in group" :key="r._id" class="record-item">
              <div class="record-left">
                <span class="record-category-icon">{{ getCategoryIcon(r.category) }}</span>
                <div class="record-info">
                  <span class="record-category">{{ r.category }}</span>
                  <span v-if="r.note" class="record-note">{{ r.note }}</span>
                </div>
              </div>
              <div class="record-right">
                <span :class="['record-amount', r.type]">
                  {{ r.type === 'income' ? '+' : '-' }}{{ r.amount.toFixed(2) }}
                </span>
                <el-dropdown trigger="click" @command="(cmd) => handleRecordCommand(cmd, r)">
                  <el-button text size="small" class="more-btn">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">编辑</el-dropdown-item>
                      <el-dropdown-item command="delete">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </div>
      </template>

      <div v-if="!loading && records.length === 0" class="empty-state">
        <el-icon :size="48" color="var(--text-muted)"><Wallet /></el-icon>
        <p>这个月还没有记录</p>
      </div>
    </div>

    <!-- 浮动记一笔按钮 -->
    <button class="fab-btn" @click="openAddDialog">
      <el-icon :size="24"><Plus /></el-icon>
    </button>

    <!-- 添加 / 编辑弹窗 -->
    <el-dialog v-model="showDialog" :title="editingRecord ? '编辑记录' : '记一笔'" width="420px" :append-to-body="true">
      <el-form :model="form" label-position="top">
        <el-form-item label="类型">
          <el-radio-group v-model="form.type" @change="form.category = ''">
            <el-radio value="expense">支出</el-radio>
            <el-radio value="income">收入</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="金额">
          <el-input v-model="form.amount" type="number" placeholder="0.00" :min="0" step="0.01">
            <template #prefix>¥</template>
          </el-input>
        </el-form-item>
        <el-form-item label="分类">
          <div class="category-picker">
            <span
              v-for="cat in currentCategories"
              :key="cat"
              :class="['category-tag', { selected: form.category === cat }]"
              @click="form.category = cat"
            >
              {{ getCategoryIcon(cat) }} {{ cat }}
            </span>
          </div>
        </el-form-item>
        <el-form-item label="日期">
          <el-input v-model="form.date" type="date" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.note" placeholder="可选备注" maxlength="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ArrowLeft, ArrowRight, Plus, MoreFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import {
  getRecords, createRecord, updateRecord, deleteRecord,
  getSummary, getTrend,
} from '../api'

// Wallet icon (not in element-plus icons, use inline)
const Wallet = {
  template: `<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg"><path d="M832 192H192c-35.3 0-64 28.7-64 64v512c0 35.3 28.7 64 64 64h640c35.3 0 64-28.7 64-64V256c0-35.3-28.7-64-64-64zm0 576H192V256h640v512zm-128-256c0-35.3-28.7-64-64-64s-64 28.7-64 64 28.7 64 64 64 64-28.7 64-64z" fill="currentColor"/></svg>`,
}

const EXPENSE_CATEGORIES = ['餐饮', '交通', '购物', '娱乐', '住房', '通讯', '医疗', '教育', '其他']
const INCOME_CATEGORIES = ['工资', '兼职', '理财', '红包', '其他']

const CATEGORY_ICONS = {
  '餐饮': '🍜', '交通': '🚗', '购物': '🛒', '娱乐': '🎮', '住房': '🏠',
  '通讯': '📱', '医疗': '💊', '教育': '📚', '其他': '📦',
  '工资': '💰', '兼职': '💼', '理财': '📈', '红包': '🧧',
}

function getCategoryIcon(cat) {
  return CATEGORY_ICONS[cat] || '📦'
}

// 月份状态
const now = new Date()
const monthOffset = ref(0)
const currentMonth = computed(() => {
  const d = new Date(now.getFullYear(), now.getMonth() + monthOffset.value, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
})

function changeMonth(delta) {
  monthOffset.value += delta
}

// 数据
const loading = ref(false)
const records = ref([])
const summary = reactive({ income: 0, expense: 0, balance: 0, categories: { income: {}, expense: {} } })
const filterType = ref('')

const hasExpenseData = computed(() => {
  return Object.keys(summary.categories.expense || {}).length > 0
})

const groupedRecords = computed(() => {
  const groups = {}
  for (const r of records.value) {
    if (!groups[r.date]) groups[r.date] = []
    groups[r.date].push(r)
  }
  return groups
})

function getDaySummary(group) {
  let inc = 0, exp = 0
  for (const r of group) {
    if (r.type === 'income') inc += r.amount
    else exp += r.amount
  }
  const parts = []
  if (inc > 0) parts.push(`收入 ${inc.toFixed(2)}`)
  if (exp > 0) parts.push(`支出 ${exp.toFixed(2)}`)
  return parts.join(' / ')
}

// 图表
const pieChartRef = ref(null)
const lineChartRef = ref(null)
let pieChart = null
let lineChart = null

async function loadAll() {
  loading.value = true
  try {
    await Promise.all([loadRecords(), loadSummary(), loadTrend()])
  } finally {
    loading.value = false
  }
}

async function loadRecords() {
  try {
    const params = { month: currentMonth.value }
    if (filterType.value) params.type = filterType.value
    const res = await getRecords(params)
    records.value = res.data.items || []
  } catch {
    ElMessage.error('加载记录失败')
  }
}

async function loadSummary() {
  try {
    const res = await getSummary(currentMonth.value)
    Object.assign(summary, res.data)
    await nextTick()
    renderPieChart()
  } catch {
    // silent
  }
}

async function loadTrend() {
  try {
    const year = parseInt(currentMonth.value.split('-')[0])
    const res = await getTrend(year)
    await nextTick()
    renderLineChart(res.data)
  } catch {
    // silent
  }
}

function renderPieChart() {
  if (!pieChartRef.value) return
  if (!pieChart) pieChart = echarts.init(pieChartRef.value)

  const expCats = summary.categories.expense || {}
  const data = Object.entries(expCats).map(([name, value]) => ({ name, value }))

  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: ¥{c} ({d}%)',
    },
    color: ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6', '#1abc9c', '#34495e', '#95a5a6'],
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '55%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: 'var(--bg-card, #fff)', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 12 },
      data,
    }],
  }, true)
}

function renderLineChart(trend) {
  if (!lineChartRef.value) return
  if (!lineChart) lineChart = echarts.init(lineChartRef.value)

  // 取当前月往前 6 个月
  const curIdx = parseInt(currentMonth.value.split('-')[1]) - 1
  const year = parseInt(currentMonth.value.split('-')[0])
  const months = []
  const incomes = []
  const expenses = []

  for (let i = 5; i >= 0; i--) {
    let m = curIdx - i
    let y = year
    if (m < 0) { m += 12; y -= 1 }
    const key = `${y}-${String(m + 1).padStart(2, '0')}`
    const item = trend.find(t => t.month === key)
    months.push(`${m + 1}月`)
    incomes.push(item ? item.income : 0)
    expenses.push(item ? item.expense : 0)
  }

  lineChart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter(params) {
        let s = params[0].axisValueLabel
        for (const p of params) {
          s += `<br/>${p.marker} ${p.seriesName}: ¥${p.value.toFixed(2)}`
        }
        return s
      },
    },
    legend: { data: ['收入', '支出'], bottom: 0, textStyle: { color: 'var(--text-secondary, #666)' } },
    grid: { top: 16, left: 50, right: 16, bottom: 36 },
    xAxis: { type: 'category', data: months, axisLine: { lineStyle: { color: '#ddd' } }, axisLabel: { color: 'var(--text-secondary, #666)' } },
    yAxis: { type: 'value', axisLabel: { color: 'var(--text-secondary, #666)' }, splitLine: { lineStyle: { color: 'var(--border-light, #eee)' } } },
    series: [
      { name: '收入', type: 'line', smooth: true, data: incomes, itemStyle: { color: '#2ecc71' }, areaStyle: { color: 'rgba(46,204,113,0.08)' } },
      { name: '支出', type: 'line', smooth: true, data: expenses, itemStyle: { color: '#e74c3c' }, areaStyle: { color: 'rgba(231,76,60,0.08)' } },
    ],
  }, true)
}

// 弹窗
const showDialog = ref(false)
const editingRecord = ref(null)
const saving = ref(false)
const form = reactive({
  type: 'expense',
  amount: '',
  category: '',
  note: '',
  date: new Date().toISOString().slice(0, 10),
})

const currentCategories = computed(() => {
  return form.type === 'income' ? INCOME_CATEGORIES : EXPENSE_CATEGORIES
})

function openAddDialog() {
  editingRecord.value = null
  form.type = 'expense'
  form.amount = ''
  form.category = ''
  form.note = ''
  form.date = new Date().toISOString().slice(0, 10)
  showDialog.value = true
}

function handleRecordCommand(cmd, record) {
  if (cmd === 'edit') {
    editingRecord.value = record
    form.type = record.type
    form.amount = String(record.amount)
    form.category = record.category
    form.note = record.note || ''
    form.date = record.date
    showDialog.value = true
  } else if (cmd === 'delete') {
    ElMessageBox.confirm('确定删除这条记录？', '删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(async () => {
      try {
        await deleteRecord(record._id)
        ElMessage.success('已删除')
        loadAll()
      } catch {
        ElMessage.error('删除失败')
      }
    }).catch(() => {})
  }
}

async function handleSave() {
  if (!form.amount || parseFloat(form.amount) <= 0) {
    ElMessage.warning('请输入有效金额')
    return
  }
  if (!form.category) {
    ElMessage.warning('请选择分类')
    return
  }
  saving.value = true
  try {
    const data = {
      type: form.type,
      amount: parseFloat(form.amount),
      category: form.category,
      note: form.note,
      date: form.date,
    }
    if (editingRecord.value) {
      await updateRecord(editingRecord.value._id, data)
      ElMessage.success('已更新')
    } else {
      await createRecord(data)
      ElMessage.success('已添加')
    }
    showDialog.value = false
    loadAll()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function handleResize() {
  pieChart?.resize()
  lineChart?.resize()
}

watch(currentMonth, () => {
  loadAll()
})

onMounted(() => {
  loadAll()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  pieChart?.dispose()
  lineChart?.dispose()
})
</script>

<style scoped>
.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 16px;
}

/* 月份导航 */
.month-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 20px;
}
.month-label {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 100px;
  text-align: center;
}

/* 汇总卡片 */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}
.summary-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.summary-label {
  font-size: 13px;
  color: var(--text-secondary);
}
.summary-value {
  font-size: 22px;
  font-weight: 700;
}
.summary-value.income { color: #2ecc71; }
.summary-value.expense { color: #e74c3c; }

/* 图表 */
.charts-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}
.chart-wrapper {
  padding: 20px;
  position: relative;
}
.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px;
}
.chart-container {
  width: 100%;
  height: 260px;
}
.chart-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--text-muted);
  font-size: 13px;
}

/* 筛选 */
.filter-bar {
  margin-bottom: 16px;
}

/* 记录列表 */
.date-group {
  margin-bottom: 16px;
}
.date-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 4px;
}
.date-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.date-summary {
  font-size: 12px;
  color: var(--text-muted);
}

.record-list {
  display: flex;
  flex-direction: column;
}
.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 8px;
  border-bottom: 1px solid var(--border-light, rgba(0,0,0,0.04));
  transition: background 0.15s;
}
.record-item:hover {
  background: var(--bg-secondary, rgba(0,0,0,0.02));
}
.record-item:last-child {
  border-bottom: none;
}

.record-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.record-category-icon {
  font-size: 24px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: 10px;
}
.record-info {
  display: flex;
  flex-direction: column;
}
.record-category {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}
.record-note {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.record-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.record-amount {
  font-size: 16px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.record-amount.income { color: #2ecc71; }
.record-amount.expense { color: #e74c3c; }

.more-btn {
  color: var(--text-muted);
}

/* FAB */
.fab-btn {
  position: fixed;
  right: 32px;
  bottom: 32px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--accent, #C45A3C);
  color: #fff;
  border: none;
  box-shadow: 0 4px 16px rgba(196, 90, 60, 0.35);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s, box-shadow 0.2s;
  z-index: 100;
}
.fab-btn:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(196, 90, 60, 0.45);
}

/* 分类选择器 */
.category-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.category-tag {
  padding: 6px 14px;
  border-radius: 16px;
  font-size: 13px;
  cursor: pointer;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border: 1.5px solid transparent;
  transition: all 0.15s;
}
.category-tag:hover {
  border-color: var(--accent);
}
.category-tag.selected {
  border-color: var(--accent);
  background: rgba(196, 90, 60, 0.08);
  color: var(--accent);
  font-weight: 500;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: var(--text-muted);
  font-size: 14px;
  gap: 12px;
}

@media (max-width: 767px) {
  .summary-cards {
    grid-template-columns: 1fr;
  }
  .charts-section {
    grid-template-columns: 1fr;
  }
  .fab-btn {
    right: 20px;
    bottom: 20px;
  }
  .summary-value {
    font-size: 18px;
  }
}
</style>
