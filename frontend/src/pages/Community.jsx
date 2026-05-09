import React, { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Users, AlertTriangle, Loader2, RefreshCw, Lock, Trash2 } from 'lucide-react'
import { getCommunityPosts, deletePost } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'

const RISK_COLORS = {
  LOW:      'bg-green-100 text-green-800 border-green-200',
  MEDIUM:   'bg-yellow-100 text-yellow-800 border-yellow-200',
  HIGH:     'bg-orange-100 text-orange-800 border-orange-200',
  CRITICAL: 'bg-red-100 text-red-800 border-red-200',
}

const RISK_BAR = {
  LOW:      'bg-green-500',
  MEDIUM:   'bg-yellow-500',
  HIGH:     'bg-orange-500',
  CRITICAL: 'bg-red-600',
}

function timeAgo(isoString, lang) {
  const diff = Math.floor((Date.now() - new Date(isoString)) / 1000)
  if (diff < 60)  return lang === 'ms' ? `${diff} saat yang lalu` : `${diff}s ago`
  if (diff < 3600) return lang === 'ms' ? `${Math.floor(diff/60)} minit yang lalu` : `${Math.floor(diff/60)}m ago`
  if (diff < 86400) return lang === 'ms' ? `${Math.floor(diff/3600)} jam yang lalu` : `${Math.floor(diff/3600)}h ago`
  return lang === 'ms' ? `${Math.floor(diff/86400)} hari yang lalu` : `${Math.floor(diff/86400)}d ago`
}

function PostCard({ post, onDelete, currentUser, lang, t }) {
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async () => {
    if (!window.confirm('Delete this post?')) return
    setDeleting(true)
    try {
      await deletePost(post.id)
      onDelete(post.id)
    } catch (_) {}
    setDeleting(false)
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow p-5">
      {/* Header row */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-brand-primary flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
            {post.author_name[0].toUpperCase()}
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">{post.author_name}</p>
            <p className="text-xs text-gray-400">{timeAgo(post.created_at, lang)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${RISK_COLORS[post.risk_level] || RISK_COLORS.HIGH}`}>
            {post.risk_level} {post.risk_score}%
          </span>
          {currentUser && (
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="text-gray-300 hover:text-red-500 transition-colors"
              title="Delete post"
            >
              {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Risk bar */}
      <div className="w-full bg-gray-100 rounded-full h-1.5 mb-3">
        <div
          className={`h-1.5 rounded-full ${RISK_BAR[post.risk_level] || RISK_BAR.HIGH}`}
          style={{ width: `${post.risk_score}%` }}
        />
      </div>

      {/* Message preview */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 mb-3">
        <p className="text-xs text-gray-500 mb-0.5 font-medium">Suspicious content:</p>
        <p className="text-sm text-gray-700 line-clamp-3 break-words">{post.original_message}</p>
      </div>

      {/* User note */}
      {post.note && (
        <p className="text-sm text-gray-600 italic mb-3 border-l-2 border-blue-300 pl-3">
          "{post.note}"
        </p>
      )}

      {/* Indicators */}
      {post.indicators?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {post.indicators.slice(0, 4).map((ind, i) => (
            <span key={i} className="text-xs bg-red-50 text-red-700 border border-red-100 px-2 py-0.5 rounded-full flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 flex-shrink-0" />
              <span className="line-clamp-1 max-w-[180px]">{ind}</span>
            </span>
          ))}
          {post.indicators.length > 4 && (
            <span className="text-xs text-gray-400">+{post.indicators.length - 4} more</span>
          )}
        </div>
      )}
    </div>
  )
}

export default function Community() {
  const { user } = useAuth()
  const { t, lang } = useLanguage()

  const [posts, setPosts]     = useState([])
  const [total, setTotal]     = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [offset, setOffset]   = useState(0)
  const LIMIT = 12

  const fetchPosts = useCallback(async (off = 0) => {
    setLoading(true)
    setError(null)
    try {
      const data = await getCommunityPosts(LIMIT, off)
      if (off === 0) {
        setPosts(data.posts)
      } else {
        setPosts((prev) => [...prev, ...data.posts])
      }
      setTotal(data.total)
      setOffset(off)
    } catch (err) {
      setError('Could not load community posts. Please ensure the backend is running.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchPosts(0) }, [fetchPosts])

  const handleDelete = (id) => {
    setPosts((prev) => prev.filter((p) => p.id !== id))
    setTotal((t) => t - 1)
  }

  return (
    <div className="min-h-[calc(100vh-5rem)] bg-gray-50">
      {/* Page header */}
      <div className="bg-brand-primary text-white px-6 py-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-brand-secondary p-2 rounded-lg">
              <Users className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold">{t('community_title')}</h1>
              <p className="text-blue-200 text-sm">{t('community_subtitle')}</p>
            </div>
          </div>
          <div className="flex items-center justify-between mt-4">
            <p className="text-blue-200 text-sm">{total} {lang === 'ms' ? 'kes dikongsi' : 'cases shared'}</p>
            {user ? (
              <Link
                to="/analysis"
                className="bg-brand-accent hover:bg-yellow-400 text-brand-primary font-bold text-sm px-4 py-2 rounded-xl transition-colors"
              >
                + {t('community_share')}
              </Link>
            ) : (
              <Link
                to="/login?from=/community"
                className="bg-white/20 hover:bg-white/30 text-white font-bold text-sm px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5"
              >
                <Lock className="w-4 h-4" />
                {t('community_login_prompt')}
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Refresh */}
        <div className="flex justify-end mb-4">
          <button
            onClick={() => fetchPosts(0)}
            disabled={loading}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl mb-6 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        {loading && posts.length === 0 ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-20">
            <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">{t('community_empty')}</p>
            <Link to="/analysis" className="mt-4 inline-block text-blue-600 font-semibold hover:underline text-sm">
              {t('community_share')} →
            </Link>
          </div>
        ) : (
          <>
            <div className="grid md:grid-cols-2 gap-4">
              {posts.map((post) => (
                <PostCard
                  key={post.id}
                  post={post}
                  onDelete={handleDelete}
                  currentUser={user}
                  lang={lang}
                  t={t}
                />
              ))}
            </div>

            {/* Load more */}
            {posts.length < total && (
              <div className="text-center mt-8">
                <button
                  onClick={() => fetchPosts(offset + LIMIT)}
                  disabled={loading}
                  className="bg-brand-primary hover:bg-blue-800 text-white font-bold px-6 py-2.5 rounded-xl transition-colors flex items-center gap-2 mx-auto"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  {lang === 'ms' ? 'Muatkan Lagi' : 'Load More'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
