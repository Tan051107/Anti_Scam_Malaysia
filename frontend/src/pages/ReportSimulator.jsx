import React, { useState } from 'react'
import { FileText, Download, AlertCircle, CheckCircle } from 'lucide-react'

const SCAM_TYPES = [
  'Macau Scam / Penipuan Macau',
  'Love Scam / Penipuan Cinta',
  'Investment Scam (Crypto/Forex) / Penipuan Pelaburan',
  'Parcel Delivery Scam / Penipuan Bungkusan',
  'LHDN Tax Scam / Penipuan LHDN',
  'Bank Impersonation / Peniruan Bank',
  'Online Shopping Scam / Penipuan Beli-belah Dalam Talian',
  'Job Scam / Penipuan Kerja',
  'Phishing / Pancingan Data',
  'Other / Lain-lain',
]

const CONTACT_METHODS = [
  'WhatsApp',
  'Telegram',
  'Phone Call / Panggilan Telefon',
  'SMS',
  'Email',
  'Facebook / Instagram',
  'Dating App',
  'Other / Lain-lain',
]

const initialForm = {
  incidentDate: '',
  scamType: '',
  description: '',
  amountLost: '',
  currency: 'MYR',
  contactMethod: '',
  scammerContact: '',
  bankAccount: '',
  reportedToPolis: false,
  reportedToBNM: false,
  victimName: '',
  victimIC: '',
  victimPhone: '',
}

function generateReportId() {
  const date = new Date()
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const rand = Math.floor(Math.random() * 90000) + 10000
  return `ASM-${y}${m}${d}-${rand}`
}

