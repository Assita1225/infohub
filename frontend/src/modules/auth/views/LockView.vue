<template>
  <div class="lock-page">
    <div class="lock-card">
      <div class="lock-brand">
        <h1 class="lock-logo">InfoHub</h1>
        <p class="lock-slogan">个人信息中枢</p>
      </div>
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
  background: linear-gradient(160deg, var(--bg-secondary) 0%, var(--bg-primary) 50%, var(--accent-light) 100%);
}

.lock-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 48px 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-lg);
  text-align: center;
}

.lock-brand {
  margin-bottom: 32px;
}

.lock-logo {
  font-family: var(--font-display);
  font-size: 32px;
  color: var(--text-primary);
  margin: 0 0 8px;
  letter-spacing: 1px;
}

.lock-slogan {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.lock-form {
  margin-top: 8px;
}

.lock-btn {
  width: 100%;
  margin-top: 8px;
}
</style>
