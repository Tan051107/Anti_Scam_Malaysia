import React, { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { Users, AlertTriangle, Loader2, RefreshCw, Lock, Trash2, X, ZoomIn, ThumbsUp } from 'lucide-react'
import { getCommunityPosts, getMyPosts, deletePost, upvotePost } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'
import ConfirmDialog from '../components/ConfirmDialog'

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
  if (diff < 60)   return lang === 'ms' ? `${diff} saat yang lalu`              : `${diff}s ago`
  if (diff < 3600) return lang === 'ms' ? `${Math.floor(diff/60)} minit yang lalu` : `${Math.floor(diff/60)}m ago`
  if (diff < 86400) return lang === 'ms' ? `${Math.floor(diff/3600)} jam yang lalu` : `${Math.floor(diff/3600)}h ago`
  return lang === 'ms' ? `${Math.floor(diff/86400)} hari yang lalu` : `${Math.floor(diff/86400)}d ago`
}

// ─── Lightbox ────────────────────────────────────────────────
function Lightbox({ src, alt, onClose }) {
  // Close on Escape key
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <button
        className="absolute top-4 right-4 text-white bg-black/50 hover:bg-black/70 rounded-full p-2 transition-colors"
        onClick={onClose}
        aria-label="Close"
      >
        <X className="w-6 h-6" />
      </button>
      <img
        src={src}
        alt={alt}
        className="max-w-full max-h-[90vh] object-contain rounded-xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      />
    </div>
  )
}