export default function ReportSimulator() {
  const [form, setForm] = useState(initialForm)
  const [generated, setGenerated] = useState(false)
  const [reportData, setReportData] = useState(null)
  const [errors, setErrors] = useState({})
  const [exporting, setExporting] = useState(false)

  const validate = () => {
    const e = {}
    if (!form.incidentDate) e.incidentDate = 'Required / Diperlukan'
    if (!form.scamType) e.scamType = 'Required / Diperlukan'
    if (!form.description || form.description.length < 20)
      e.description = 'Please provide at least 20 characters / Sila berikan sekurang-kurangnya 20 aksara'
    if (!form.contactMethod) e.contactMethod = 'Required / Diperlukan'
    return e
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }))
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: undefined }))
  }

  const handleGenerate = () => {
    const e = validate()
    if (Object.keys(e).length > 0) {
      setErrors(e)
      return
    }
    const report = {
      ...form,
      reportId: generateReportId(),
      generatedAt: new Date().toLocaleString('en-MY', { timeZone: 'Asia/Kuala_Lumpur' }),
      status: 'DRAFT — For Reference Only',
    }
    setReportData(report)
    setGenerated(true)
  }

  const handleExportPdf = async () => {
    if (!reportData) return
    setExporting(true)
    try {
      const response = await fetch('/api/simulator/report/export-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reportData),
      })
      if (!response.ok) throw new Error('Export failed')
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `scam-report-${reportData.reportId}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Failed to export PDF. Please try again.')
    } finally {
      setExporting(false)
    }
  }

  const handleReset = () => {
    setForm(initialForm)
    setGenerated(false)
    setReportData(null)
    setErrors({})
  }

  const inputClass = (field) =>
    `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
      errors[field] ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-white'
    }`

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-green-600 p-2 rounded-lg">
          <FileText className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Report Generator</h1>
          <p className="text-sm text-gray-500">Penjana Laporan Insiden Penipuan</p>
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-300 rounded-xl p-4 mb-6 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-yellow-800">
          <strong>Note / Nota:</strong> This tool generates a reference report for your records.
          For official police reports, please visit your nearest police station or use{' '}
          <strong>e-Aduan PDRM</strong>. For bank-related scams, contact your bank immediately.
        </p>
      </div>

      {/* Form */}
      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-6 mb-6">
        <h2 className="font-bold text-gray-900 mb-5 text-lg">Incident Details / Butiran Insiden</h2>

        <div className="grid md:grid-cols-2 gap-5">
          {/* Incident Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Incident Date / Tarikh Insiden <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              name="incidentDate"
              value={form.incidentDate}
              onChange={handleChange}
              className={inputClass('incidentDate')}
              max={new Date().toISOString().split('T')[0]}
            />
            {errors.incidentDate && <p className="text-xs text-red-500 mt-1">{errors.incidentDate}</p>}
          </div>

          {/* Scam Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Scam Type / Jenis Penipuan <span className="text-red-500">*</span>
            </label>
            <select
              name="scamType"
              value={form.scamType}
              onChange={handleChange}
              className={inputClass('scamType')}
            >
              <option value="">Select / Pilih...</option>
              {SCAM_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            {errors.scamType && <p className="text-xs text-red-500 mt-1">{errors.scamType}</p>}
          </div>

          {/* Contact Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Method Used / Kaedah Hubungan <span className="text-red-500">*</span>
            </label>
            <select
              name="contactMethod"
              value={form.contactMethod}
              onChange={handleChange}
              className={inputClass('contactMethod')}
            >
              <option value="">Select / Pilih...</option>
              {CONTACT_METHODS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            {errors.contactMethod && <p className="text-xs text-red-500 mt-1">{errors.contactMethod}</p>}
          </div>

          {/* Scammer Contact */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Scammer's Contact / Nombor/Akaun Penipu
            </label>
            <input
              type="text"
              name="scammerContact"
              value={form.scammerContact}
              onChange={handleChange}
              placeholder="+60123456789 or username"
              className={inputClass('scammerContact')}
            />
          </div>

          {/* Amount Lost */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount Lost / Jumlah Kerugian (if any / jika ada)
            </label>
            <div className="flex gap-2">
              <select
                name="currency"
                value={form.currency}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option>MYR</option>
                <option>USD</option>
                <option>SGD</option>
              </select>
              <input
                type="number"
                name="amountLost"
                value={form.amountLost}
                onChange={handleChange}
                placeholder="0.00"
                min="0"
                step="0.01"
                className={`flex-1 ${inputClass('amountLost')}`}
              />
            </div>
          </div>

          {/* Bank Account (scammer's) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Scammer's Bank Account / Akaun Bank Penipu
            </label>
            <input
              type="text"
              name="bankAccount"
              value={form.bankAccount}
              onChange={handleChange}
              placeholder="Bank name + account number"
              className={inputClass('bankAccount')}
            />
          </div>
        </div>

        {/* Description */}
        <div className="mt-5">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description of Incident / Penerangan Insiden <span className="text-red-500">*</span>
          </label>
          <textarea
            name="description"
            value={form.description}
            onChange={handleChange}
            rows={5}
            placeholder="Describe what happened in detail / Huraikan apa yang berlaku secara terperinci..."
            className={`${inputClass('description')} resize-none`}
          />
          <div className="flex justify-between mt-1">
            {errors.description ? (
              <p className="text-xs text-red-500">{errors.description}</p>
            ) : (
              <span />
            )}
            <span className="text-xs text-gray-400">{form.description.length} chars</span>
          </div>
        </div>

        {/* Victim Info (optional) */}
        <div className="mt-5 border-t border-gray-100 pt-5">
          <h3 className="font-semibold text-gray-700 text-sm mb-3">
            Your Information (Optional) / Maklumat Anda (Pilihan)
          </h3>
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Full Name / Nama Penuh</label>
              <input
                type="text"
                name="victimName"
                value={form.victimName}
                onChange={handleChange}
                placeholder="Your name"
                className={inputClass('victimName')}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">IC Number / Nombor IC</label>
              <input
                type="text"
                name="victimIC"
                value={form.victimIC}
                onChange={handleChange}
                placeholder="XXXXXX-XX-XXXX"
                className={inputClass('victimIC')}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Phone / Telefon</label>
              <input
                type="text"
                name="victimPhone"
                value={form.victimPhone}
                onChange={handleChange}
                placeholder="+601X-XXXXXXX"
                className={inputClass('victimPhone')}
              />
            </div>
          </div>
        </div>

        {/* Reported checkboxes */}
        <div className="mt-5 flex flex-wrap gap-6">
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              name="reportedToPolis"
              checked={form.reportedToPolis}
              onChange={handleChange}
              className="w-4 h-4 accent-blue-600"
            />
            Already reported to PDRM / Sudah lapor ke PDRM
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              name="reportedToBNM"
              checked={form.reportedToBNM}
              onChange={handleChange}
              className="w-4 h-4 accent-blue-600"
            />
            Already reported to BNM / Sudah lapor ke BNM
          </label>
        </div>

        {/* Generate button */}
        <div className="mt-6 flex gap-3">
          <button
            onClick={handleGenerate}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            <FileText className="w-5 h-5" />
            Jana Laporan / Generate Report
          </button>
          <button
            onClick={handleReset}
            className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold px-6 py-3 rounded-xl transition-colors"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Generated Report */}
      {generated && reportData && (
        <div className="bg-white border-2 border-gray-300 rounded-2xl shadow-lg overflow-hidden">
          {/* Report header */}
          <div className="bg-[#003893] text-white p-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                  <span className="text-green-300 text-sm font-medium">Report Generated</span>
                </div>
                <h2 className="text-2xl font-extrabold">SCAM INCIDENT REPORT</h2>
                <p className="text-blue-200 text-sm">Laporan Insiden Penipuan</p>
              </div>
              <div className="text-right">
                <div className="text-xs text-blue-300 mb-1">Report ID</div>
                <div className="font-mono font-bold text-[#FFCC00] text-lg">{reportData.reportId}</div>
                <div className="text-xs text-blue-300 mt-1">{reportData.generatedAt}</div>
              </div>
            </div>
          </div>

          <div className="p-6 space-y-5">
            {/* Status */}
            <div className="bg-yellow-50 border border-yellow-300 rounded-lg px-4 py-2 text-sm text-yellow-800 font-medium text-center">
              ⚠️ {reportData.status}
            </div>

            {/* Details grid */}
            <div className="grid md:grid-cols-2 gap-4">
              {[
                { label: 'Incident Date / Tarikh', value: reportData.incidentDate },
                { label: 'Scam Type / Jenis Penipuan', value: reportData.scamType },
                { label: 'Contact Method / Kaedah Hubungan', value: reportData.contactMethod },
                { label: "Scammer's Contact / Hubungan Penipu", value: reportData.scammerContact || 'Not provided' },
                {
                  label: 'Amount Lost / Kerugian',
                  value: reportData.amountLost
                    ? `${reportData.currency} ${parseFloat(reportData.amountLost).toLocaleString('en-MY', { minimumFractionDigits: 2 })}`
                    : 'Not specified / Tidak dinyatakan',
                },
                { label: "Scammer's Bank / Bank Penipu", value: reportData.bankAccount || 'Not provided' },
              ].map((item) => (
                <div key={item.label} className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-1">{item.label}</div>
                  <div className="text-sm font-semibold text-gray-900">{item.value}</div>
                </div>
              ))}
            </div>

            {/* Description */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-xs text-gray-500 mb-2">Description / Penerangan</div>
              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{reportData.description}</p>
            </div>

            {/* Victim info */}
            {(reportData.victimName || reportData.victimIC || reportData.victimPhone) && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="text-xs text-blue-600 font-semibold mb-2">Victim Information / Maklumat Mangsa</div>
                <div className="grid grid-cols-3 gap-3 text-sm">
                  {reportData.victimName && (
                    <div><span className="text-gray-500 text-xs">Name:</span><br />{reportData.victimName}</div>
                  )}
                  {reportData.victimIC && (
                    <div><span className="text-gray-500 text-xs">IC:</span><br />{reportData.victimIC}</div>
                  )}
                  {reportData.victimPhone && (
                    <div><span className="text-gray-500 text-xs">Phone:</span><br />{reportData.victimPhone}</div>
                  )}
                </div>
              </div>
            )}

            {/* Reported status */}
            <div className="flex gap-4">
              <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg ${reportData.reportedToPolis ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'}`}>
                {reportData.reportedToPolis ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                Reported to PDRM
              </div>
              <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg ${reportData.reportedToBNM ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'}`}>
                {reportData.reportedToBNM ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                Reported to BNM
              </div>
            </div>

            {/* Advice */}
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <h3 className="font-bold text-red-800 text-sm mb-2">🚨 Next Steps / Langkah Seterusnya</h3>
              <ul className="text-xs text-red-700 space-y-1">
                <li>• File a police report at your nearest police station / Buat laporan polis di balai polis berhampiran</li>
                <li>• Contact your bank immediately if money was transferred / Hubungi bank anda segera jika wang telah dipindahkan</li>
                <li>• Report to CCID: <strong>03-2610 5000</strong></li>
                <li>• Report to BNM TELELINK: <strong>1-300-88-5465</strong></li>
                <li>• Check mule accounts at: <strong>www.semakmule.rmp.gov.my</strong></li>
                <li>• Report to MCMC: <strong>aduan.mcmc.gov.my</strong></li>
              </ul>
            </div>

            {/* Action buttons */}
            <div className="flex gap-3 print:hidden">
              <button
                onClick={handleExportPdf}
                disabled={exporting}
                className="flex-1 bg-[#003893] hover:bg-blue-800 disabled:opacity-60 text-white font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                <Download className="w-5 h-5" />
                {exporting ? 'Exporting...' : 'Export PDF / Eksport PDF'}
              </button>
              <button
                onClick={handleReset}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold py-3 rounded-xl transition-colors"
              >
                New Report / Laporan Baru
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
