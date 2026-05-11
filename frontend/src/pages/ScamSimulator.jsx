import React, { useState, useRef, useEffect } from 'react'
import { Send, RotateCcw, Play, AlertTriangle, Loader2, CheckCircle, XCircle } from 'lucide-react'
import ChatBubble from '../components/ChatBubble'
import { sendSimulatorMessage, resetSimulator } from '../services/api'
import { useLanguage } from '../context/LanguageContext'

const INTRO_MESSAGE_EN = {
  id: 'intro',
  isBot: true,
  text:
    '⚠️ SIMULATION MODE ⚠️\n\n' +
    'Welcome to the Scam Simulator!\n\n' +
    'In this simulation, the bot will act as a scammer to help you identify common Malaysian scam tactics.\n\n' +
    '🎯 Your goal: Identify the scam and refuse\n\n' +
    'Press "Start Simulation" to begin.',
}

const INTRO_MESSAGE_MS = {
  id: 'intro',
  isBot: true,
  text:
    '⚠️ MOD SIMULASI ⚠️\n\n' +
    'Selamat datang ke Simulator Penipuan!\n\n' +
    'Dalam simulasi ini, bot akan berperanan sebagai penipu untuk membantu anda mengenal pasti taktik penipuan biasa di Malaysia.\n\n' +
    '🎯 Matlamat anda: Kenal pasti penipuan dan tolak\n\n' +
    'Tekan "Mulakan Simulasi" untuk bermula.',
}

