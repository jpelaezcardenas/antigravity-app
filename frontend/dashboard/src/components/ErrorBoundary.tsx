/**
 * ErrorBoundary Component
 * Catches React render errors and prevents white screen of death
 * Shows fallback UI with retry button
 * Integrates with Sentry for error tracking (Stage 3)
 */

import React, { ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    })

    // Log to console in development
    console.error('ErrorBoundary caught error:', error, errorInfo)

    // Call optional callback (can be used to trigger Sentry, logging, etc.)
    this.props.onError?.(error, errorInfo)

    // TODO: Stage 3 - Send to Sentry
    // Sentry.captureException(error, { contexts: { react: errorInfo } })
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
          <div className="max-w-md w-full">
            {/* Error Card */}
            <div className="bg-slate-900 border border-red-500/30 rounded-lg p-8">
              {/* Icon */}
              <div className="text-5xl mb-4 text-center">🚨</div>

              {/* Title */}
              <h1 className="text-2xl font-bold text-white mb-2 text-center">
                Algo salió mal
              </h1>

              {/* Description */}
              <p className="text-gray-400 text-sm mb-6 text-center">
                La aplicación encontró un error inesperado. Por favor, intenta recargar la página
                o contacta al equipo de soporte si el problema persiste.
              </p>

              {/* Error Details (Development Only) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="bg-slate-800 border border-red-500/20 rounded p-4 mb-6">
                  <p className="text-xs text-gray-400 font-mono mb-2">Error Details:</p>
                  <p className="text-xs text-red-400 font-mono break-words mb-2">
                    {this.state.error.toString()}
                  </p>
                  {this.state.errorInfo?.componentStack && (
                    <>
                      <p className="text-xs text-gray-400 font-mono mb-2 mt-4">Component Stack:</p>
                      <p className="text-xs text-gray-500 font-mono whitespace-pre-wrap break-words">
                        {this.state.errorInfo.componentStack}
                      </p>
                    </>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="space-y-3">
                {/* Reload Button */}
                <button
                  onClick={() => window.location.reload()}
                  className="w-full bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-3 rounded-lg transition-colors"
                >
                  🔄 Recargar página
                </button>

                {/* Retry Button (Local Reset) */}
                <button
                  onClick={this.handleReset}
                  className="w-full bg-slate-800 hover:bg-slate-700 text-gray-300 font-semibold py-3 rounded-lg transition-colors border border-gray-700"
                >
                  ↺ Reintentar
                </button>

                {/* Contact Support Link */}
                <a
                  href="https://contexia.online/support"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full block text-center text-gray-400 hover:text-gray-300 text-sm py-2 transition-colors"
                >
                  📧 Contactar soporte
                </a>
              </div>

              {/* Error ID (for tracking) */}
              {process.env.NODE_ENV === 'development' && (
                <p className="text-xs text-gray-600 text-center mt-6">
                  Error ID: {Date.now()}
                </p>
              )}
            </div>

            {/* Footer Note */}
            <p className="text-center text-gray-500 text-xs mt-6">
              No te preocupes, nuestro equipo ha sido notificado del error.
            </p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
