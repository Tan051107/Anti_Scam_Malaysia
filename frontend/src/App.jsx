import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import AnalysisBot from './pages/AnalysisBot'
import ScamSimulator from './pages/ScamSimulator'
import ReportSimulator from './pages/ReportSimulator'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analysis" element={<AnalysisBot />} />
          <Route path="/simulator" element={<ScamSimulator />} />
          <Route path="/report" element={<ReportSimulator />} />
        </Routes>
      </main>
      <footer className="bg-gray-900 text-gray-400 text-center py-4 text-sm">
        <p>
          © 2024 Anti-Scam Malaysia &nbsp;|&nbsp; Untuk kecemasan, hubungi{' '}
          <span className="text-yellow-400 font-semibold">997</span> atau CCID Polis{' '}
          <span className="text-yellow-400 font-semibold">03-2610 5000</span>
        </p>
      </footer>
    </div>
  )
}
