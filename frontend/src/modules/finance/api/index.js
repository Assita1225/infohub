import request from '@/common/api/request'

export const getRecords = (params) => request.get('/finance/records', { params })
export const createRecord = (data) => request.post('/finance/records', data)
export const updateRecord = (id, data) => request.put(`/finance/records/${id}`, data)
export const deleteRecord = (id) => request.delete(`/finance/records/${id}`)
export const getSummary = (month) => request.get('/finance/summary', { params: { month } })
export const getTrend = (year) => request.get('/finance/trend', { params: { year } })
export const getCategories = () => request.get('/finance/categories')
