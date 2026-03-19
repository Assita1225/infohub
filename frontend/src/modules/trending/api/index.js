import request from '@/common/api/request'

// ── Trending 热榜 ──

export const getTrendingSources = () => request.get('/trending/sources')

export const getTrendingList = (source) =>
  request.get('/trending/list', { params: { source } })

export const getWordcloudData = () => request.get('/trending/wordcloud')

export const refreshTrending = () => request.post('/trending/refresh')

// ── Recommend 推荐 ──

export const getRecommendTags = () => request.get('/recommend/tags')

export const updateSelectedTags = (selectedTags) =>
  request.put('/recommend/tags', { selected_tags: selectedTags })

export const addCustomTag = (tag) =>
  request.post('/recommend/tags/custom', { tag })

export const deleteCustomTag = (tag) =>
  request.delete(`/recommend/tags/${encodeURIComponent(tag)}`)

export const getRecommendFeed = (tagsWithWeights) =>
  request.get('/recommend/feed', {
    params: {
      tags: tagsWithWeights.map(t => `${t.name}:${t.weight}`).join(',')
    }
  })
