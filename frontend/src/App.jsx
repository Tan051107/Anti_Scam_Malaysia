import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import AnalysisBot from './pages/AnalysisBot'
import ScamSimulator from './pages/ScamSimulator'
import ReportSimulator from './pages/ReportSimulator'
import Community from './pages/Community'
import AuthPage from './pages/AuthPage'
import { LanguageProvider, useLanguage } from './context/LanguageContext'
import { AuthProvider } from './context/AuthContext'

function AppFooter() {
  const { lang } = useLanguage()
  return (
    <footer className="bg-gray-900 text-gray-400 text-center py-4 text-sm">
      <p>
        © 2026 Anti-Scam Malaysia &nbsp;|&nbsp;{' '}
        {lang === 'ms' ? 'Untuk kecemasan, hubungi' : 'For emergencies, call'}{' '}
        <span className="text-yellow-400 font-semibold">997</span>{' '}
        {lang === 'ms' ? 'atau' : 'or'} CCID Polis{' '}
        <span className="text-yellow-400 font-semibold">03-2610 5000</span>
      </p>
    </footer>
  )
}

export default function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <div className="min-h-screen flex flex-col bg-gray-50">
          <Navbar />
          <main className="flex-1">
            <Routes>
              <Route path="/"          element={<Home />} />
              <Route path="/analysis"  element={<AnalysisBot />} />
              <Route path="/simulator" element={<ScamSimulator />} />
              <Route path="/report"    element={<ReportSimulator />} />
              <Route path="/community" element={<Community />} />
              <Route path="/login"     element={<AuthPage mode="login" />} />
              <Route path="/signup"    element={<AuthPage mode="signup" />} />
            </Routes>
          </main>
          <AppFooter />
        </div>
      </AuthProvider>
    </LanguageProvider>
  )
}
