import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─────────────────────────────────────────────
// Analysis Bot API
// ─────────────────────────────────────────────

/**
 * Send a text message to the analysis bot.
 * @param {string} message
 * @param {string|null} sessionId
 * @returns {Promise<{reply, risk_score, risk_level, indicators, confidence, session_id}>}
 */
export async function sendAnalysisMessage(message, sessionId = null) {
  const response = await api.post('/analysis/chat', {
    message,
    session_id: sessionId,
  })
  return response.data
}

/**
 * Upload an image for scam analysis.
 * @param {File} file
 * @param {string|null} sessionId
 * @returns {Promise<{reply, risk_score, risk_level, indicators, confidence, filename}>}
 */
export async function uploadAnalysisImage(file, sessionId = null) {
  const formData = new FormData()
  formData.append('file', file)
  if (sessionId) formData.append('session_id', sessionId)

  const response = await api.post('/analysis/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

// ─────────────────────────────────────────────
// Scam Simulator API
// ─────────────────────────────────────────────

/**
 * Send a message in the scam simulator.
 * @param {string} message
 * @param {string|null} sessionId
 * @returns {Promise<{reply, session_id, scam_ended, user_caught_scam, report}>}
 */
export async function sendSimulatorMessage(message, sessionId = null) {
  const response = await api.post('/simulator/chat', {
    message,
    session_id: sessionId,
  })
  return response.data
}

/**
 * Reset the simulator session.
 * @param {string|null} sessionId
 * @returns {Promise<{session_id, message}>}
 */
export async function resetSimulator(sessionId = null) {
  const response = await api.post('/simulator/reset', {
    session_id: sessionId,
  })
  return response.data
}

// ─────────────────────────────────────────────
// Health Check
// ─────────────────────────────────────────────

/**
 * Check API health.
 * @returns {Promise<{status, version, bedrock_configured}>}
 */
export async function checkHealth() {
  const response = await api.get('/health')
  return response.data
}

export default api
