import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Shield, Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'

export default function AuthPage({ mode = 'login' }) {
  const { login, signup } = useAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()

  const [form, setForm] = useState({ email: '', password: '', display_name: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const isLogin = mode === 'login'

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      if (isLogin) {
        await login(form.email, form.password)
      } else {
        await signup(form.email, form.password, form.display_name)
      }
      // Redirect to wherever they came from, or community
      const from = new URLSearchParams(window.location.search).get('from') || '/community'
      navigate(from)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-5rem)] flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-brand-primary px-8 py-6 text-center">
            <div className="flex justify-center mb-3">
              <div className="bg-brand-secondary p-3 rounded-xl">
                <Shield className="w-7 h-7 text-white" />
              </div>
            </div>
            <h1 className="text-white text-2xl font-extrabold">
              {isLogin ? t('login_title') : t('signup_title')}
            </h1>
            <p className="text-blue-200 text-sm mt-1">Anti-Scam Malaysia</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="px-8 py-6 space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('signup_name')}
                </label>
                <input
                  name="display_name"
                  type="text"
                  required
                  value={form.display_name}
                  onChange={handleChange}
                  placeholder="e.g. Ahmad Razif"
                  className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {isLogin ? t('login_email') : t('signup_email')}
              </label>
              <input
                name="email"
                type="email"
                required
                value={form.email}
                onChange={handleChange}
                placeholder="you@example.com"
                className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {isLogin ? t('login_password') : t('signup_password')}
              </label>
              <div className="relative">
                <input
                  name="password"
                  type={showPw ? 'text' : 'password'}
                  required
                  minLength={6}
                  value={form.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  className="w-full border border-gray-300 rounded-xl px-4 py-2.5 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2.5 rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-secondary hover:bg-brand-secondary-dark disabled:bg-gray-300 text-white font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {isLogin ? t('login_btn') : t('signup_btn')}
            </button>

            <p className="text-center text-sm text-gray-500">
              {isLogin ? t('login_no_account') : t('signup_have_account')}{' '}
              <Link
                to={isLogin ? '/signup' : '/login'}
                className="text-brand-primary font-semibold hover:underline"
              >
                {isLogin ? t('login_signup_link') : t('signup_login_link')}
              </Link>
            </p>
          </form>
        </div>
      </div>
    </div>
  )
}
