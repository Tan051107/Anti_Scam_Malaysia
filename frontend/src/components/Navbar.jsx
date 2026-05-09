import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Shield, Menu, X, LogOut, User } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { lang, toggleLang, t } = useLanguage()
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const navLinks = [
    { to: '/',          label: t('nav_home') },
    { to: '/analysis',  label: t('nav_analysis') },
    { to: '/simulator', label: t('nav_simulator') },
    { to: '/report',    label: t('nav_report') },
    { to: '/community', label: t('nav_community') },
  ]

  const handleLogout = () => {
    logout()
    navigate('/')
    setMenuOpen(false)
  }

  return (
    <nav className="bg-brand-primary shadow-lg sticky top-0 z-50">
      {/* Malaysian flag stripe */}
      <div className="h-1 bg-gradient-to-r from-brand-secondary via-brand-accent to-brand-secondary" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* Brand */}
          <Link to="/" className="flex items-center gap-2 group flex-shrink-0">
            <div className="bg-brand-secondary p-1.5 rounded-lg group-hover:bg-red-700 transition-colors">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div className="leading-tight">
              <span className="text-white font-bold text-lg tracking-tight">Anti-Scam</span>
              <span className="text-brand-accent font-bold text-lg tracking-tight"> Malaysia</span>
            </div>
          </Link>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-0.5">
            {navLinks.map((link) => {
              const active = location.pathname === link.to
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    active
                      ? 'bg-brand-secondary text-white'
                      : 'text-blue-100 hover:bg-blue-700 hover:text-white'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
          </div>

          {/* Right side controls */}
          <div className="hidden md:flex items-center gap-2">
            {/* Language toggle */}
            <button
              onClick={toggleLang}
              className="flex items-center gap-1 bg-white/10 hover:bg-white/20 text-white text-xs font-bold px-3 py-1.5 rounded-full transition-colors border border-white/20"
              title={lang === 'en' ? 'Switch to Bahasa Malaysia' : 'Switch to English'}
            >
              <span className={lang === 'en' ? 'text-brand-accent' : 'text-white/60'}>EN</span>
              <span className="text-white/40 mx-0.5">/</span>
              <span className={lang === 'ms' ? 'text-brand-accent' : 'text-white/60'}>BM</span>
            </button>

            {/* Auth */}
            {user ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 text-white text-xs">
                  <div className="w-6 h-6 rounded-full bg-brand-accent flex items-center justify-center text-brand-primary font-bold text-xs">
                    {user.display_name[0].toUpperCase()}
                  </div>
                  <span className="text-blue-200 max-w-[80px] truncate">{user.display_name}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1 text-blue-200 hover:text-white text-xs transition-colors"
                  title={t('nav_logout')}
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1.5">
                <Link
                  to="/login"
                  className="text-blue-100 hover:text-white text-sm font-medium transition-colors px-2 py-1"
                >
                  {t('nav_login')}
                </Link>
                <Link
                  to="/signup"
                  className="bg-brand-accent hover:bg-yellow-400 text-brand-primary text-sm font-bold px-3 py-1.5 rounded-lg transition-colors"
                >
                  {t('nav_signup')}
                </Link>
              </div>
            )}

            {/* Emergency badge */}
            <div className="bg-red-700 text-white text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1">
              <span>🚨</span>
              <span>{t('nav_emergency')}</span>
            </div>
          </div>

          {/* Mobile: language + menu button */}
          <div className="md:hidden flex items-center gap-2">
            <button
              onClick={toggleLang}
              className="bg-white/10 text-white text-xs font-bold px-2.5 py-1 rounded-full border border-white/20"
            >
              <span className={lang === 'en' ? 'text-brand-accent' : 'text-white/60'}>EN</span>
              <span className="text-white/40 mx-0.5">/</span>
              <span className={lang === 'ms' ? 'text-brand-accent' : 'text-white/60'}>BM</span>
            </button>
            <button
              className="text-white p-2"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Toggle menu"
            >
              {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden bg-blue-900 border-t border-blue-700 px-4 py-3 space-y-1">
          {navLinks.map((link) => {
            const active = location.pathname === link.to
            return (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setMenuOpen(false)}
                className={`block px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  active
                    ? 'bg-brand-secondary text-white'
                    : 'text-blue-100 hover:bg-blue-700 hover:text-white'
                }`}
              >
                {link.label}
              </Link>
            )
          })}

          <div className="border-t border-blue-700 pt-2 mt-2 space-y-1">
            {user ? (
              <>
                <div className="flex items-center gap-2 px-4 py-2 text-blue-200 text-sm">
                  <User className="w-4 h-4" />
                  {user.display_name}
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-red-300 hover:text-red-100 flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  {t('nav_logout')}
                </button>
              </>
            ) : (
              <div className="flex gap-2 px-2">
                <Link
                  to="/login"
                  onClick={() => setMenuOpen(false)}
                  className="flex-1 text-center bg-white/10 text-white text-sm font-medium py-2 rounded-lg"
                >
                  {t('nav_login')}
                </Link>
                <Link
                  to="/signup"
                  onClick={() => setMenuOpen(false)}
                  className="flex-1 text-center bg-brand-accent text-brand-primary text-sm font-bold py-2 rounded-lg"
                >
                  {t('nav_signup')}
                </Link>
              </div>
            )}
          </div>

          <div className="pt-1 text-center text-red-300 text-xs font-bold">
            🚨 {t('nav_emergency')} | CCID: 03-2610 5000
          </div>
        </div>
      )}
    </nav>
  )
}
