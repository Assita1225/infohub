import request from '@/common/api/request'

export function getWidgets() {
  return request.get('/dashboard/widgets')
}

export function saveWidgets(layout) {
  return request.put('/dashboard/widgets', layout)
}

export function getWeatherCity() {
  return request.get('/dashboard/weather-city')
}

export function saveWeatherCity(city) {
  return request.put('/dashboard/weather-city', { city })
}

export function getTodos() {
  return request.get('/dashboard/todos')
}

export function createTodo(title) {
  return request.post('/dashboard/todos', { title })
}

export function updateTodo(id, data) {
  return request.put(`/dashboard/todos/${id}`, data)
}

export function deleteTodo(id) {
  return request.delete(`/dashboard/todos/${id}`)
}

// 活跃微件
export function getActiveWidgets() {
  return request.get('/dashboard/active-widgets')
}

export function saveActiveWidgets(widgets) {
  return request.put('/dashboard/active-widgets', widgets)
}

// 倒计时
export function getCountdowns() {
  return request.get('/dashboard/countdowns')
}

export function createCountdown(name, target_date) {
  return request.post('/dashboard/countdowns', { name, target_date })
}

export function deleteCountdown(id) {
  return request.delete(`/dashboard/countdowns/${id}`)
}

// 最近笔记（复用 notes API）
export function getRecentNotes() {
  return request.get('/notes/', { params: { page_size: 5, sort: 'updated_at' } })
}
