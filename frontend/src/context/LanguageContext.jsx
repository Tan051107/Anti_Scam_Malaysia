import React, { createContext, useContext, useState } from 'react'

const LanguageContext = createContext()

// ─────────────────────────────────────────────
// Translation strings
// ─────────────────────────────────────────────
export const translations = {
  en: {
    // Navbar
    nav_home: 'Home',
    nav_analysis: 'Analysis Bot',
    nav_simulator: 'Scam Simulator',
    nav_report: 'Report',
    nav_community: 'Community',
    nav_login: 'Login',
    nav_signup: 'Sign Up',
    nav_logout: 'Logout',
    nav_emergency: 'Emergency: 997',

    // Home
    hero_title: 'Protect Yourself from Scams',
    hero_subtitle: 'Lindungi Diri Anda dari Penipuan',
    hero_desc: 'AI-powered scam detection and education platform built for Malaysians.',
    hero_analyze: '🔍 Analyze a Message',
    hero_simulator: '🎮 Try Simulator',
    recent_scam_title: 'Recent Scam Cases',
    recent_scam_subtitle: 'Shared by the community',
    recent_scam_view_all: 'View All in Community →',
    recent_scam_empty: 'No community posts yet. Be the first to share!',

    // Analysis Bot
    analysis_title: 'Analysis Bot',
    analysis_subtitle: 'Malaysia Scam Analysis Bot',
    analysis_welcome: 'Welcome! You can:\n• Paste suspicious messages\n• Send URLs or links\n• Enter phone numbers\n• Upload screenshots\n\nI will analyze and provide a risk assessment.',
    analysis_placeholder: 'Paste suspicious message, URL, phone number...',
    analysis_analyzing: 'Analyzing...',
    analysis_risk_title: 'Risk Assessment',
    analysis_risk_subtitle: 'Scam Risk Assessment',
    analysis_indicators: 'Scam Indicators',
    analysis_no_indicators: 'No indicators detected yet. Send a message to analyze.',
    analysis_share_btn: '📢 Share to Community',
    analysis_share_tooltip: 'Risk score above 60% — share this case to warn others',

    // Simulator
    sim_title: 'Scam Simulator Coach',
    sim_subtitle: 'Scam Simulator Coach',
    sim_mode: 'SIMULATION MODE',
    sim_start: 'Start Simulation',
    sim_loading: 'Loading...',
    sim_placeholder: 'Type your response...',
    sim_tip: '💡 Tip: If you suspect a scam, say "This is a scam" or refuse to comply',
    sim_ended_success: '✅ Simulation Ended — You Succeeded!',
    sim_ended_fail: '❌ Simulation Ended — Try Again',
    sim_view_report: 'View Report',
    sim_try_again: 'Try Again',
    sim_close: 'Close',

    // Community
    community_title: 'Community Scam Reports',
    community_subtitle: 'Real cases shared by Malaysians to protect each other',
    community_share: 'Share a Case',
    community_login_prompt: 'Login to share a scam case',
    community_empty: 'No cases shared yet. Be the first to warn others!',
    community_posted_by: 'Posted by',
    community_risk: 'Risk',
    community_indicators: 'Indicators',
    community_ago: 'ago',

    // Auth
    login_title: 'Login',
    login_email: 'Email',
    login_password: 'Password',
    login_btn: 'Login',
    login_no_account: "Don't have an account?",
    login_signup_link: 'Sign up',
    signup_title: 'Create Account',
    signup_name: 'Display Name',
    signup_email: 'Email',
    signup_password: 'Password',
    signup_btn: 'Create Account',
    signup_have_account: 'Already have an account?',
    signup_login_link: 'Login',

    // Share modal
    share_title: 'Share Scam Case to Community',
    share_desc: 'Add a note (optional)',
    share_desc_placeholder: 'Describe what happened...',
    share_anonymous: 'Post anonymously',
    share_submit: 'Share to Community',
    share_cancel: 'Cancel',
    share_success: 'Successfully shared to community!',

    // Common
    risk_low: 'LOW',
    risk_medium: 'MEDIUM',
    risk_high: 'HIGH',
    risk_critical: 'CRITICAL',
    confidence: 'Confidence',
    tips_title: '💡 Tips',
    report_hotlines: '🚨 Report Scam',
  },

  ms: {
    // Navbar
    nav_home: 'Laman Utama',
    nav_analysis: 'Bot Analisis',
    nav_simulator: 'Simulator Penipuan',
    nav_report: 'Laporan',
    nav_community: 'Komuniti',
    nav_login: 'Log Masuk',
    nav_signup: 'Daftar',
    nav_logout: 'Log Keluar',
    nav_emergency: 'Kecemasan: 997',

    // Home
    hero_title: 'Lindungi Diri Anda dari Penipuan',
    hero_subtitle: 'Protect Yourself from Scams',
    hero_desc: 'Platform pengesanan dan pendidikan penipuan berkuasa AI untuk rakyat Malaysia.',
    hero_analyze: '🔍 Analisis Mesej',
    hero_simulator: '🎮 Cuba Simulator',
    recent_scam_title: 'Kes Penipuan Terkini',
    recent_scam_subtitle: 'Dikongsi oleh komuniti',
    recent_scam_view_all: 'Lihat Semua di Komuniti →',
    recent_scam_empty: 'Tiada siaran komuniti lagi. Jadilah yang pertama berkongsi!',

    // Analysis Bot
    analysis_title: 'Bot Analisis',
    analysis_subtitle: 'Bot Analisis Penipuan Malaysia',
    analysis_welcome: 'Selamat datang! Anda boleh:\n• Tampal mesej mencurigakan\n• Hantar URL atau pautan\n• Masukkan nombor telefon\n• Muat naik tangkapan skrin\n\nSaya akan menganalisis dan memberikan penilaian risiko.',
    analysis_placeholder: 'Tampal mesej mencurigakan, URL, nombor telefon...',
    analysis_analyzing: 'Menganalisis...',
    analysis_risk_title: 'Penilaian Risiko',
    analysis_risk_subtitle: 'Penilaian Risiko Penipuan',
    analysis_indicators: 'Petanda Penipuan',
    analysis_no_indicators: 'Tiada petanda dikesan lagi. Hantar mesej untuk dianalisis.',
    analysis_share_btn: '📢 Kongsi ke Komuniti',
    analysis_share_tooltip: 'Skor risiko melebihi 60% — kongsi kes ini untuk amaran orang lain',

    // Simulator
    sim_title: 'Jurulatih Simulator Penipuan',
    sim_subtitle: 'Jurulatih Simulator Penipuan',
    sim_mode: 'MOD SIMULASI',
    sim_start: 'Mulakan Simulasi',
    sim_loading: 'Memuatkan...',
    sim_placeholder: 'Taip respons anda...',
    sim_tip: '💡 Tip: Jika anda syak penipuan, katakan "Ini penipuan" atau enggan mematuhi',
    sim_ended_success: '✅ Simulasi Tamat — Anda Berjaya!',
    sim_ended_fail: '❌ Simulasi Tamat — Cuba Lagi',
    sim_view_report: 'Lihat Laporan',
    sim_try_again: 'Cuba Lagi',
    sim_close: 'Tutup',

    // Community
    community_title: 'Laporan Penipuan Komuniti',
    community_subtitle: 'Kes sebenar dikongsi oleh rakyat Malaysia untuk melindungi satu sama lain',
    community_share: 'Kongsi Kes',
    community_login_prompt: 'Log masuk untuk berkongsi kes penipuan',
    community_empty: 'Tiada kes dikongsi lagi. Jadilah yang pertama memberi amaran!',
    community_posted_by: 'Dikongsi oleh',
    community_risk: 'Risiko',
    community_indicators: 'Petanda',
    community_ago: 'yang lalu',

    // Auth
    login_title: 'Log Masuk',
    login_email: 'E-mel',
    login_password: 'Kata Laluan',
    login_btn: 'Log Masuk',
    login_no_account: 'Tiada akaun?',
    login_signup_link: 'Daftar',
    signup_title: 'Buat Akaun',
    signup_name: 'Nama Paparan',
    signup_email: 'E-mel',
    signup_password: 'Kata Laluan',
    signup_btn: 'Buat Akaun',
    signup_have_account: 'Sudah ada akaun?',
    signup_login_link: 'Log Masuk',

    // Share modal
    share_title: 'Kongsi Kes Penipuan ke Komuniti',
    share_desc: 'Tambah nota (pilihan)',
    share_desc_placeholder: 'Huraikan apa yang berlaku...',
    share_anonymous: 'Siar secara tanpa nama',
    share_submit: 'Kongsi ke Komuniti',
    share_cancel: 'Batal',
    share_success: 'Berjaya dikongsi ke komuniti!',

    // Common
    risk_low: 'RENDAH',
    risk_medium: 'SEDERHANA',
    risk_high: 'TINGGI',
    risk_critical: 'KRITIKAL',
    confidence: 'Keyakinan',
    tips_title: '💡 Petua',
    report_hotlines: '🚨 Laporkan Penipuan',
  },
}

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState('en')
  const t = (key) => translations[lang][key] ?? translations['en'][key] ?? key
  const toggleLang = () => setLang((l) => (l === 'en' ? 'ms' : 'en'))

  return (
    <LanguageContext.Provider value={{ lang, setLang, toggleLang, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  return useContext(LanguageContext)
}
