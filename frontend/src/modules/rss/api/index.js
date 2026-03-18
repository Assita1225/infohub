import request from '@/common/api/request'

// 订阅源
export const getFeeds = (group) => request.get('/rss/feeds', { params: { group } })
export const addFeed = (data) => request.post('/rss/feeds', data)
export const updateFeed = (id, data) => request.put(`/rss/feeds/${id}`, data)
export const deleteFeed = (id) => request.delete(`/rss/feeds/${id}`)
export const getFeedGroups = () => request.get('/rss/feeds/groups')
export const createGroup = (name) => request.post('/rss/feeds/groups', { name })
export const renameGroup = (oldName, newName) => request.put(`/rss/feeds/groups/${encodeURIComponent(oldName)}`, { name: newName })
export const deleteGroup = (name) => request.delete(`/rss/feeds/groups/${encodeURIComponent(name)}`)

// 刷新
export const refreshFeed = (id) => request.post(`/rss/feeds/${id}/refresh`)
export const refreshAllFeeds = () => request.post('/rss/feeds/refresh-all')

// 文章
export const getFeedArticles = (feedId, page = 1, pageSize = 20) =>
  request.get(`/rss/feeds/${feedId}/articles`, { params: { page, page_size: pageSize } })
export const getArticle = (id) => request.get(`/rss/articles/${id}`)
export const markRead = (id) => request.post(`/rss/articles/${id}/read`)
export const toggleFavorite = (id) => request.post(`/rss/articles/${id}/favorite`)

// 保存到笔记本
export const articleToNote = (id) => request.post(`/rss/articles/${id}/to-note`)

// AI 摘要
export const summarizeArticle = (id) => request.post(`/rss/articles/${id}/summarize`)

// 统计
export const getRssStats = () => request.get('/rss/stats')
