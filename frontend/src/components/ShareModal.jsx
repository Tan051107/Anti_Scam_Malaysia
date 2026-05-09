import React, { useState } from 'react'
import { X, Share2, Loader2, CheckCircle, Lock } from 'lucide-react'
import { Link } from 'react-router-dom'
import { shareToCommmunity } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'

export default function ShareModal({ analysisData, onClose }) {
  const { user } = useAuth()
  const { t } = useLanguage()

  const [note, setNote]           = useState('')
  const [anonymous, setAnonymous] = useState(false)
  const [loading, setLoading]     = useState(false)
  const [success, setSuccess]     = useState(false)
  const [error, setError]         = useState(null)

  const handleShare = async () => {
    setError(null)
    setLoading(true)
    try {
      await shareToCommmunity({
        original_message: analysisData.lastMessage,
        risk_score: analysisData.risk_score,
        risk_level: analysisData.risk_level,
        indicators: analysisData.indicators,
        note: note.trim() || null,
        anonymous,
      })
      setSuccess(true)
      setTimeout(onClose, 1800)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to share. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Share2 className="w-5 h-5 text-blue-600" />
            <h2 className="font-bold text-gray-900">{t('share_title')}</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {success ? (
            <div className="text-center py-6">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <p className="font-bold text-gray-900">{t('share_success')}</p>
            </div>
          ) : !user ? (
            /* Not logged in */
            <div className="text-center py-6">
              <Lock className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-600 mb-4">{t('community_login_prompt')}</p>
              <div className="flex gap-3 justify-center">
                <Link
                  to="/login?from=/analysis"
                  onClick={onClose}
                  className="bg-brand-primary hover:bg-blue-800 text-white font-bold px-5 py-2 rounded-xl text-sm transition-colors"
                >
                  {t('nav_login')}
                </Link>
                <Link
                  to="/signup?from=/analysis"
                  onClick={onClose}
                  className="bg-brand-secondary hover:bg-red-700 text-white font-bold px-5 py-2 rounded-xl text-sm transition-colors"
                >
                  {t('nav_signup')}
                </Link>
              </div>
            </div>
          ) : (
            <>
              {/* Risk summary */}
              <div className="bg-gray-50 border border-gray-200 rounded-xl p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-500">Risk Score</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                    analysisData.risk_level === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                    analysisData.risk_level === 'HIGH'     ? 'bg-orange-100 text-orange-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {analysisData.risk_level} — {analysisData.risk_score}%
                  </span>
                </div>
                <p className="text-xs text-gray-600 line-clamp-2">{analysisData.lastMessage}</p>
              </div>

              {/* Note */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('share_desc')}
                </label>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder={t('share_desc_placeholder')}
                  rows={3}
                  className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Anonymous toggle */}
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={anonymous}
                  onChange={(e) => setAnonymous(e.target.checked)}
                  className="w-4 h-4 accent-blue-600"
                />
                <span className="text-sm text-gray-600">{t('share_anonymous')}</span>
              </label>

              {error && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-xl">
                  {error}
                </p>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-1">
                <button
                  onClick={handleShare}
                  disabled={loading}
                  className="flex-1 bg-brand-primary hover:bg-blue-800 disabled:bg-gray-300 text-white font-bold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2 text-sm"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  {t('share_submit')}
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-2.5 rounded-xl transition-colors text-sm"
                >
                  {t('share_cancel')}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
