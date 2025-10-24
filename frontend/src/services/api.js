import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ''

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Health check
export const getHealth = async () => {
  const response = await api.get('/health')
  return response.data
}

// News endpoints
export const getNews = async ({ page = 1, pageSize = 50, source = null }) => {
  const params = {
    skip: (page - 1) * pageSize,
    limit: pageSize
  }
  if (source) params.source = source

  const response = await api.get('/api/news', { params })
  return response.data
}

export const getNewsArticle = async (id) => {
  const response = await api.get(`/api/news/${id}`)
  return response.data
}

export const refreshNews = async () => {
  const response = await api.post('/api/news/refresh')
  return response.data
}

// Cluster endpoints
export const getClusters = async ({ skip = 0, limit = 100 }) => {
  const response = await api.get('/api/clusters', { params: { skip, limit } })
  return response.data
}

export const getCluster = async (id) => {
  const response = await api.get(`/api/clusters/${id}`)
  return response.data
}

export const generateClusters = async ({ minArticles = 10, force = false }) => {
  const response = await api.post('/api/clusters/generate', { min_articles: minArticles, force })
  return response.data
}

// Trading Ideas endpoints
export const getIdeas = async ({ skip = 0, limit = 100, minConfidence = null }) => {
  const params = { skip, limit }
  if (minConfidence !== null) params.min_confidence = minConfidence

  const response = await api.get('/api/ideas', { params })
  return response.data
}

export const getIdea = async (id) => {
  const response = await api.get(`/api/ideas/${id}`)
  return response.data
}

export const generateIdeas = async ({ clusterIds = null, force = false }) => {
  const response = await api.post('/api/ideas/generate', {
    cluster_ids: clusterIds,
    force
  })
  return response.data
}

export default api
