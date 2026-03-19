<template>
  <div class="setup-page">
    <div class="setup-card">
      <div class="setup-brand">
        <h1 class="setup-logo">InfoHub</h1>
        <p class="setup-slogan">你的个人信息中枢</p>
      </div>
      <p class="setup-hint">首次使用，请设置一个访问密码</p>
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
  background: linear-gradient(160deg, var(--bg-secondary) 0%, var(--bg-primary) 50%, var(--accent-light) 100%);
}

.setup-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 48px 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-lg);
  text-align: center;
}

.setup-brand {
  margin-bottom: 16px;
}

.setup-logo {
  font-family: var(--font-display);
  font-size: 32px;
  color: var(--text-primary);
  margin: 0 0 8px;
  letter-spacing: 1px;
}

.setup-slogan {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.setup-hint {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 24px;
}

.setup-form {
  margin-top: 8px;
}

.setup-btn {
  width: 100%;
  margin-top: 8px;
}
</style>
