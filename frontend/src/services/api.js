import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

export default api

// ─────────────────────────────────────────────
// Analysis Bot
// ─────────────────────────────────────────────
export async function sendAnalysisMessage(message, sessionId = null, language = 'en') {
  const res = await api.post('/analysis/chat', { message, session_id: sessionId, language })
  return res.data
}

export async function uploadAnalysisImage(file, sessionId = null, language = 'en') {
  const formData = new FormData()
  formData.append('file', file)
  if (sessionId) formData.append('session_id', sessionId)
  const res = await api.post(`/analysis/upload?language=${language}`, formData, {
    headers: { 'Content-Type': undefined },  // let axios set multipart + boundary automatically
  })
  return res.data
}

// ─────────────────────────────────────────────
// Scam Simulator
// ─────────────────────────────────────────────
export async function sendSimulatorMessage(message, sessionId = null, language = 'en') {
  const res = await api.post('/simulator/chat', { message, session_id: sessionId, language })
  return res.data
}

export async function resetSimulator(sessionId = null) {
  const res = await api.post('/simulator/reset', { session_id: sessionId })
  return res.data
}

// ─────────────────────────────────────────────
// Auth
// ─────────────────────────────────────────────
export async function apiLogin(email, password) {
  const formData = new URLSearchParams()
  formData.append('username', email)
  formData.append('password', password)
  const res = await api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

export async function apiSignup(email, password, display_name) {
  const username = display_name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
  const res = await api.post('/auth/signup', {
    email,
    password,
    username,
    full_name: display_name,
  })
  return res.data
}

export async function apiGetMe() {
  const res = await api.get('/auth/me')
  return res.data
}

export async function apiRefreshToken(refreshToken) {
  const res = await api.post('/auth/refresh', { refresh_token: refreshToken })
  return res.data
}

// ─────────────────────────────────────────────
// Community
// ─────────────────────────────────────────────
export async function getCommunityPosts(limit = 20, offset = 0) {
  const res = await api.get('/community/posts', { params: { limit, offset } })
  return res.data
}

export async function getRecentPosts(limit = 3) {
  const res = await api.get('/community/posts', { params: { limit, offset: 0 } })
  return res.data
}

export async function getMyPosts(limit = 20, offset = 0) {
  const res = await api.get('/community/posts/mine', { params: { limit, offset } })
  return res.data
}

export async function createCommunityPost(formData) {
  // Set Content-Type to undefined so axios auto-sets multipart/form-data with correct boundary
  // while still preserving the Authorization header from defaults
  const res = await api.post('/community/posts', formData, {
    headers: { 'Content-Type': undefined },
  })
  return res.data
}

export async function deletePost(postId) {
  const res = await api.delete(`/community/posts/${postId}`)
  return res.data
}

export async function upvotePost(postId) {
  const res = await api.post(`/community/posts/${postId}/upvote`)
  return res.data
}

// ─────────────────────────────────────────────
// Health Check
// ─────────────────────────────────────────────
export async function checkHealth() {
  const res = await api.get('/health')
  return res.data
}
