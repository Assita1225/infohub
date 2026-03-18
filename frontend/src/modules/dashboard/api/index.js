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
