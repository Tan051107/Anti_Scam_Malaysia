import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Shield, Menu, X } from 'lucide-react'

const navLinks = [
  { to: '/', label: 'Home' },
  { to: '/analysis', label: 'Analysis Bot' },
  { to: '/simulator', label: 'Scam Simulator' },
  { to: '/report', label: 'Report' },
]

export default function Navbar() {
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <nav className="bg-[#003893] shadow-lg sticky top-0 z-50">
      {/* Malaysian flag stripe */}
      <div className="h-1 bg-gradient-to-r from-[#CC0001] via-[#FFCC00] to-[#CC0001]" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="bg-[#CC0001] p-1.5 rounded-lg group-hover:bg-red-700 transition-colors">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div className="leading-tight">
              <span className="text-white font-bold text-lg tracking-tight">Anti-Scam</span>
              <span className="text-[#FFCC00] font-bold text-lg tracking-tight"> Malaysia</span>
            </div>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const active = location.pathname === link.to
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    active
                      ? 'bg-[#CC0001] text-white'
                      : 'text-blue-100 hover:bg-blue-700 hover:text-white'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
          </div>

          {/* Emergency badge */}
          <div className="hidden md:flex items-center gap-2 bg-red-700 text-white text-xs font-bold px-3 py-1.5 rounded-full">
            <span>🚨</span>
            <span>Emergency: 997</span>
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden text-white p-2"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
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
                    ? 'bg-[#CC0001] text-white'
                    : 'text-blue-100 hover:bg-blue-700 hover:text-white'
                }`}
              >
                {link.label}
              </Link>
            )
          })}
          <div className="pt-2 text-center text-red-300 text-xs font-bold">
            🚨 Emergency: 997 | CCID: 03-2610 5000
          </div>
        </div>
      )}
    </nav>
  )
}
