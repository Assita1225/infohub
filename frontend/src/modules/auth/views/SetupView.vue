<template>
  <div class="setup-page">
    <div class="setup-card">
      <h1 class="setup-title">欢迎使用 InfoHub</h1>
      <p class="setup-subtitle">首次使用，请设置一个访问密码</p>
      <el-form @submit.prevent="handleSetup" class="setup-form">
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="设置密码（至少 6 位）"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            show-password
            @keyup.enter="handleSetup"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          class="setup-btn"
          @click="handleSetup"
        >
          确认设置
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
const confirmPassword = ref('')
const loading = ref(false)

async function handleSetup() {
  if (password.value.length < 6) {
    ElMessage.warning('密码长度不能少于 6 位')
    return
  }
  if (password.value !== confirmPassword.value) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    await auth.setup(password.value)
    ElMessage.success('密码设置成功')
    router.push('/dashboard')
  } catch (e) {
    const msg = e.response?.data?.message || '设置失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.setup-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.setup-card {
  background: #fff;
  border-radius: 12px;
  padding: 48px 40px;
  width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  text-align: center;
}

.setup-title {
  font-size: 28px;
  color: #303133;
  margin-bottom: 8px;
}

.setup-subtitle {
  font-size: 14px;
  color: #909399;
  margin-bottom: 32px;
}

.setup-form {
  margin-top: 16px;
}

.setup-btn {
  width: 100%;
}
</style>
