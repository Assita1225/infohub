<template>
  <div class="lock-page">
    <div class="lock-card">
      <h1 class="lock-title">InfoHub</h1>
      <p class="lock-subtitle">个人信息聚合与智能分析终端</p>
      <el-form @submit.prevent="handleUnlock" class="lock-form">
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="请输入密码解锁"
            size="large"
            show-password
            @keyup.enter="handleUnlock"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="lock-btn"
          @click="handleUnlock"
        >
          解锁
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()
const password = ref('')
const loading = ref(false)

async function handleUnlock() {
  if (!password.value) {
    ElMessage.warning('请输入密码')
    return
  }
  loading.value = true
  try {
    await auth.unlock(password.value)
    ElMessage.success('解锁成功')
    router.push('/dashboard')
  } catch (e) {
    const msg = e.response?.data?.message || '解锁失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.lock-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.lock-card {
  background: #fff;
  border-radius: 12px;
  padding: 48px 40px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  text-align: center;
}

.lock-title {
  font-size: 28px;
  color: #303133;
  margin-bottom: 8px;
}

.lock-subtitle {
  font-size: 14px;
  color: #909399;
  margin-bottom: 32px;
}

.lock-form {
  margin-top: 16px;
}

.lock-btn {
  width: 100%;
}
</style>
