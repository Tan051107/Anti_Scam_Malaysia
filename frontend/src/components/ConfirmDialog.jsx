import React, { useEffect } from 'react'
import { AlertTriangle, X } from 'lucide-react'

/**
 * ConfirmDialog — reusable styled confirmation modal.
 *
 * Props:
 *   isOpen      : boolean  — controls visibility
 *   title       : string   — dialog heading
 *   message     : string   — body text
 *   confirmLabel: string   — confirm button text (default "Confirm")
 *   cancelLabel : string   — cancel button text  (default "Cancel")
 *   variant     : "danger" | "warning" | "info"  (default "danger")
 *   onConfirm   : () => void
 *   onCancel    : () => void
 */
export default function ConfirmDialog({
  isOpen,
  title = 'Are you sure?',
  message = 'This action cannot be undone.',
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'danger',
  onConfirm,
  onCancel,
}) {
  // Close on Escape
  useEffect(() => {
    if (!isOpen) return
    const handler = (e) => { if (e.key === 'Escape') onCancel() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [isOpen, onCancel])

  if (!isOpen) return null

  const variantStyles = {
    danger:  { icon: 'bg-red-100 text-red-600',    btn: 'bg-red-600 hover:bg-red-700',    border: 'border-red-200' },
    warning: { icon: 'bg-yellow-100 text-yellow-600', btn: 'bg-yellow-500 hover:bg-yellow-600', border: 'border-yellow-200' },
    info:    { icon: 'bg-blue-100 text-blue-600',   btn: 'bg-blue-600 hover:bg-blue-700',  border: 'border-blue-200' },
  }
  const s = variantStyles[variant] || variantStyles.danger

  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={onCancel}
    >
      <div
        className={`bg-white rounded-2xl shadow-2xl w-full max-w-sm border ${s.border} overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-3">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-xl ${s.icon}`}>
              <AlertTriangle className="w-5 h-5" />
            </div>
            <h2 className="font-bold text-gray-900 text-base">{title}</h2>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <p className="px-5 pb-5 text-sm text-gray-600 leading-relaxed">{message}</p>

        {/* Actions */}
        <div className="flex gap-3 px-5 pb-5">
          <button
            onClick={onCancel}
            className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2.5 rounded-xl transition-colors text-sm"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`flex-1 ${s.btn} text-white font-semibold py-2.5 rounded-xl transition-colors text-sm`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
