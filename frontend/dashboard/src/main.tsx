import React from 'react'
import ReactDOM from 'react-dom/client'
import BunkerApp from './BunkerApp'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ToastProvider, useToast } from './hooks/useToast'
import { ToastContainer } from './components/Toast'
import { initSentry, setUserContext } from './config/sentry'
import './index.css'

// Initialize Sentry error tracking (Task 3.1)
initSentry()

/**
 * Root App Wrapper
 * Provides ErrorBoundary, Toast context, and Sentry profiling
 */
const AppWrapper: React.FC = () => {
  const { toasts, dismiss } = useToast()

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('App Error:', error, errorInfo)
        // Sentry capture is automatic via Sentry.captureException
        // This callback is for additional logging
      }}
    >
      <BunkerApp />
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ErrorBoundary>
  )
}

// Task 3.2: Wrap with Sentry profiler for performance monitoring
const ProfiledApp = Sentry.withProfiler(AppWrapper)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ToastProvider>
      <ProfiledApp />
    </ToastProvider>
  </React.StrictMode>,
)
