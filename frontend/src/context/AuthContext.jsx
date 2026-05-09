import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)   // { id, email, display_name, token }
  const [loading, setLoading] = useState(true)

  // Restore session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('antiscam_user')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        setUser(parsed)
        // Attach token to all future axios requests
        api.defaults.headers.common['Authorization'] = `Bearer ${parsed.token}`
      } catch (_) {
        localStorage.removeItem('antiscam_user')
      }
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    const userData = res.data
    setUser(userData)
    localStorage.setItem('antiscam_user', JSON.stringify(userData))
    api.defaults.headers.common['Authorization'] = `Bearer ${userData.token}`
    return userData
  }

  const signup = async (email, password, display_name) => {
    const res = await api.post('/auth/signup', { email, password, display_name })
    const userData = res.data
    setUser(userData)
    localStorage.setItem('antiscam_user', JSON.stringify(userData))
    api.defaults.headers.common['Authorization'] = `Bearer ${userData.token}`
    return userData
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
