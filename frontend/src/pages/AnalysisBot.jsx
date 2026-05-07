import React, { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, X, AlertCircle, Loader2 } from 'lucide-react'
import ChatBubble from '../components/ChatBubble'
import RiskGauge from '../components/RiskGauge'
import { sendAnalysisMessage, uploadAnalysisImage } from '../services/api'

const WELCOME_MESSAGE = {
  id: 'welcome',
  isBot: true,
  text:
    'Selamat datang! / Welcome!\n\n' +
    'Saya adalah bot analisis penipuan Malaysia. Anda boleh:\n' +
    'I am the Malaysia scam analysis bot. You can:\n\n' +
    '• Tampal mesej mencurigakan / Paste suspicious messages\n' +
    '• Hantar URL atau pautan / Send URLs or links\n' +
    '• Masukkan nombor telefon / Enter phone numbers\n' +
    '• Muat naik tangkapan skrin / Upload screenshots\n\n' +
    'Saya akan menganalisis dan memberikan penilaian risiko. / I will analyze and provide a risk assessment.',
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
}

export default function AnalysisBot() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [riskData, setRiskData] = useState({ score: 0, level: 'LOW', confidence: 0, indicators: [] })
  const [attachedFile, setAttachedFile] = useState(null)
  const [error, setError] = useState(null)

  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addMessage = (text, isBot, timestamp) => {
    setMessages((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), text, isBot, timestamp },
    ])
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed && !attachedFile) return
    if (loading) return

    setError(null)
    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    if (attachedFile) {
      addMessage(`📎 [Image: ${attachedFile.name}]`, false, ts)
      setAttachedFile(null)
      setLoading(true)
      try {
        const data = await uploadAnalysisImage(attachedFile, sessionId)
        if (data.session_id) setSessionId(data.session_id)
        setRiskData({
          score: data.risk_score,
          level: data.risk_level,
          confidence: data.confidence,
          indicators: data.indicators,
        })
        addMessage(data.reply, true, new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
      } catch (err) {
        setError('Failed to upload image. Please ensure the backend is running.')
      } finally {
        setLoading(false)
      }
      return
    }

    addMessage(trimmed, false, ts)
    setInput('')
    setLoading(true)

    try {
      const data = await sendAnalysisMessage(trimmed, sessionId)
      if (data.session_id) setSessionId(data.session_id)
      setRiskData({
        score: data.risk_score,
        level: data.risk_level,
        confidence: data.confidence,
        indicators: data.indicators,
      })
      addMessage(data.reply, true, new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
    } catch (err) {
      setError('Cannot connect to backend. Please ensure the API server is running on port 8000.')
      addMessage(
        '⚠️ Ralat sambungan / Connection error. Sila pastikan pelayan API berjalan. / Please ensure the API server is running.',
        true,
        new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      )
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) setAttachedFile(file)
    e.target.value = ''
  }

  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'LOW':      return 'text-green-600 bg-green-50 border-green-200'
      case 'MEDIUM':   return 'text-yellow-700 bg-yellow-50 border-yellow-200'
      case 'HIGH':     return 'text-orange-700 bg-orange-50 border-orange-200'
      case 'CRITICAL': return 'text-red-700 bg-red-50 border-red-200'
      default:         return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className="h-[calc(100vh-5rem)] flex flex-col">
      {/* Page header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3">
        <div className="bg-blue-600 p-2 rounded-lg">
          <AlertCircle className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-gray-900">Analysis Bot</h1>
          <p className="text-xs text-gray-500">Bot Analisis Penipuan Malaysia</p>
        </div>
      </div>

      {/* Split layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT — Chat */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-gray-200">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 scrollbar-thin scrollbar-thumb-gray">
            {messages.map((msg) => (
              <ChatBubble
                key={msg.id}
                message={msg.text}
                isBot={msg.isBot}
                timestamp={msg.timestamp}
              />
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-gray-400 text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Menganalisis... / Analyzing...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Error banner */}
          {error && (
            <div className="mx-4 mb-2 bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Attached file preview */}
          {attachedFile && (
            <div className="mx-4 mb-2 bg-blue-50 border border-blue-200 text-blue-700 text-xs px-3 py-2 rounded-lg flex items-center justify-between">
              <span>📎 {attachedFile.name}</span>
              <button onClick={() => setAttachedFile(null)}>
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Input bar */}
          <div className="bg-white border-t border-gray-200 p-3">
            <div className="flex items-end gap-2 bg-gray-100 rounded-xl px-3 py-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-gray-400 hover:text-blue-600 transition-colors flex-shrink-0 mb-1"
                title="Attach image"
              >
                <Paperclip className="w-5 h-5" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileChange}
              />
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Hantar mesej yang mencurigakan... / Paste suspicious message, URL, phone number..."
                className="flex-1 bg-transparent resize-none outline-none text-sm text-gray-800 placeholder-gray-400 max-h-32 min-h-[2rem]"
                rows={1}
                style={{ height: 'auto' }}
                onInput={(e) => {
                  e.target.style.height = 'auto'
                  e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px'
                }}
              />
              <button
                onClick={handleSend}
                disabled={loading || (!input.trim() && !attachedFile)}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white p-2 rounded-lg transition-colors flex-shrink-0"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-1 text-center">
              Press Enter to send • Shift+Enter for new line
            </p>
          </div>
        </div>

        {/* RIGHT — Risk Dashboard */}
        <div className="w-80 xl:w-96 flex-shrink-0 bg-white overflow-y-auto">
          <div className="p-5">
            <h2 className="font-bold text-gray-900 mb-1">Risk Assessment</h2>
            <p className="text-xs text-gray-500 mb-5">Penilaian Risiko Penipuan</p>

            {/* Gauge */}
            <RiskGauge
              score={riskData.score}
              riskLevel={riskData.level}
              confidence={riskData.confidence}
            />

            {/* Indicators */}
            <div className="mt-6">
              <h3 className="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-orange-500" />
                Scam Indicators / Petanda Penipuan
              </h3>
              {riskData.indicators.length === 0 ? (
                <p className="text-xs text-gray-400 italic">
                  No indicators detected yet. Send a message to analyze.
                </p>
              ) : (
                <ul className="space-y-2">
                  {riskData.indicators.map((indicator, i) => (
                    <li
                      key={i}
                      className={`text-xs px-3 py-2 rounded-lg border flex items-start gap-2 ${getRiskLevelColor(riskData.level)}`}
                    >
                      <span className="mt-0.5 flex-shrink-0">⚠️</span>
                      <span>{indicator}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Tips */}
            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4">
              <h3 className="font-semibold text-blue-800 text-sm mb-2">💡 Tips</h3>
              <ul className="text-xs text-blue-700 space-y-1">
                <li>• Never share OTP with anyone</li>
                <li>• Banks never call asking for passwords</li>
                <li>• Verify via official hotlines only</li>
                <li>• Jangan kongsi OTP dengan sesiapa</li>
                <li>• Bank tidak pernah minta kata laluan</li>
              </ul>
            </div>

            {/* Hotlines */}
            <div className="mt-4 bg-red-50 border border-red-200 rounded-xl p-4">
              <h3 className="font-semibold text-red-800 text-sm mb-2">🚨 Report Scam</h3>
              <div className="text-xs text-red-700 space-y-1">
                <div>CCID Polis: <strong>03-2610 5000</strong></div>
                <div>BNM TELELINK: <strong>1-300-88-5465</strong></div>
                <div>Emergency: <strong>997</strong></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
