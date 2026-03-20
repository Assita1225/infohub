import request from '@/common/api/request'

// 笔记 CRUD
export const getNotes = (params) => request.get('/notes/', { params })
export const createNote = (data) => request.post('/notes/', data)
export const getNote = (id) => request.get(`/notes/${id}`)
export const updateNote = (id, data) => request.put(`/notes/${id}`, data)
export const deleteNote = (id) => request.delete(`/notes/${id}`)

// 恢复 & 回收站
export const restoreNote = (id) => request.post(`/notes/${id}/restore`)
export const getTrashNotes = (params) => request.get('/notes/trash', { params })

// 全文搜索
export const searchNotes = (params) => request.get('/notes/search', { params })

// 导出
export const exportNote = (id) =>
  request.get(`/notes/${id}/export`, { responseType: 'blob' })
export const exportNotesBatch = (ids) =>
  request.post('/notes/export-batch', { ids }, { responseType: 'blob' })
