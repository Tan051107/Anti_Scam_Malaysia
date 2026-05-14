import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Shield, MessageSquare, Play, FileText, AlertTriangle, TrendingUp, Users, Phone } from 'lucide-react'
import { getRecentPosts } from '../services/api'
import { useLanguage } from '../context/LanguageContext'

const RISK_COLORS = {
  LOW:      'bg-green-100 text-green-800',
  MEDIUM:   'bg-yellow-100 text-yellow-800',
  HIGH:     'bg-orange-100 text-orange-800',
  CRITICAL: 'bg-red-100 text-red-800',
}

export default function Home() {
  const { t, lang } = useLanguage()
  const [recentPosts, setRecentPosts] = useState([])

  useEffect(() => {
    getRecentPosts(3).then((data) => setRecentPosts(data.posts)).catch(() => {})
  }, [])

  const features = [
    {
      icon: <MessageSquare className="w-8 h-8" />,
      title: t('nav_analysis'),
      description: lang === 'ms'
        ? 'Tampal mesej, URL, nombor telefon atau e-mel yang mencurigakan. AI kami menganalisis petanda penipuan dengan segera.'
        : 'Paste suspicious messages, URLs, phone numbers, or emails. Our AI analyzes them for scam indicators instantly.',
      link: '/analysis',
      color: 'bg-brand-primary',
      badge: 'AI Powered',
    },
    {
      icon: <Play className="w-8 h-8" />,
      title: t('nav_simulator'),
      description: lang === 'ms'
        ? 'Latih diri mengenal pasti penipuan dalam persekitaran selamat. Bot kami mensimulasikan senario penipuan Malaysia yang sebenar.'
        : 'Practice identifying scams in a safe environment. Our bot simulates real Malaysian scam scenarios.',
      link: '/simulator',
      color: 'bg-red-600',
      badge: 'Interactive',
    },
    {
      icon: <FileText className="w-8 h-8" />,
      title: t('nav_report'),
      description: lang === 'ms'
        ? 'Jana laporan insiden penipuan berstruktur untuk diserahkan kepada PDRM, Bank Negara atau MCMC.'
        : 'Generate a structured scam incident report to submit to PDRM, Bank Negara, or MCMC.',
      link: '/report',
      color: 'bg-green-600',
      badge: 'Free',
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: t('nav_community'),
      description: lang === 'ms'
        ? 'Lihat kes penipuan terkini yang dikongsi oleh rakyat Malaysia. Bersama kita lindungi satu sama lain.'
        : 'View recent scam cases shared by Malaysians. Together we protect each other.',
      link: '/community',
      color: 'bg-purple-600',
      badge: 'Community',
    },
  ]

  const stats = [
    { value: '56,000+', label: lang === 'ms' ? 'Kes penipuan dilaporkan 2023' : 'Scam cases reported in 2023', icon: <AlertTriangle className="w-5 h-5" /> },
    { value: 'RM1.2B',  label: lang === 'ms' ? 'Kerugian akibat penipuan 2023' : 'Lost to scams in 2023',       icon: <TrendingUp className="w-5 h-5" /> },
    { value: '1 in 3',  label: lang === 'ms' ? 'Rakyat Malaysia disasarkan penipu' : 'Malaysians targeted by scams', icon: <Users className="w-5 h-5" /> },
    { value: '997',     label: lang === 'ms' ? 'Talian kecemasan' : 'Emergency hotline',                        icon: <Phone className="w-5 h-5" /> },
  ]

  const scamTypes = [
    { name: 'Macau Scam',      nameMs: 'Penipuan Macau',     emoji: '📞', desc: lang === 'ms' ? 'Menyamar sebagai polis/pegawai kerajaan' : 'Impersonating police/government officials' },
    { name: 'Love Scam',       nameMs: 'Penipuan Cinta',     emoji: '💔', desc: lang === 'ms' ? 'Hubungan romantik palsu untuk wang' : 'Fake romantic relationships for money' },
    { name: 'Investment Scam', nameMs: 'Penipuan Pelaburan', emoji: '📈', desc: lang === 'ms' ? 'Pulangan dijamin palsu crypto/forex' : 'Fake crypto/forex guaranteed returns' },
    { name: 'Parcel Scam',     nameMs: 'Penipuan Bungkusan', emoji: '📦', desc: lang === 'ms' ? 'Bayaran penghantaran Shopee/Lazada palsu' : 'Fake Shopee/Lazada delivery fees' },
    { name: 'LHDN Scam',       nameMs: 'Penipuan LHDN',      emoji: '🏛️', desc: lang === 'ms' ? 'Tuntutan pihak berkuasa cukai palsu' : 'Fake tax authority demands' },
    { name: 'Job Scam',        nameMs: 'Penipuan Kerja',     emoji: '💼', desc: lang === 'ms' ? 'Tawaran kerja palsu memerlukan bayaran' : 'Fake job offers requiring upfront fees' },
  ]

  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-primary via-brand-primary-mid to-brand-primary text-white py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex justify-center mb-6">
            <div className="bg-brand-secondary p-4 rounded-2xl shadow-2xl">
              <Shield className="w-14 h-14 text-white" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold mb-3 leading-tight">
            {t('hero_title')}
          </h1>
          <h2 className="text-2xl md:text-3xl font-bold text-brand-accent mb-6">
            {t('hero_subtitle')}
          </h2>
          <p className="text-blue-200 text-lg max-w-2xl mx-auto mb-8">
            {t('hero_desc')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/analysis" className="bg-brand-secondary hover:bg-brand-secondary-dark text-white font-bold px-8 py-3 rounded-xl transition-colors shadow-lg">
              {t('hero_analyze')}
            </Link>
            <Link to="/simulator" className="bg-white hover:bg-gray-100 text-brand-primary font-bold px-8 py-3 rounded-xl transition-colors shadow-lg">
              {t('hero_simulator')}
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-brand-secondary py-8 px-4">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div key={stat.value} className="text-center text-white">
              <div className="flex justify-center mb-1 text-red-200">{stat.icon}</div>
              <div className="text-2xl font-extrabold">{stat.value}</div>
              <div className="text-xs text-red-200 mt-0.5">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">
            {lang === 'ms' ? 'Alat Kami' : 'Our Tools'}
          </h2>
          <p className="text-center text-gray-500 mb-10">
            {lang === 'ms' ? 'Alat Perlindungan Anda' : 'Your Protection Tools'}
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => (
              <Link
                key={feature.link}
                to={feature.link}
                className="group bg-white border border-gray-200 rounded-2xl p-6 shadow-sm hover:shadow-xl transition-all hover:-translate-y-1"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`${feature.color} text-white p-3 rounded-xl`}>
                    {feature.icon}
                  </div>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full font-medium">
                    {feature.badge}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-sm text-gray-600">{feature.description}</p>
                <div className={`mt-4 text-sm font-semibold ${feature.color.replace('bg-', 'text-')} group-hover:underline`}>
                  {lang === 'ms' ? 'Mulakan →' : 'Get started →'}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Recent Scam Cases */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-3xl font-bold text-gray-900">{t('recent_scam_title')}</h2>
            <Link to="/community" className="text-brand-primary hover:underline text-sm font-semibold">
              {t('recent_scam_view_all')}
            </Link>
          </div>
          <p className="text-gray-500 mb-8">{t('recent_scam_subtitle')}</p>

          {recentPosts.length === 0 ? (
            <div className="text-center py-10 bg-white rounded-2xl border border-gray-200">
              <Users className="w-10 h-10 text-gray-300 mx-auto mb-2" />
              <p className="text-gray-400 text-sm">{t('recent_scam_empty')}</p>
              <Link to="/analysis" className="mt-3 inline-block text-brand-primary text-sm font-semibold hover:underline">
                {lang === 'ms' ? 'Analisis mesej mencurigakan →' : 'Analyze a suspicious message →'}
              </Link>
            </div>
          ) : (
            <div className="grid md:grid-cols-3 gap-4">
              {recentPosts.map((post) => (
                <div key={post.id} className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-brand-primary flex items-center justify-center text-white text-xs font-bold">
                        {post.author_name[0].toUpperCase()}
                      </div>
                      <span className="text-xs text-gray-500">{post.author_name}</span>
                    </div>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${RISK_COLORS[post.risk_level] || 'bg-gray-100 text-gray-700'}`}>
                      {post.risk_level} {post.risk_score}%
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-3 break-words">{post.original_message}</p>
                  {post.note && (
                    <p className="text-xs text-gray-400 italic mt-2 line-clamp-1">"{post.note}"</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Scam Types */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">
            {lang === 'ms' ? 'Jenis Penipuan Biasa di Malaysia' : 'Common Scams in Malaysia'}
          </h2>
          <p className="text-center text-gray-500 mb-10">
            {lang === 'ms' ? 'Kenali untuk melindungi diri anda' : 'Know them to protect yourself'}
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {scamTypes.map((scam) => (
              <div key={scam.name} className="bg-white border border-gray-200 rounded-xl p-4 flex items-start gap-3 shadow-sm hover:shadow-md transition-shadow">
                <span className="text-3xl">{scam.emoji}</span>
                <div>
                  <div className="font-bold text-gray-900 text-sm">{lang === 'ms' ? scam.nameMs : scam.name}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{scam.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Emergency Banner */}
      <section className="bg-gray-900 py-10 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h3 className="text-white text-xl font-bold mb-4">
            {lang === 'ms' ? '🚨 Jika anda mangsa penipuan' : '🚨 If you are a scam victim'}
          </h3>
          <div className="grid sm:grid-cols-3 gap-4 text-sm">
            {[
              { label: lang === 'ms' ? 'Kecemasan' : 'Emergency', number: '997',           color: 'bg-red-600' },
              { label: 'CCID Polis Malaysia',                      number: '03-2610 5000',  color: 'bg-brand-secondary' },
              { label: 'BNM TELELINK',                             number: '1-300-88-5465', color: 'bg-green-700' },
            ].map((item) => (
              <div key={item.number} className={`${item.color} text-white rounded-xl py-3 px-4`}>
                <div className="text-xs opacity-80 mb-1">{item.label}</div>
                <div className="text-xl font-extrabold">{item.number}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
