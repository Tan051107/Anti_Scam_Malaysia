import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)   // { id, email, username, full_name, access_token, refresh_token }
  const [loading, setLoading] = useState(true)

  // Restore session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('antiscam_user')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        setUser(parsed)
        api.defaults.headers.common['Authorization'] = `Bearer ${parsed.access_token}`
      } catch (_) {
        localStorage.removeItem('antiscam_user')
      }
    }
    setLoading(false)
  }, [])

  const _saveSession = async (tokens) => {
    // Attach token then fetch profile
    api.defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`
    const profileRes = await api.get('/auth/me')
    const userData = {
      ...profileRes.data,
      display_name: profileRes.data.full_name || profileRes.data.username,
      access_token: tokens.access_token,
      refresh_token: tokens.refresh_token,
    }
    setUser(userData)
    localStorage.setItem('antiscam_user', JSON.stringify(userData))
    return userData
  }

  const login = async (email, password) => {
    // Backend expects form data for OAuth2PasswordRequestForm
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    const res = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return await _saveSession(res.data)
  }

  const signup = async (email, password, display_name) => {
    // Split display_name into username (no spaces, lowercase)
    const username = display_name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
    const res = await api.post('/auth/signup', {
      email,
      password,
      username,
      full_name: display_name,
    })
    return await _saveSession(res.data)
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('antiscam_user')
    delete api.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
