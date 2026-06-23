import React from 'react'
import ReactDOM from 'react-dom/client'
import BunkerApp from './BunkerApp'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ToastProvider, useToast } from './hooks/useToast'
import { ToastContainer } from './components/Toast'
import './index.css'

/**
 * Root App Wrapper
 * Provides ErrorBoundary and Toast context to entire app
 */
const AppWrapper: React.FC = () => {
  const { toasts, dismiss } = useToast()

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('App Error:', error, errorInfo)
        // TODO: Stage 3 - Send to Sentry
      }}
    >
      <BunkerApp />
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ErrorBoundary>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ToastProvider>
      <AppWrapper />
    </ToastProvider>
  </React.StrictMode>,
)
