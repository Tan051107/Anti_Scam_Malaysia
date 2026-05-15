import React, { useState } from 'react'
import { FileText, Download, AlertCircle, CheckCircle } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'

const SCAM_TYPES_EN = [
  'Macau Scam',
  'Love Scam',
  'Investment Scam (Crypto/Forex)',
  'Parcel Delivery Scam',
  'LHDN Tax Scam',
  'Bank Impersonation',
  'Online Shopping Scam',
  'Job Scam',
  'Phishing',
  'Other',
]

const SCAM_TYPES_MS = [
  'Penipuan Macau',
  'Penipuan Cinta',
  'Penipuan Pelaburan (Kripto/Forex)',
  'Penipuan Penghantaran Bungkusan',
  'Penipuan Cukai LHDN',
  'Peniruan Bank',
  'Penipuan Beli-belah Dalam Talian',
  'Penipuan Kerja',
  'Pancingan Data',
  'Lain-lain',
]

const CONTACT_METHODS_EN = [
  'WhatsApp',
  'Telegram',
  'Phone Call',
  'SMS',
  'Email',
  'Facebook / Instagram',
  'Dating App',
  'Other',
]

const CONTACT_METHODS_MS = [
  'WhatsApp',
  'Telegram',
  'Panggilan Telefon',
  'SMS',
  'E-mel',
  'Facebook / Instagram',
  'Aplikasi Temu Kenalan',
  'Lain-lain',
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
  const { t, lang } = useLanguage()

  const [form, setForm] = useState(initialForm)
  const [generated, setGenerated] = useState(false)
  const [reportData, setReportData] = useState(null)
  const [errors, setErrors] = useState({})
  const [exporting, setExporting] = useState(false)

  const scamTypes = lang === 'ms' ? SCAM_TYPES_MS : SCAM_TYPES_EN
  const contactMethods = lang === 'ms' ? CONTACT_METHODS_MS : CONTACT_METHODS_EN

  const validate = () => {
    const e = {}
    if (!form.incidentDate) e.incidentDate = t('report_required')
    if (!form.scamType) e.scamType = t('report_required')
    if (!form.description || form.description.length < 20)
      e.description = t('report_desc_min')
    if (!form.contactMethod) e.contactMethod = t('report_required')
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
      status: t('report_status_draft'),
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
      alert(t('report_export_fail'))
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
    `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary ${
      errors[field] ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-white'
    }`

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-brand-secondary p-2 rounded-lg">
          <FileText className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('report_title')}</h1>
          <p className="text-sm text-gray-500">{t('report_subtitle')}</p>
        </div>
      </div>

      <div className="bg-yellow-50 border border-yellow-300 rounded-xl p-4 mb-6 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-yellow-800">{t('report_notice')}</p>
      </div>

      {/* Form */}
      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-6 mb-6">
        <h2 className="font-bold text-gray-900 mb-5 text-lg">{t('report_incident_details')}</h2>

        <div className="grid md:grid-cols-2 gap-5">
          {/* Incident Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('report_incident_date')} <span className="text-red-500">*</span>
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
              {t('report_scam_type')} <span className="text-red-500">*</span>
            </label>
            <select
              name="scamType"
              value={form.scamType}
              onChange={handleChange}
              className={inputClass('scamType')}
            >
              <option value="">{t('report_select')}</option>
              {scamTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            {errors.scamType && <p className="text-xs text-red-500 mt-1">{errors.scamType}</p>}
          </div>

          {/* Contact Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('report_contact_method')} <span className="text-red-500">*</span>
            </label>
            <select
              name="contactMethod"
              value={form.contactMethod}
              onChange={handleChange}
              className={inputClass('contactMethod')}
            >
              <option value="">{t('report_select')}</option>
              {contactMethods.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            {errors.contactMethod && <p className="text-xs text-red-500 mt-1">{errors.contactMethod}</p>}
          </div>

          {/* Scammer Contact */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('report_scammer_contact')}
            </label>
            <input
              type="text"
              name="scammerContact"
              value={form.scammerContact}
              onChange={handleChange}
              placeholder={t('report_scammer_contact_ph')}
              className={inputClass('scammerContact')}
            />
          </div>

          {/* Amount Lost */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('report_amount_lost')}
            </label>
            <div className="flex gap-2">
              <select
                name="currency"
                value={form.currency}
                onChange={handleChange}
                className="border border-gray-300 rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-primary bg-white"
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

          {/* Bank Account */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('report_bank_account')}
            </label>
            <input
              type="text"
              name="bankAccount"
              value={form.bankAccount}
              onChange={handleChange}
              placeholder={t('report_bank_account_ph')}
              className={inputClass('bankAccount')}
            />
          </div>
        </div>

        {/* Description */}
        <div className="mt-5">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {t('report_description')} <span className="text-red-500">*</span>
          </label>
          <textarea
            name="description"
            value={form.description}
            onChange={handleChange}
            rows={5}
            placeholder={t('report_description_ph')}
            className={`${inputClass('description')} resize-none`}
          />
          <div className="flex justify-between mt-1">
            {errors.description
              ? <p className="text-xs text-red-500">{errors.description}</p>
              : <span />
            }
            <span className="text-xs text-gray-400">{form.description.length} {t('report_chars')}</span>
          </div>
        </div>

        {/* Victim Info */}
        <div className="mt-5 border-t border-gray-100 pt-5">
          <h3 className="font-semibold text-gray-700 text-sm mb-3">{t('report_victim_info')}</h3>
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('report_victim_name')}</label>
              <input
                type="text"
                name="victimName"
                value={form.victimName}
                onChange={handleChange}
                placeholder={t('report_victim_name')}
                className={inputClass('victimName')}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">{t('report_victim_ic')}</label>
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
              <label className="block text-xs text-gray-600 mb-1">{t('report_victim_phone')}</label>
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
            {t('report_reported_pdrm')}
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              name="reportedToBNM"
              checked={form.reportedToBNM}
              onChange={handleChange}
              className="w-4 h-4 accent-blue-600"
            />
            {t('report_reported_bnm')}
          </label>
        </div>

        {/* Generate button */}
        <div className="mt-6 flex gap-3">
          <button
            onClick={handleGenerate}
            className="flex-1 bg-brand-secondary hover:bg-brand-secondary-dark text-white font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            <FileText className="w-5 h-5" />
            {t('report_generate_btn')}
          </button>
          <button
            onClick={handleReset}
            className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold px-6 py-3 rounded-xl transition-colors"
          >
            {t('report_reset_btn')}
          </button>
        </div>
      </div>

      {/* Generated Report */}
      {generated && reportData && (
        <div className="bg-white border-2 border-gray-300 rounded-2xl shadow-lg overflow-hidden">
          {/* Report header */}
          <div className="bg-brand-primary text-white p-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="w-6 h-6 text-brand-accent" />
                  <span className="text-brand-accent text-sm font-medium">{t('report_generated_label')}</span>
                </div>
                <h2 className="text-2xl font-extrabold">{t('report_heading')}</h2>
              </div>
              <div className="text-right">
                <div className="text-xs text-white/60 mb-1">{t('report_id_label')}</div>
                <div className="font-mono font-bold text-brand-accent text-lg">{reportData.reportId}</div>
                <div className="text-xs text-white/60 mt-1">{reportData.generatedAt}</div>
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
                { label: t('report_field_date'),    value: reportData.incidentDate },
                { label: t('report_field_type'),    value: reportData.scamType },
                { label: t('report_field_contact'), value: reportData.contactMethod },
                { label: t('report_field_scammer'), value: reportData.scammerContact || t('report_not_provided') },
                {
                  label: t('report_field_amount'),
                  value: reportData.amountLost
                    ? `${reportData.currency} ${parseFloat(reportData.amountLost).toLocaleString('en-MY', { minimumFractionDigits: 2 })}`
                    : t('report_not_specified'),
                },
                { label: t('report_field_bank'), value: reportData.bankAccount || t('report_not_provided') },
              ].map((item) => (
                <div key={item.label} className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-1">{item.label}</div>
                  <div className="text-sm font-semibold text-gray-900">{item.value}</div>
                </div>
              ))}
            </div>

            {/* Description */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-xs text-gray-500 mb-2">{t('report_field_description')}</div>
              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{reportData.description}</p>
            </div>

            {/* Victim info */}
            {(reportData.victimName || reportData.victimIC || reportData.victimPhone) && (
              <div className="bg-brand-primary/10 border border-brand-primary/20 rounded-lg p-4">
                <div className="text-xs text-brand-primary font-semibold mb-2">{t('report_victim_section')}</div>
                <div className="grid grid-cols-3 gap-3 text-sm">
                  {reportData.victimName && (
                    <div><span className="text-gray-500 text-xs">{t('report_victim_name')}:</span><br />{reportData.victimName}</div>
                  )}
                  {reportData.victimIC && (
                    <div><span className="text-gray-500 text-xs">{t('report_victim_ic')}:</span><br />{reportData.victimIC}</div>
                  )}
                  {reportData.victimPhone && (
                    <div><span className="text-gray-500 text-xs">{t('report_victim_phone')}:</span><br />{reportData.victimPhone}</div>
                  )}
                </div>
              </div>
            )}

            {/* Reported status */}
            <div className="flex gap-4">
              <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg ${reportData.reportedToPolis ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'}`}>
                {reportData.reportedToPolis ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                {t('report_reported_to_pdrm')}
              </div>
              <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg ${reportData.reportedToBNM ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'}`}>
                {reportData.reportedToBNM ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                {t('report_reported_to_bnm')}
              </div>
            </div>

            {/* Next steps */}
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <h3 className="font-bold text-red-800 text-sm mb-2">{t('report_next_steps')}</h3>
              <ul className="text-xs text-red-700 space-y-1">
                <li>{t('report_step_police')}</li>
                <li>{t('report_step_bank')}</li>
                <li>{t('report_step_ccid')} <strong>03-2610 1222</strong></li>
                <li>{t('report_step_bnm')} <strong>1-300-88-5465</strong></li>
                <li>{t('report_step_mule')} <strong>www.semakmule.rmp.gov.my</strong></li>
                <li>{t('report_step_mcmc')} <strong>aduan.mcmc.gov.my</strong></li>
              </ul>
            </div>

            {/* Action buttons */}
            <div className="flex gap-3 print:hidden">
              <button
                onClick={handleExportPdf}
                disabled={exporting}
                className="flex-1 bg-brand-primary hover:bg-brand-primary-dark disabled:opacity-60 text-white font-bold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                <Download className="w-5 h-5" />
                {exporting ? t('report_exporting') : t('report_export_btn')}
              </button>
              <button
                onClick={handleReset}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold py-3 rounded-xl transition-colors"
              >
                {t('report_new_btn')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
