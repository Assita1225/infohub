import request from '@/common/api/request'

// 习惯 CRUD
export const getHabits = () => request.get('/habits/')
export const createHabit = (data) => request.post('/habits/', data)
export const updateHabit = (id, data) => request.put(`/habits/${id}`, data)
export const deleteHabit = (id) => request.delete(`/habits/${id}`)

// 打卡
export const checkIn = (id) => request.post(`/habits/${id}/check-in`)
export const cancelCheckIn = (id) => request.delete(`/habits/${id}/check-in`)

// 历史 & 统计
export const getHistory = (id, year) => request.get(`/habits/${id}/history`, { params: { year } })
export const getStats = () => request.get('/habits/stats')
