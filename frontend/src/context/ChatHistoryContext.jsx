import React, { createContext, useContext, useState } from 'react'
import { translations } from './LanguageContext'

// ─── Initial states ───────────────────────────────────────────────────────────

function makeAnalysisInitial(lang) {
  return {
    messages: [{
      id: 'welcome',
      isBot: true,
      text: translations[lang]?.analysis_welcome ?? translations.en.analysis_welcome,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }],
    sessionId: null,
    riskData: { score: 0, level: 'LOW', confidence: 0, indicators: [] },
    lastMessage: '',
    lastImageFile: null,
  }
}

const INTRO_EN = {
  id: 'intro-en',
  isBot: true,
  text:
    '⚠️ SIMULATION MODE ⚠️\n\n' +
    'Welcome to the Scam Simulator!\n\n' +
    'Each session is a realistic Malaysian message — it may be a real scam or a legitimate alert. ' +
    'The bot will stay in character; you will not be told which until the end.\n\n' +
    '🎯 Your goal: Verify before you act — spot scams, but do not panic over real notices\n\n' +
    'Press "Start Simulation" to begin.',
}

const INTRO_MS = {
  id: 'intro-ms',
  isBot: true,
  text:
    '⚠️ MOD SIMULASI ⚠️\n\n' +
    'Selamat datang ke Simulator Penipuan!\n\n' +
    'Setiap sesi ialah mesej realistik dari Malaysia — ia mungkin penipuan sebenar atau notis sah. ' +
    'Bot kekal berperanan; anda tidak akan diberitahu sehingga simulasi tamat.\n\n' +
    '🎯 Matlamat anda: Sahkan dahulu sebelum bertindak — kenal pasti penipuan tanpa panik terhadap notis sah\n\n' +
    'Tekan "Mulakan Simulasi" untuk bermula.',
}

function makeSimulatorInitial(lang) {
  return {
    messages: [lang === 'ms' ? INTRO_MS : INTRO_EN],
    sessionId: null,
    started: false,
    scamEnded: false,
    report: null,
    userSucceeded: false,
    sessionLang: null,
  }
}

// ─── Context ──────────────────────────────────────────────────────────────────

const ChatHistoryContext = createContext(null)

export function ChatHistoryProvider({ children }) {
  // Each bot's state is stored here and survives route changes.
  // Initialised lazily using the browser's current language preference.
  const initialLang = localStorage.getItem('antiscam_lang') || 'en'

  const [analysisState, setAnalysisState] = useState(() => makeAnalysisInitial(initialLang))
  const [simulatorState, setSimulatorState] = useState(() => makeSimulatorInitial(initialLang))

  // Reset helpers — called on explicit user reset or page refresh (via key prop in App)
  const resetAnalysis = (lang = 'en') => setAnalysisState(makeAnalysisInitial(lang))
  const resetSimulator = (lang = 'en') => setSimulatorState(makeSimulatorInitial(lang))

  return (
    <ChatHistoryContext.Provider value={{
      analysisState,   setAnalysisState,   resetAnalysis,
      simulatorState,  setSimulatorState,  resetSimulator,
      INTRO_EN, INTRO_MS,
    }}>
      {children}
    </ChatHistoryContext.Provider>
  )
}

export function useChatHistory() {
  return useContext(ChatHistoryContext)
}
