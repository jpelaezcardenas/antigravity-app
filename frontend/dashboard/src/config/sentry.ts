/**
 * Sentry Configuration
 * Error tracking and performance monitoring setup
 * Task 3.1: Initialize Sentry for production error tracking
 */

import * as Sentry from '@sentry/react'
import { BrowserTracing } from '@sentry/tracing'

/**
 * Initialize Sentry with DSN from environment
 * Must be called before any other Sentry functions
 */
export const initSentry = () => {
  const dsn = import.meta.env.VITE_SENTRY_DSN || ''

  // Only initialize if DSN is provided
  if (!dsn) {
    console.warn('[Sentry] No DSN provided, error tracking disabled')
    return
  }

  Sentry.init({
    dsn,
    integrations: [
      // Browser performance tracking
      new BrowserTracing({
        // Set sampling rate for performance monitoring
        tracingOrigins: [
          'localhost',
          /^\//,
          // Adjust to your backend domain
          /^https:\/\/antigravity-app-production-175a\.up\.railway\.app/,
        ],
        routingInstrumentation: Sentry.reactRouterV6Instrumentation(
          window.history
        ),
      }),
    ],

    // Set sampling rates
    tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

    // Capture replay for errors only (not all sessions)
    replaysOnErrorSampleRate: 1.0,

    // Environment
    environment: process.env.NODE_ENV || 'development',

    // Release tag
    release: import.meta.env.VITE_APP_VERSION || 'unknown',

    // Disable in development if desired
    enabled: process.env.NODE_ENV === 'production',

    // Before sending event to Sentry
    beforeSend(event) {
      // Filter out known non-critical errors
      if (event.exception) {
        const error = event.exception.values?.[0]?.value || ''
        // Don't track network errors that user can't fix
        if (error.includes('NetworkError') || error.includes('timeout')) {
          return null
        }
      }
      return event
    },

    // Attach user context
    initialScope: {
      tags: {
        component: 'frontend-dashboard',
        app: 'antigravity',
      },
    },
  })

  console.log('[Sentry] Initialized with DSN:', dsn.substring(0, 20) + '...')
}

/**
 * Capture exception manually (e.g., from try/catch)
 */
export const captureException = (error: Error | string, context?: Record<string, any>) => {
  Sentry.withScope((scope) => {
    if (context) {
      Object.entries(context).forEach(([key, value]) => {
        scope.setContext(key, value)
      })
    }
    Sentry.captureException(error)
  })
}

/**
 * Capture message (for non-error events)
 */
export const captureMessage = (message: string, level: 'fatal' | 'error' | 'warning' | 'info' = 'info') => {
  Sentry.captureMessage(message, level)
}

/**
 * Set user context for error tracking
 */
export const setUserContext = (user: { id: string; email?: string; username?: string }) => {
  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.username,
  })
}

/**
 * Clear user context (on logout)
 */
export const clearUserContext = () => {
  Sentry.setUser(null)
}

/**
 * Start transaction for performance monitoring
 */
export const startTransaction = (name: string, op: string = 'http.request') => {
  return Sentry.startTransaction({
    name,
    op,
  })
}

/**
 * Add breadcrumb for user action tracking
 */
export const addBreadcrumb = (message: string, category: string = 'action', data?: Record<string, any>) => {
  Sentry.addBreadcrumb({
    category,
    message,
    level: 'info',
    data,
  })
}

export default Sentry
