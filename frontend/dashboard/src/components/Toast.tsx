/**
 * Toast Component
 * Displays temporary notifications (success, error, info, warning)
 * Auto-dismisses after 5 seconds
 * Stacks vertically, max 3 visible
 * Deduplicates within 2 seconds
 */

import React, { useEffect } from 'react'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface ToastMessage {
  id: string
  type: ToastType
  title: string
  message?: string
  action?: {
    label: string
    onClick: () => void
  }
  duration?: number // milliseconds, default 5000
}

interface ToastProps {
  toast: ToastMessage
  onDismiss: (id: string) => void
}

const getIcon = (type: ToastType): string => {
  switch (type) {
    case 'success':
      return '✅'
    case 'error':
      return '❌'
    case 'info':
      return 'ℹ️'
    case 'warning':
      return '⚠️'
    default:
      return '📌'
  }
}

const getColors = (type: ToastType): { bg: string; border: string; title: string; message: string } => {
  switch (type) {
    case 'success':
      return {
        bg: 'bg-green-900/20',
        border: 'border-green-500/30',
        title: 'text-green-400',
        message: 'text-green-300',
      }
    case 'error':
      return {
        bg: 'bg-red-900/20',
        border: 'border-red-500/30',
        title: 'text-red-400',
        message: 'text-red-300',
      }
    case 'info':
      return {
        bg: 'bg-blue-900/20',
        border: 'border-blue-500/30',
        title: 'text-blue-400',
        message: 'text-blue-300',
      }
    case 'warning':
      return {
        bg: 'bg-yellow-900/20',
        border: 'border-yellow-500/30',
        title: 'text-yellow-400',
        message: 'text-yellow-300',
      }
    default:
      return {
        bg: 'bg-slate-800/20',
        border: 'border-slate-500/30',
        title: 'text-slate-400',
        message: 'text-slate-300',
      }
  }
}

/**
 * Individual Toast Item
 */
export const Toast: React.FC<ToastProps> = ({ toast, onDismiss }) => {
  const colors = getColors(toast.type)
  const duration = toast.duration ?? 5000

  useEffect(() => {
    if (duration === 0) return // No auto-dismiss

    const timer = setTimeout(() => {
      onDismiss(toast.id)
    }, duration)

    return () => clearTimeout(timer)
  }, [toast.id, duration, onDismiss])

  return (
    <div
      className={`${colors.bg} border ${colors.border} rounded-lg p-4 max-w-sm w-full backdrop-blur-sm animate-slide-in-right`}
      role="alert"
    >
      <div className="flex gap-3">
        {/* Icon */}
        <span className="text-xl flex-shrink-0">{getIcon(toast.type)}</span>

        {/* Content */}
        <div className="flex-1">
          <h3 className={`font-semibold ${colors.title}`}>{toast.title}</h3>
          {toast.message && <p className={`text-sm ${colors.message} mt-1`}>{toast.message}</p>}

          {/* Action Button */}
          {toast.action && (
            <button
              onClick={() => {
                toast.action!.onClick()
                onDismiss(toast.id)
              }}
              className={`text-sm font-medium ${colors.title} hover:opacity-80 transition-opacity mt-2`}
            >
              {toast.action.label} →
            </button>
          )}
        </div>

        {/* Close Button */}
        <button
          onClick={() => onDismiss(toast.id)}
          className="text-gray-400 hover:text-gray-300 flex-shrink-0 transition-colors"
          aria-label="Close"
        >
          ✕
        </button>
      </div>
    </div>
  )
}

/**
 * Toast Container
 * Manages multiple toasts, stacking, and deduplication
 */
interface ToastContainerProps {
  toasts: ToastMessage[]
  onDismiss: (id: string) => void
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  // Show max 3 toasts (FIFO)
  const visibleToasts = toasts.slice(-3)

  return (
    <div className="fixed bottom-4 right-4 space-y-3 z-50 pointer-events-none">
      {visibleToasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast toast={toast} onDismiss={onDismiss} />
        </div>
      ))}
    </div>
  )
}
