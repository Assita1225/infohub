import axios from 'axios'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截：自动带上 JWT
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：统一处理错误、提取 data
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      router.push('/lock')
    }
    return Promise.reject(error)
  }
)

export default request
