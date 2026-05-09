import React, { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, X, AlertCircle, Loader2, Share2 } from 'lucide-react'
import ChatBubble from '../components/ChatBubble'
import RiskGauge from '../components/RiskGauge'
import ShareModal from '../components/ShareModal'
import { sendAnalysisMessage, uploadAnalysisImage } from '../services/api'
import { useLanguage } from '../context/LanguageContext'

export default function AnalysisBot() {
  const { t, lang } = useLanguage()

  const WELCOME_MESSAGE = {
    id: 'welcome',
    isBot: true,
    text: t('analysis_welcome'),
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }

  const [messages, setMessages]       = useState([WELCOME_MESSAGE])
  const [input, setInput]             = useState('')
  const [loading, setLoading]         = useState(false)
  const [sessionId, setSessionId]     = useState(null)
  const [riskData, setRiskData]       = useState({ score: 0, level: 'LOW', confidence: 0, indicators: [] })
  const [attachedFile, setAttachedFile] = useState(null)
  const [error, setError]             = useState(null)
  const [lastMessage, setLastMessage] = useState('')
  const [lastImageFile, setLastImageFile] = useState(null)
  const [showShare, setShowShare]     = useState(false)

  const messagesEndRef = useRef(null)
  const fileInputRef   = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addMessage = (text, isBot, imageUrl = null) => {
    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    setMessages((prev) => [...prev, { id: Date.now() + Math.random(), text, isBot, timestamp: ts, imageUrl }])
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed && !attachedFile) return
    if (loading) return

    setError(null)

    if (attachedFile) {
      const previewUrl = URL.createObjectURL(attachedFile)
      addMessage(`📎 ${attachedFile.name}`, false, previewUrl)
      const file = attachedFile
      setAttachedFile(null)
      setLoading(true)
      try {
        const data = await uploadAnalysisImage(file, sessionId)
        if (data.session_id) setSessionId(data.session_id)
        setRiskData({ score: data.risk_score, level: data.risk_level, confidence: data.confidence, indicators: data.indicators })
        setLastMessage(`[Image: ${file.name}]`)
        setLastImageFile(file)
        addMessage(data.reply, true)
      } catch {
        setError('Failed to upload image. Please ensure the backend is running.')
      } finally {
        setLoading(false)
      }
      return
    }

    addMessage(trimmed, false)
    setLastMessage(trimmed)
    setLastImageFile(null)
    setInput('')
    setLoading(true)

    try {
      const data = await sendAnalysisMessage(trimmed, sessionId)
      if (data.session_id) setSessionId(data.session_id)
      setRiskData({ score: data.risk_score, level: data.risk_level, confidence: data.confidence, indicators: data.indicators })
      addMessage(data.reply, true)
    } catch {
      setError('Cannot connect to backend. Please ensure the API server is running on port 8000.')
      addMessage('⚠️ Connection error. Please ensure the API server is running.', true)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
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

  const canShare = riskData.score >= 60 && lastMessage

  return (
    <div className="h-[calc(100vh-5rem)] flex flex-col">
      {/* Page header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3">
        <div className="bg-blue-600 p-2 rounded-lg">
          <AlertCircle className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-gray-900">{t('analysis_title')}</h1>
          <p className="text-xs text-gray-500">{t('analysis_subtitle')}</p>
        </div>
      </div>

      {/* Split layout */}
      <div className="flex-1 flex overflow-hidden">

        {/* LEFT — Chat */}
        <div className="flex-1 flex flex-col min-w-0 border-r border-gray-200">
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((msg) => (
              <ChatBubble key={msg.id} message={msg.text} isBot={msg.isBot} timestamp={msg.timestamp} imageUrl={msg.imageUrl} />
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-gray-400 text-sm">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{t('analysis_analyzing')}</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {error && (
            <div className="mx-4 mb-2 bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2 rounded-lg flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {attachedFile && (
            <div className="mx-4 mb-2 bg-blue-50 border border-blue-200 text-blue-700 text-xs px-3 py-2 rounded-lg flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <img
                  src={URL.createObjectURL(attachedFile)}
                  alt="preview"
                  className="w-10 h-10 object-cover rounded-lg border border-blue-200 flex-shrink-0"
                />
                <span className="truncate">{attachedFile.name}</span>
              </div>
              <button onClick={() => setAttachedFile(null)} className="flex-shrink-0"><X className="w-4 h-4" /></button>
            </div>
          )}

          <div className="bg-white border-t border-gray-200 p-3">
            <div className="flex items-end gap-2 bg-gray-100 rounded-xl px-3 py-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-gray-400 hover:text-blue-600 transition-colors flex-shrink-0 mb-1"
                title="Attach image"
              >
                <Paperclip className="w-5 h-5" />
              </button>
              <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={t('analysis_placeholder')}
                className="flex-1 bg-transparent resize-none outline-none text-sm text-gray-800 placeholder-gray-400 max-h-32 min-h-[2rem]"
                rows={1}
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
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-1 text-center">
              {lang === 'ms' ? 'Tekan Enter untuk hantar • Shift+Enter untuk baris baru' : 'Press Enter to send • Shift+Enter for new line'}
            </p>
          </div>
        </div>

        {/* RIGHT — Risk Dashboard */}
        <div className="w-80 xl:w-96 flex-shrink-0 bg-white overflow-y-auto">
          <div className="p-5">
            <h2 className="font-bold text-gray-900 mb-1">{t('analysis_risk_title')}</h2>
            <p className="text-xs text-gray-500 mb-5">{t('analysis_risk_subtitle')}</p>

            <RiskGauge score={riskData.score} riskLevel={riskData.level} confidence={riskData.confidence} />

            {/* Share button — shown when risk >= 60% */}
            {canShare && (
              <button
                onClick={() => setShowShare(true)}
                className="w-full mt-4 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2 text-sm"
                title={t('analysis_share_tooltip')}
              >
                <Share2 className="w-4 h-4" />
                {t('analysis_share_btn')}
              </button>
            )}

            {/* Indicators */}
            <div className="mt-6">
              <h3 className="font-semibold text-gray-800 text-sm mb-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-orange-500" />
                {t('analysis_indicators')}
              </h3>
              {riskData.indicators.length === 0 ? (
                <p className="text-xs text-gray-400 italic">{t('analysis_no_indicators')}</p>
              ) : (
                <ul className="space-y-2">
                  {riskData.indicators.map((indicator, i) => (
                    <li key={i} className={`text-xs px-3 py-2 rounded-lg border flex items-start gap-2 ${getRiskLevelColor(riskData.level)}`}>
                      <span className="mt-0.5 flex-shrink-0">⚠️</span>
                      <span>{indicator}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Tips */}
            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4">
              <h3 className="font-semibold text-blue-800 text-sm mb-2">{t('tips_title')}</h3>
              <ul className="text-xs text-blue-700 space-y-1">
                {lang === 'ms' ? (
                  <>
                    <li>• Jangan sekali-kali kongsi OTP dengan sesiapa</li>
                    <li>• Bank tidak pernah telefon minta kata laluan</li>
                    <li>• Sahkan melalui talian rasmi sahaja</li>
                  </>
                ) : (
                  <>
                    <li>• Never share OTP with anyone</li>
                    <li>• Banks never call asking for passwords</li>
                    <li>• Verify via official hotlines only</li>
                  </>
                )}
              </ul>
            </div>

            {/* Hotlines */}
            <div className="mt-4 bg-red-50 border border-red-200 rounded-xl p-4">
              <h3 className="font-semibold text-red-800 text-sm mb-2">{t('report_hotlines')}</h3>
              <div className="text-xs text-red-700 space-y-1">
                <div>CCID Polis: <strong>03-2610 5000</strong></div>
                <div>BNM TELELINK: <strong>1-300-88-5465</strong></div>
                <div>{lang === 'ms' ? 'Kecemasan' : 'Emergency'}: <strong>997</strong></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Share Modal */}
      {showShare && (
        <ShareModal
          analysisData={{
            lastMessage,
            imageFile: lastImageFile,
            risk_score: riskData.score,
            risk_level: riskData.level,
            indicators: riskData.indicators,
          }}
          onClose={() => setShowShare(false)}
        />
      )}
    </div>
  )
}
