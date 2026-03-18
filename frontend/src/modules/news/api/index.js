import request from '@/common/api/request'

// 分类
export const getCategories = () => request.get('/news/categories')

// 文章列表
export const getNewsArticles = (category, page = 1, pageSize = 20) =>
  request.get('/news/articles', { params: { category, page, page_size: pageSize } })

// 稍后读列表
export const getReadLaterList = (page = 1, pageSize = 20) =>
  request.get('/news/articles/read-later', { params: { page, page_size: pageSize } })

// 文章详情
export const getNewsArticle = (id) => request.get(`/news/articles/${id}`)

// AI 摘要
export const summarizeNewsArticle = (id) => request.post(`/news/articles/${id}/summarize`)

// 稍后读
export const addReadLater = (id) => request.post(`/news/articles/${id}/read-later`)
export const removeReadLater = (id) => request.delete(`/news/articles/${id}/read-later`)

// 转笔记
export const articleToNote = (id) => request.post(`/news/articles/${id}/to-note`)

// 刷新
export const refreshNews = () => request.post('/news/refresh')
