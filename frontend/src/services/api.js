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
export async function sendAnalysisMessage(message, sessionId = null) {
  const res = await api.post('/analysis/chat', { message, session_id: sessionId })
  return res.data
}

export async function uploadAnalysisImage(file, sessionId = null) {
  const formData = new FormData()
  formData.append('file', file)
  if (sessionId) formData.append('session_id', sessionId)
  const res = await api.post('/analysis/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

// ─────────────────────────────────────────────
// Scam Simulator
// ─────────────────────────────────────────────
export async function sendSimulatorMessage(message, sessionId = null) {
  const res = await api.post('/simulator/chat', { message, session_id: sessionId })
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
  const res = await api.post('/auth/login', { email, password })
  return res.data
}

export async function apiSignup(email, password, display_name) {
  const res = await api.post('/auth/signup', { email, password, display_name })
  return res.data
}

// ─────────────────────────────────────────────
// Community
// ─────────────────────────────────────────────
export async function getCommunityPosts(limit = 20, offset = 0) {
  const res = await api.get('/community', { params: { limit, offset } })
  return res.data
}

export async function getRecentPosts(limit = 3) {
  const res = await api.get('/community/recent', { params: { limit } })
  return res.data
}

export async function shareToCommmunity(payload) {
  const res = await api.post('/community', payload)
  return res.data
}

export async function deletePost(postId) {
  const res = await api.delete(`/community/${postId}`)
  return res.data
}

// ─────────────────────────────────────────────
// Health Check
// ─────────────────────────────────────────────
export async function checkHealth() {
  const res = await api.get('/health')
  return res.data
}