// ─── Post Card ───────────────────────────────────────────────
function PostCard({ post, onDelete, onUpvote, currentUser, lang, t }) {
  const [deleting, setDeleting]             = useState(false)
  const [lightboxSrc, setLightboxSrc]       = useState(null)
  const [showConfirm, setShowConfirm]       = useState(false)
  const [upvoting, setUpvoting]             = useState(false)
  const [showAllIndicators, setShowAllIndicators] = useState(false)

  const handleDeleteConfirmed = async () => {
    setShowConfirm(false)
    setDeleting(true)
    try {
      await deletePost(post.id)
      onDelete(post.id)
    } catch (_) {}
    setDeleting(false)
  }

  const handleUpvote = async () => {
    if (!currentUser || upvoting) return
    setUpvoting(true)
    try {
      const data = await upvotePost(post.id)
      onUpvote(post.id, data.upvote_count, data.has_upvoted)
    } catch (_) {}
    setUpvoting(false)
  }

  const isOwnPost = currentUser && currentUser.id === post.user_id
  const canUpvote = currentUser && !isOwnPost

  return (
    <>
      {lightboxSrc && (
        <Lightbox src={lightboxSrc} alt="Scam screenshot" onClose={() => setLightboxSrc(null)} />
      )}

      <ConfirmDialog
        isOpen={showConfirm}
        title={t('community_delete_title')}
        message={t('community_delete_msg')}
        confirmLabel={t('community_delete_confirm')}
        cancelLabel={t('community_delete_cancel')}
        variant="danger"
        onConfirm={handleDeleteConfirmed}
        onCancel={() => setShowConfirm(false)}
      />

      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-brand-primary flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
              {post.author_name[0].toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800 flex items-center gap-1.5">
                {post.author_name}
                {post.is_anonymous && (
                  <span className="text-xs font-normal bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">
                    anonymous
                  </span>
                )}
              </p>
              <p className="text-xs text-gray-400">{timeAgo(post.created_at, lang)}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${RISK_COLORS[post.risk_level] || RISK_COLORS.HIGH}`}>
              {post.risk_level} {post.risk_score}%
            </span>
          </div>
        </div>

        {/* Risk bar */}
        <div className="w-full bg-gray-100 rounded-full h-1.5 mb-3">
          <div
            className={`h-1.5 rounded-full ${RISK_BAR[post.risk_level] || RISK_BAR.HIGH}`}
            style={{ width: `${post.risk_score}%` }}
          />
        </div>

        {/* Scam image — clickable to enlarge */}
        {post.image_url && (
          <div
            className="relative mb-3 rounded-xl overflow-hidden border border-gray-200 cursor-zoom-in group"
            onClick={() => setLightboxSrc(post.image_url)}
          >
            <img
              src={post.image_url}
              alt="Shared scam screenshot"
              className="w-full max-h-48 object-cover transition-transform group-hover:scale-[1.02]"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
              <ZoomIn className="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity drop-shadow-lg" />
            </div>
          </div>
        )}

        {/* Extracted / suspicious message */}
        {post.original_message && (
          <div className="bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 mb-3">
            <p className="text-xs text-gray-500 mb-0.5 font-medium flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-orange-500" />
              {post.image_url ? t('community_extracted_msg') : t('community_suspicious_content')}
            </p>
            <p className="text-sm text-gray-700 break-words whitespace-pre-wrap md:line-clamp-none line-clamp-4">
              {post.original_message}
            </p>
          </div>
        )}

        {/* User note */}
        {post.note && (
          <p className="text-sm text-gray-600 italic mb-3 border-l-2 border-blue-300 pl-3">
            "{post.note}"
          </p>
        )}

        {/* Indicators */}
        {post.indicators?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {(showAllIndicators ? post.indicators : post.indicators.slice(0, 4)).map((ind, i) => (
              <span key={i} className="text-xs bg-red-50 text-red-700 border border-red-100 px-2 py-0.5 rounded-full flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                <span className="line-clamp-1 max-w-[180px]">{ind}</span>
              </span>
            ))}
            {post.indicators.length > 4 && (
              <button
                onClick={() => setShowAllIndicators((v) => !v)}
                className="text-xs text-brand-primary hover:text-brand-primary-dark font-medium px-2 py-0.5 rounded-full border border-brand-primary/30 hover:bg-brand-primary/5 transition-colors"
              >
                {showAllIndicators
                  ? t('community_show_less') || 'Show less'
                  : `+${post.indicators.length - 4} ${t('community_more_indicators')}`}
              </button>
            )}
          </div>
        )}

        {/* Footer: upvote + delete */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-100 mt-2">
          {/* Upvote button — hidden for own posts */}
          {!isOwnPost && (
            <button
              onClick={handleUpvote}
              disabled={!currentUser || upvoting}
              title={
                !currentUser ? t('community_upvote_login')
                : post.has_upvoted ? t('community_upvote_remove')
                : t('community_upvote_seen')
              }
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-semibold transition-all
                ${post.has_upvoted
                  ? 'bg-brand-primary text-white shadow-sm'
                  : currentUser
                    ? 'bg-gray-100 text-gray-600 hover:bg-brand-primary/10 hover:text-brand-primary'
                    : 'bg-gray-50 text-gray-300 cursor-not-allowed'
                }`}
            >
              {upvoting
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <ThumbsUp className="w-4 h-4" />
              }
              <span>{post.upvote_count}</span>
              <span className="text-xs font-normal hidden sm:inline">
                {post.has_upvoted ? t('community_seen_it') : t('community_seen_scam')}
              </span>
            </button>
          )}

          {/* Upvote count (read-only) for own posts */}
          {isOwnPost && post.upvote_count > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-400">
              <ThumbsUp className="w-4 h-4" />
              <span>{post.upvote_count}</span>
              <span className="text-xs hidden sm:inline">{t('community_people_seen')}</span>
            </div>
          )}

          {/* Delete (own post only) */}
          {isOwnPost && (
            <button
              onClick={() => setShowConfirm(true)}
              disabled={deleting}
              className="text-gray-300 hover:text-red-500 transition-colors p-1.5 ml-auto"
              title="Delete post"
            >
              {deleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>
    </>
  )
}

// ─── Page ────────────────────────────────────────────────────
export default function Community() {
  const { user } = useAuth()
  const { t, lang } = useLanguage()

  const [activeTab, setActiveTab] = useState('all')  // 'all' | 'mine'
  const [posts, setPosts]         = useState([])
  const [total, setTotal]         = useState(0)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)
  const [offset, setOffset]       = useState(0)
  const LIMIT = 12

  const fetchPosts = useCallback(async (tab = activeTab, off = 0) => {
    setLoading(true)
    setError(null)
    try {
      const data = tab === 'mine'
        ? await getMyPosts(LIMIT, off)
        : await getCommunityPosts(LIMIT, off)
      if (off === 0) {
        setPosts(data.posts)
      } else {
        setPosts((prev) => [...prev, ...data.posts])
      }
      setTotal(data.total)
      setOffset(off)
    } catch {
      setError('Could not load posts. Please ensure the backend is running.')
    } finally {
      setLoading(false)
    }
  }, [activeTab])

  useEffect(() => { fetchPosts(activeTab, 0) }, [activeTab])

  const handleTabChange = (tab) => {
    if (tab === activeTab) return
    setActiveTab(tab)
    setPosts([])
    setOffset(0)
  }

  const handleDelete = (id) => {
    setPosts((prev) => prev.filter((p) => p.id !== id))
    setTotal((n) => n - 1)
  }

  const handleUpvote = (id, upvote_count, has_upvoted) => {
    setPosts((prev) => prev
      .map((p) => p.id === id ? { ...p, upvote_count, has_upvoted } : p)
      .sort((a, b) => b.upvote_count - a.upvote_count || new Date(b.created_at) - new Date(a.created_at))
    )
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
            <p className="text-blue-200 text-sm">{total} {t('community_cases_shared')}</p>
            {user ? (
              <Link
                to="/analysis"
                className="bg-brand-accent hover:bg-brand-accent-dark text-brand-primary font-bold text-sm px-4 py-2 rounded-xl transition-colors"
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

        {/* Tab switcher */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex bg-gray-200 rounded-xl p-1 gap-1">
            <button
              onClick={() => handleTabChange('all')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'all'
                  ? 'bg-white text-brand-primary shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t('community_all_posts')}
            </button>
            {user && (
              <button
                onClick={() => handleTabChange('mine')}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  activeTab === 'mine'
                    ? 'bg-white text-brand-primary shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {t('community_my_posts')}
              </button>
            )}
          </div>

          <button
            onClick={() => fetchPosts(activeTab, 0)}
            disabled={loading}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {t('community_refresh')}
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
            <Loader2 className="w-8 h-8 animate-spin text-brand-primary" />
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-20">
            <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">
              {activeTab === 'mine'
                ? t('community_no_own_posts')
                : t('community_empty')
              }
            </p>
            <Link to="/analysis" className="mt-4 inline-block text-brand-primary font-semibold hover:underline text-sm">
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
                  onUpvote={handleUpvote}
                  currentUser={user}
                  lang={lang}
                  t={t}
                />
              ))}
            </div>

            {posts.length < total && (
              <div className="text-center mt-8">
                <button
                  onClick={() => fetchPosts(activeTab, offset + LIMIT)}
                  disabled={loading}
                className="bg-brand-primary hover:bg-brand-primary-dark text-white font-bold px-6 py-2.5 rounded-xl transition-colors flex items-center gap-2 mx-auto"
                >
                  {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                  {t('community_load_more')}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
