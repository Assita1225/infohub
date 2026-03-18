import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/common/api/request'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const initialized = ref(false) // 是否已设置密码
  const checked = ref(false)     // 是否已完成初始检查

  function setToken(t) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function clearToken() {
    token.value = ''
    localStorage.removeItem('token')
  }

  const isLoggedIn = () => !!token.value

  async function checkStatus() {
    const res = await request.get('/auth/status')
    initialized.value = res.data.initialized
    checked.value = true
    return res.data.initialized
  }

  async function setup(password) {
    const res = await request.post('/auth/setup', { password })
    setToken(res.data.token)
    initialized.value = true
    return res
  }

  async function unlock(password) {
    const res = await request.post('/auth/unlock', { password })
    setToken(res.data.token)
    return res
  }

  async function changePassword(oldPassword, newPassword) {
    const res = await request.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
    setToken(res.data.token)
    return res
  }

  function logout() {
    clearToken()
  }

  return {
    token, initialized, checked,
    isLoggedIn, checkStatus, setup, unlock, changePassword, logout,
  }
})
