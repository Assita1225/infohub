import request from '@/common/api/request'

export const getOverviewStats = () => request.get('/overview/stats')
