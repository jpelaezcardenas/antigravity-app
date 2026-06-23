/**
 * useToast Hook
 * Manages toast notifications globally
 * Includes deduplication (no duplicates within 2 seconds)
 * Auto-generates toast IDs
 */

import { createContext, useContext, useState, useCallback, useRef } from 'react'
import { ToastMessage, ToastType } from '../components/Toast'

interface ToastContextType {
  toasts: ToastMessage[]
  show: (config: ToastConfig) => string
  dismiss: (id: string) => void
  success: (title: string, message?: string) => string
  error: (title: string, message?: string) => string
  info: (title: string, message?: string) => string
  warning: (title: string, message?: string) => string
}

interface ToastConfig {
  type: ToastType
  title: string
  message?: string
  action?: {
    label: string
    onClick: () => void
  }
  duration?: number
}

// Create context
export const ToastContext = createContext<ToastContextType | undefined>(undefined)

/**
 * Provider component for useToast
 * Wrap your app with <ToastProvider> to enable useToast()
 */
export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([])
  const lastMessagesRef = useRef<Map<string, number>>(new Map())
  const idCounterRef = useRef(0)

  // Deduplication: don't show same message within 2 seconds
  const isDuplicate = useCallback((title: string, message?: string): boolean => {
    const key = `${title}:${message}`
    const lastTime = lastMessagesRef.current.get(key)

    if (!lastTime) return false
    if (Date.now() - lastTime < 2000) return true

    return false
  }, [])

  // Show a toast
  const show = useCallback(
    (config: ToastConfig): string => {
      // Check for duplicates
      if (isDuplicate(config.title, config.message)) {
        console.warn('[Toast] Duplicate message skipped (dedup window 2s)')
        return '' // Return empty ID to indicate duplicate
      }

      // Record this message
      const key = `${config.title}:${config.message}`
      lastMessagesRef.current.set(key, Date.now())

      // Generate unique ID
      const id = `toast-${++idCounterRef.current}`

      // Create toast
      const toast: ToastMessage = {
        id,
        type: config.type,
        title: config.title,
        message: config.message,
        action: config.action,
        duration: config.duration ?? 5000,
      }

      setToasts((prev) => [...prev, toast])
      return id
    },
    [isDuplicate]
  )

  // Dismiss a toast
  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  // Convenience methods
  const success = useCallback(
    (title: string, message?: string) =>
      show({
        type: 'success',
        title,
        message,
      }),
    [show]
  )

  const error = useCallback(
    (title: string, message?: string) =>
      show({
        type: 'error',
        title,
        message,
      }),
    [show]
  )

  const info = useCallback(
    (title: string, message?: string) =>
      show({
        type: 'info',
        title,
        message,
      }),
    [show]
  )

  const warning = useCallback(
    (title: string, message?: string) =>
      show({
        type: 'warning',
        title,
        message,
      }),
    [show]
  )

  const value: ToastContextType = {
    toasts,
    show,
    dismiss,
    success,
    error,
    info,
    warning,
  }

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>
}

/**
 * Hook to use toast notifications
 * Must be used within a <ToastProvider>
 */
export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext)

  if (!context) {
    throw new Error('useToast must be used within <ToastProvider>')
  }

  return context
}
