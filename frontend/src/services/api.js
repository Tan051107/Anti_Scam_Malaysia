import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ─── Token refresh interceptor ───────────────────────────────
// When any request gets a 401, try to refresh the access token once.
// If refresh succeeds, retry the original request.
// If refresh fails, clear the session and redirect to login.
let _isRefreshing = false
let _refreshQueue = []  // pending requests waiting for the new token

function _processQueue(error, token = null) {
  _refreshQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token)
  })
  _refreshQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    // Only intercept 401s that haven't already been retried
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }

    // Don't intercept auth endpoints themselves (login/refresh)
    if (original.url?.includes('/auth/')) {
      return Promise.reject(error)
    }

    if (_isRefreshing) {
      // Queue this request until the refresh completes
      return new Promise((resolve, reject) => {
        _refreshQueue.push({ resolve, reject })
      }).then((token) => {
        original.headers['Authorization'] = `Bearer ${token}`
        return api(original)
      })
    }

    original._retry = true
    _isRefreshing = true

    try {
      const stored = localStorage.getItem('antiscam_user')
      if (!stored) throw new Error('No session')

      const { refresh_token } = JSON.parse(stored)
      if (!refresh_token) throw new Error('No refresh token')

      const res = await api.post('/auth/refresh', { refresh_token })
      const { access_token, refresh_token: new_refresh } = res.data

      // Update stored session with new tokens
      const updated = { ...JSON.parse(localStorage.getItem('antiscam_user')), access_token, refresh_token: new_refresh }
      localStorage.setItem('antiscam_user', JSON.stringify(updated))
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

      _processQueue(null, access_token)
      original.headers['Authorization'] = `Bearer ${access_token}`
      return api(original)
    } catch (refreshError) {
      _processQueue(refreshError, null)
      // Clear session and send to login
      localStorage.removeItem('antiscam_user')
      delete api.defaults.headers.common['Authorization']
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      _isRefreshing = false
    }
  }
)

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