export default function ScamSimulator() {
  const { lang, t } = useLanguage()

  const [messages, setMessages] = useState([INTRO_MESSAGE_EN])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [started, setStarted] = useState(false)
  const [scamEnded, setScamEnded] = useState(false)
  const [report, setReport] = useState(null)
  const [userCaught, setUserCaught] = useState(false)
  const [showReport, setShowReport] = useState(false)
  const [error, setError] = useState(null)
  // Track the language the current session was started in
  const [sessionLang, setSessionLang] = useState(null)

  const messagesEndRef = useRef(null)
  // Ref to skip the effect on first mount
  const isFirstRender = useRef(true)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // React to language changes
  useEffect(() => {
    // Skip on initial mount — no language change has happened yet
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }

    if (!started) {
      // Not yet started — swap the intro message to the new language
      setMessages([lang === 'ms' ? INTRO_MESSAGE_MS : INTRO_MESSAGE_EN])
      return
    }

    // Conversation is active or ended — intro message is frozen, only append a notice pill
    if (scamEnded) {
      const notice = lang === 'ms'
        ? '🌐 Bahasa ditukar kepada Bahasa Malaysia.\n\nSesi ini telah tamat dalam bahasa sebelumnya. Tekan "Cuba Lagi" untuk memulakan simulasi baru dalam Bahasa Malaysia.'
        : '🌐 Language switched to English.\n\nThis session was conducted in the previous language. Press "Try Again" to start a new simulation in English.'
      const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      setMessages((prev) => [
        ...prev,
        { id: `lang-notice-${Date.now()}`, isBot: true, text: notice, timestamp: ts, isNotice: true },
      ])
    }
    // Active simulation: banner shown via JSX (sessionLang !== lang), no message injection
  }, [lang])

  const addMessage = (text, isBot) => {
    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    setMessages((prev) => [...prev, { id: Date.now() + Math.random(), text, isBot, timestamp: ts }])
  }

  const handleStart = async () => {
    setError(null)
    setLoading(true)
    try {
      // Reset to get a new session, then send first message to trigger scenario
      const resetData = await resetSimulator(sessionId)
      const newSessionId = resetData.session_id
      setSessionId(newSessionId)

      // Send empty trigger to get the opening scam message
      const data = await sendSimulatorMessage('start', newSessionId, lang)
      setSessionId(data.session_id)
      setStarted(true)
      setSessionLang(lang)
      addMessage(data.reply, true)
    } catch (err) {
      setError('Cannot connect to backend. Please ensure the API server is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || loading || !started || scamEnded) return

    setError(null)
    addMessage(trimmed, false)
    setInput('')
    setLoading(true)

    try {
      const data = await sendSimulatorMessage(trimmed, sessionId, lang)
      setSessionId(data.session_id)
      addMessage(data.reply, true)

      if (data.scam_ended) {
        setScamEnded(true)
        setUserCaught(data.user_caught_scam)
        if (data.report) {
          setReport(data.report)
          setTimeout(() => setShowReport(true), 800)
        }
      }
    } catch (err) {
      setError('Connection error. Please ensure the API server is running.')
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

  const handleReset = async () => {
    setLoading(true)
    try {
      const data = await resetSimulator(sessionId)
      setSessionId(data.session_id)
    } catch (_) {}
    setMessages([lang === 'ms' ? INTRO_MESSAGE_MS : INTRO_MESSAGE_EN])
    setStarted(false)
    setScamEnded(false)
    setReport(null)
    setShowReport(false)
    setUserCaught(false)
    setInput('')
    setError(null)
    setSessionLang(null)
    setLoading(false)
  }

  return (
    <div className="h-[calc(100vh-5rem)] flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-red-600 p-2 rounded-lg">
            <Play className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900">{t('sim_title')}</h1>
            <p className="text-xs text-gray-500">{t('sim_subtitle')}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="bg-yellow-100 text-yellow-800 border border-yellow-300 text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            {t('sim_mode')}
          </span>
          <button
            onClick={handleReset}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
        </div>
      </div>

      {/* Language mismatch banner — shown when user switches language mid-simulation */}
      {started && !scamEnded && sessionLang && sessionLang !== lang && (
        <div className="mx-4 mt-2 bg-blue-50 border border-blue-200 text-blue-800 text-xs px-3 py-2 rounded-lg flex items-center justify-between gap-2">
          <span>
            {lang === 'ms'
              ? '🌐 Bahasa ditukar. Sesi semasa akan terus dalam bahasa asal. Tekan Reset untuk sesi baru dalam Bahasa Malaysia.'
              : '🌐 Language switched. Current session continues in its original language. Press Reset for a new session in English.'}
          </span>
          <button
            onClick={handleReset}
            className="flex-shrink-0 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors"
          >
            {t('sim_try_again')}
          </button>
        </div>
      )}

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 scrollbar-thin scrollbar-thumb-gray">
        {messages.map((msg) =>
          msg.isNotice ? (
            <div key={msg.id} className="flex justify-center">
              <div className="bg-blue-50 border border-blue-200 text-blue-800 text-xs px-4 py-2.5 rounded-xl max-w-sm text-center leading-relaxed whitespace-pre-wrap shadow-sm">
                {msg.text}
              </div>
            </div>
          ) : (
            <ChatBubble
              key={msg.id}
              message={msg.text}
              isBot={msg.isBot}
              timestamp={msg.timestamp}
            />
          )
        )}
        {loading && (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="mx-4 mb-2 bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Input / Start */}
      <div className="bg-white border-t border-gray-200 p-3">
        {!started ? (
          <button
            onClick={handleStart}
            disabled={loading}
            className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-300 text-white font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <><Loader2 className="w-5 h-5 animate-spin" /> {t('sim_loading')}</>
            ) : (
              <><Play className="w-5 h-5" /> {t('sim_start')}</>
            )}
          </button>
        ) : scamEnded ? (
          <div className="flex gap-2">
            <div className={`flex-1 text-center py-3 rounded-xl font-bold text-sm ${userCaught ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              {userCaught ? t('sim_ended_success') : t('sim_ended_fail')}
            </div>
            <button
              onClick={() => setShowReport(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-4 py-3 rounded-xl text-sm transition-colors"
            >
              {t('sim_view_report')}
            </button>
            <button
              onClick={handleReset}
              className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold px-4 py-3 rounded-xl text-sm transition-colors flex items-center gap-1"
            >
              <RotateCcw className="w-4 h-4" /> {t('sim_try_again')}
            </button>
          </div>
        ) : (
          <div className="flex items-end gap-2 bg-gray-100 rounded-xl px-3 py-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('sim_placeholder')}
              className="flex-1 bg-transparent resize-none outline-none text-sm text-gray-800 placeholder-gray-400 max-h-32 min-h-[2rem]"
              rows={1}
              onInput={(e) => {
                e.target.style.height = 'auto'
                e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px'
              }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-red-600 hover:bg-red-700 disabled:bg-gray-300 text-white p-2 rounded-lg transition-colors flex-shrink-0"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
        )}
        {started && !scamEnded && (
          <p className="text-xs text-gray-400 mt-1 text-center">{t('sim_tip')}</p>
        )}
      </div>

      {/* Report Modal */}
      {showReport && report && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            {/* Modal header */}
            <div className={`p-5 rounded-t-2xl ${userCaught ? 'bg-green-600' : 'bg-red-600'} text-white`}>
              <div className="flex items-center gap-3 mb-2">
                {userCaught ? (
                  <CheckCircle className="w-8 h-8" />
                ) : (
                  <XCircle className="w-8 h-8" />
                )}
                <div>
                  <h2 className="text-xl font-extrabold">{t('sim_report_title')}</h2>
                  <p className="text-sm opacity-90">{t('sim_report_subtitle')}</p>
                </div>
              </div>
              <div className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${userCaught ? 'bg-green-800' : 'bg-red-800'}`}>
                {t('sim_report_outcome_label')} {userCaught ? t('sim_report_outcome_success') : t('sim_report_outcome_fail')}
              </div>
            </div>

            <div className="p-5 space-y-5">
              {/* Scam type */}
              <div>
                <h3 className="font-bold text-gray-900 text-sm mb-1">{t('sim_report_pattern')}</h3>
                <div className="bg-orange-50 border border-orange-200 text-orange-800 px-3 py-2 rounded-lg text-sm font-medium">
                  {report.scam_type}
                </div>
              </div>

              {/* Red flags */}
              <div>
                <h3 className="font-bold text-gray-900 text-sm mb-2">{t('sim_report_red_flags')}</h3>
                <ul className="space-y-2">
                  {report.red_flags.map((flag, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700 bg-red-50 border border-red-100 px-3 py-2 rounded-lg">
                      <span className="text-red-500 flex-shrink-0 mt-0.5">⚠️</span>
                      {flag}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Summary */}
              <div>
                <h3 className="font-bold text-gray-900 text-sm mb-1">{t('sim_report_summary')}</h3>
                <p className="text-sm text-gray-600 bg-gray-50 border border-gray-200 px-3 py-2 rounded-lg leading-relaxed">
                  {report.summary}
                </p>
              </div>

              {/* Advice */}
              <div>
                <h3 className="font-bold text-gray-900 text-sm mb-1">
                  {userCaught ? t('sim_report_did_right') : t('sim_report_next_time')}
                </h3>
                <p className="text-sm text-gray-600 bg-blue-50 border border-blue-200 px-3 py-2 rounded-lg leading-relaxed whitespace-pre-line">
                  {report.advice}
                </p>
              </div>

              {/* Emergency notice */}
              <div className="bg-yellow-50 border border-yellow-300 rounded-xl p-4">
                <p className="text-sm font-bold text-yellow-800 mb-1">{t('sim_report_notice_title')}</p>
                <p className="text-xs text-yellow-700">{t('sim_report_notice_body')}</p>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={handleReset}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  {t('sim_try_again')}
                </button>
                <button
                  onClick={() => setShowReport(false)}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold py-3 rounded-xl transition-colors"
                >
                  {t('sim_close')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
