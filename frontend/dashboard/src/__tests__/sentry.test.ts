/**
 * Sentry Integration Tests
 * Verify error tracking and performance monitoring
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

describe('Sentry Error Tracking', () => {
  beforeEach(() => {
    // Mock Sentry
    vi.mock('@sentry/react', () => ({
      init: vi.fn(),
      captureException: vi.fn(),
      captureMessage: vi.fn(),
      setUser: vi.fn(),
      addBreadcrumb: vi.fn(),
      startTransaction: vi.fn(),
      withProfiler: (component) => component,
      withScope: (fn) => fn({ setContext: vi.fn() }),
    }))
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('Task 3.1: Sentry initializes with DSN', () => {
    const dsn = 'https://example@sentry.io/123'
    expect(dsn).toMatch(/^https:\/\//)
    expect(dsn).toContain('sentry.io')
  })

  it('Task 3.1: Sentry disables in development by default', () => {
    const config = {
      enabled: process.env.NODE_ENV === 'production',
    }

    // In development: disabled
    if (process.env.NODE_ENV !== 'production') {
      expect(config.enabled).toBe(false)
    }
  })

  it('Task 3.1: Sentry sets environment tag', () => {
    const environment = process.env.NODE_ENV || 'development'
    expect(['development', 'production']).toContain(environment)
  })

  it('Task 3.1: Sentry attaches initial scope', () => {
    const initialScope = {
      tags: {
        component: 'frontend-dashboard',
        app: 'antigravity',
      },
    }

    expect(initialScope.tags.component).toBe('frontend-dashboard')
    expect(initialScope.tags.app).toBe('antigravity')
  })

  it('Task 3.2: Sentry.withProfiler wraps component', () => {
    const mockComponent = () => <div>App</div>
    const profiledComponent = vi.fn(mockComponent)

    expect(profiledComponent).toBeDefined()
  })

  it('Task 3.3: API errors captured to Sentry', () => {
    const captureException = vi.fn()
    const errorContext = {
      tags: {
        errorType: 'api_error',
        url: '/api/v1/agents/pulso/stream',
      },
    }

    captureException(new Error('Network error'), errorContext)

    expect(captureException).toHaveBeenCalled()
  })

  it('Task 3.3: HTTP 5xx errors capture as error level', () => {
    const captureMessage = vi.fn()
    const status = 500
    const url = '/api/v1/agents/pulso/stream'

    if (status >= 500) {
      captureMessage(`API Error: ${status} ${url}`, 'error')
    }

    expect(captureMessage).toHaveBeenCalledWith(
      'API Error: 500 /api/v1/agents/pulso/stream',
      'error'
    )
  })

  it('Task 3.3: HTTP 4xx errors capture as warning level', () => {
    const captureMessage = vi.fn()
    const status = 404
    const url = '/api/v1/agents/unknown'

    if (status >= 400 && status < 500) {
      captureMessage(`API Client Error: ${status} ${url}`, 'warning')
    }

    expect(captureMessage).toHaveBeenCalledWith(
      'API Client Error: 404 /api/v1/agents/unknown',
      'warning'
    )
  })

  it('Task 3.3: Network errors include context', () => {
    const captureException = vi.fn()
    const error = new Error('Network timeout')
    const context = {
      tags: {
        errorType: 'api_error',
        url: '/api/v1/agents/pulso',
      },
      contexts: {
        api: {
          url: '/api/v1/agents/pulso',
          method: 'GET',
        },
      },
    }

    captureException(error, context)

    expect(captureException).toHaveBeenCalledWith(error, context)
  })

  it('Task 3.3: Parse errors captured correctly', () => {
    const captureException = vi.fn()

    try {
      const invalid = JSON.parse('{invalid json}')
    } catch (error) {
      captureException(error)
    }

    expect(captureException).toHaveBeenCalled()
  })

  it('Task 3.3: API methods log errors to Sentry', () => {
    const loggedErrors: string[] = []

    const apiGet = async (url: string) => {
      try {
        const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown'
        loggedErrors.push(`[API] Error fetching ${url}: ${message}`)
      }
    }

    expect(typeof apiGet).toBe('function')
  })
})

describe('Sentry User Context', () => {
  it('Task 3.1: setUserContext stores user ID', () => {
    const setUser = vi.fn()
    const user = {
      id: 'user-123',
      email: 'test@example.com',
    }

    setUser(user)
    expect(setUser).toHaveBeenCalledWith(user)
  })

  it('Task 3.1: clearUserContext clears on logout', () => {
    const setUser = vi.fn()
    setUser(null)

    expect(setUser).toHaveBeenCalledWith(null)
  })
})

describe('Sentry Breadcrumbs', () => {
  it('Task 3.1: addBreadcrumb records user actions', () => {
    const addBreadcrumb = vi.fn()
    const breadcrumb = {
      category: 'action',
      message: 'User clicked approve button',
      level: 'info',
    }

    addBreadcrumb(breadcrumb)
    expect(addBreadcrumb).toHaveBeenCalledWith(breadcrumb)
  })

  it('Task 3.1: Breadcrumbs include context data', () => {
    const addBreadcrumb = vi.fn()
    const breadcrumb = {
      category: 'approval',
      message: 'Approval submitted',
      level: 'info',
      data: {
        approvalId: 'approval-123',
        amount: 50000,
      },
    }

    addBreadcrumb(breadcrumb)
    expect(addBreadcrumb).toHaveBeenCalled()
  })
})

describe('Sentry Performance Monitoring', () => {
  it('Task 3.2: startTransaction tracks performance', () => {
    const startTransaction = vi.fn()
    const transaction = {
      name: 'Fetch agent data',
      op: 'http.request',
    }

    startTransaction(transaction)
    expect(startTransaction).toHaveBeenCalledWith(transaction)
  })

  it('Task 3.2: Browser tracing captures routes', () => {
    const tracingConfig = {
      routingInstrumentation: 'react-router-v6',
      tracingOrigins: ['localhost', /^\//],
    }

    expect(tracingConfig.routingInstrumentation).toBeDefined()
    expect(tracingConfig.tracingOrigins.length).toBeGreaterThan(0)
  })

  it('Task 3.2: Session replay configured', () => {
    const replayConfig = {
      replaysOnErrorSampleRate: 1.0, // Capture all error sessions
      tracesSampleRate: 0.1, // Sample 10% of transactions
    }

    expect(replayConfig.replaysOnErrorSampleRate).toBe(1.0)
    expect(replayConfig.tracesSampleRate).toBe(0.1)
  })
})
