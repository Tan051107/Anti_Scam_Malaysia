import React from 'react'
import { Link } from 'react-router-dom'
import { Shield, MessageSquare, Play, FileText, AlertTriangle, TrendingUp, Users, Phone } from 'lucide-react'

const features = [
  {
    icon: <MessageSquare className="w-8 h-8" />,
    title: 'Analysis Bot',
    titleMs: 'Bot Analisis',
    description: 'Paste suspicious messages, URLs, phone numbers, or emails. Our AI analyzes them for scam indicators instantly.',
    descriptionMs: 'Tampal mesej, URL, nombor telefon atau e-mel yang mencurigakan. AI kami menganalisis petanda penipuan dengan segera.',
    link: '/analysis',
    color: 'bg-blue-600',
    hoverColor: 'hover:bg-blue-700',
    badge: 'AI Powered',
  },
  {
    icon: <Play className="w-8 h-8" />,
    title: 'Scam Simulator',
    titleMs: 'Simulator Penipuan',
    description: 'Practice identifying scams in a safe environment. Our bot simulates real Malaysian scam scenarios.',
    descriptionMs: 'Latih diri mengenal pasti penipuan dalam persekitaran selamat. Bot kami mensimulasikan senario penipuan Malaysia yang sebenar.',
    link: '/simulator',
    color: 'bg-red-600',
    hoverColor: 'hover:bg-red-700',
    badge: 'Interactive',
  },
  {
    icon: <FileText className="w-8 h-8" />,
    title: 'Report Generator',
    titleMs: 'Penjana Laporan',
    description: 'Generate a structured scam incident report to submit to PDRM, Bank Negara, or MCMC.',
    descriptionMs: 'Jana laporan insiden penipuan berstruktur untuk diserahkan kepada PDRM, Bank Negara atau MCMC.',
    link: '/report',
    color: 'bg-green-600',
    hoverColor: 'hover:bg-green-700',
    badge: 'Free',
  },
]

const stats = [
  { value: '56,000+', label: 'Scam cases reported in 2023', labelMs: 'Kes penipuan dilaporkan 2023', icon: <AlertTriangle className="w-5 h-5" /> },
  { value: 'RM1.2B', label: 'Lost to scams in 2023', labelMs: 'Kerugian akibat penipuan 2023', icon: <TrendingUp className="w-5 h-5" /> },
  { value: '1 in 3', label: 'Malaysians targeted by scams', labelMs: 'Rakyat Malaysia disasarkan penipu', icon: <Users className="w-5 h-5" /> },
  { value: '997', label: 'Emergency hotline', labelMs: 'Talian kecemasan', icon: <Phone className="w-5 h-5" /> },
]

const scamTypes = [
  { name: 'Macau Scam', nameMs: 'Penipuan Macau', emoji: '📞', desc: 'Impersonating police/government officials' },
  { name: 'Love Scam', nameMs: 'Penipuan Cinta', emoji: '💔', desc: 'Fake romantic relationships for money' },
  { name: 'Investment Scam', nameMs: 'Penipuan Pelaburan', emoji: '📈', desc: 'Fake crypto/forex guaranteed returns' },
  { name: 'Parcel Scam', nameMs: 'Penipuan Bungkusan', emoji: '📦', desc: 'Fake Shopee/Lazada delivery fees' },
  { name: 'LHDN Scam', nameMs: 'Penipuan LHDN', emoji: '🏛️', desc: 'Fake tax authority demands' },
  { name: 'Job Scam', nameMs: 'Penipuan Kerja', emoji: '💼', desc: 'Fake job offers requiring upfront fees' },
]

export default function Home() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="bg-gradient-to-br from-[#003893] via-blue-800 to-[#003893] text-white py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex justify-center mb-6">
            <div className="bg-[#CC0001] p-4 rounded-2xl shadow-2xl">
              <Shield className="w-14 h-14 text-white" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold mb-3 leading-tight">
            Protect Yourself from Scams
          </h1>
          <h2 className="text-2xl md:text-3xl font-bold text-[#FFCC00] mb-6">
            Lindungi Diri Anda dari Penipuan
          </h2>
          <p className="text-blue-200 text-lg max-w-2xl mx-auto mb-8">
            AI-powered scam detection and education platform built for Malaysians.
            Analyze suspicious messages, practice identifying scams, and generate reports.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/analysis"
              className="bg-[#CC0001] hover:bg-red-700 text-white font-bold px-8 py-3 rounded-xl transition-colors shadow-lg"
            >
              🔍 Analyze a Message
            </Link>
            <Link
              to="/simulator"
              className="bg-white hover:bg-gray-100 text-[#003893] font-bold px-8 py-3 rounded-xl transition-colors shadow-lg"
            >
              🎮 Try Simulator
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-[#CC0001] py-8 px-4">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div key={stat.value} className="text-center text-white">
              <div className="flex justify-center mb-1 text-red-200">{stat.icon}</div>
              <div className="text-2xl font-extrabold">{stat.value}</div>
              <div className="text-xs text-red-200 mt-0.5">{stat.label}</div>
              <div className="text-xs text-red-300">{stat.labelMs}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">Our Tools</h2>
          <p className="text-center text-gray-500 mb-10">Alat Perlindungan Anda</p>
          <div className="grid md:grid-cols-3 gap-6">
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
                <h3 className="text-xl font-bold text-gray-900 mb-1">{feature.title}</h3>
                <p className="text-sm text-blue-600 font-medium mb-3">{feature.titleMs}</p>
                <p className="text-sm text-gray-600 mb-2">{feature.description}</p>
                <p className="text-xs text-gray-400 italic">{feature.descriptionMs}</p>
                <div className={`mt-4 text-sm font-semibold ${feature.color.replace('bg-', 'text-')} group-hover:underline`}>
                  Get started →
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Scam Types */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-2">Common Scams in Malaysia</h2>
          <p className="text-center text-gray-500 mb-10">Jenis Penipuan Biasa di Malaysia</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {scamTypes.map((scam) => (
              <div
                key={scam.name}
                className="bg-white border border-gray-200 rounded-xl p-4 flex items-start gap-3 shadow-sm hover:shadow-md transition-shadow"
              >
                <span className="text-3xl">{scam.emoji}</span>
                <div>
                  <div className="font-bold text-gray-900 text-sm">{scam.name}</div>
                  <div className="text-xs text-blue-600 mb-1">{scam.nameMs}</div>
                  <div className="text-xs text-gray-500">{scam.desc}</div>
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
            🚨 If you are a scam victim / Jika anda mangsa penipuan
          </h3>
          <div className="grid sm:grid-cols-3 gap-4 text-sm">
            {[
              { label: 'Emergency / Kecemasan', number: '997', color: 'bg-red-600' },
              { label: 'CCID Polis Malaysia', number: '03-2610 5000', color: 'bg-blue-700' },
              { label: 'BNM TELELINK', number: '1-300-88-5465', color: 'bg-green-700' },
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
