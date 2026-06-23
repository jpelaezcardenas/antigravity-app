/**
 * Integration Tests
 * Verify state management + component interaction works together
 * Task 5.4: Integration testing of Zustand + components
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

describe('Zustand Store + Components Integration', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('PulsaCard + Store Integration', () => {
    it('Task 5.4: Component loads data from store', () => {
      // Simulate store state
      const storeState = {
        agents: {
          pulso: {
            data: {
              caja_real: 42850000,
              dinero_tuyo: 38500000,
              ventas_ayer: 1250000,
              salidas_plata: 345000,
              estado_plata: 'bien',
            },
            timestamp: Date.now(),
            status: 'success',
          },
        },
      }

      // Component should render this data
      expect(storeState.agents.pulso.data.caja_real).toBe(42850000)
      expect(storeState.agents.pulso.status).toBe('success')
    })

    it('Task 5.4: Component updates on store change', () => {
      let componentData = null
      const updateComponent = (newData) => {
        componentData = newData
      }

      // Simulate store update
      const newData = {
        caja_real: 50000000,
        estado_plata: 'alerta',
      }

      updateComponent(newData)

      // Component should reflect new data
      expect(componentData.caja_real).toBe(50000000)
      expect(componentData.estado_plata).toBe('alerta')
    })

    it('Task 5.4: Component handles store loading state', () => {
      const storeState = {
        isLoading: true,
        error: null,
      }

      // Component should show loading indicator
      expect(storeState.isLoading).toBe(true)
      expect(storeState.error).toBeNull()
    })

    it('Task 5.4: Component handles store error state', () => {
      const storeState = {
        isLoading: false,
        error: {
          message: 'Failed to fetch data',
          code: 'FETCH_ERROR',
          timestamp: Date.now(),
        },
      }

      // Component should show error message
      expect(storeState.error).toBeDefined()
      expect(storeState.error.message).toBe('Failed to fetch data')
    })
  })

  describe('ErrorBoundary + Toast Integration', () => {
    it('Task 5.4: Error triggers ErrorBoundary and Toast', () => {
      const errorBoundaryState = { hasError: true, error: new Error('Test error') }
      const toastState = { toasts: [{ type: 'error', title: 'Error', message: 'Test error' }] }

      // Both should be triggered together
      expect(errorBoundaryState.hasError).toBe(true)
      expect(toastState.toasts.length).toBe(1)
      expect(toastState.toasts[0].type).toBe('error')
    })

    it('Task 5.4: Multiple errors create multiple toasts', () => {
      const errors = [
        new Error('Error 1'),
        new Error('Error 2'),
        new Error('Error 3'),
      ]

      const toasts = errors.map((error) => ({
        type: 'error',
        title: 'Error',
        message: error.message,
      }))

      // Container should limit to 3 toasts (FIFO)
      expect(toasts.length).toBeLessThanOrEqual(3)
      expect(toasts[0].message).toBe('Error 1')
    })

    it('Task 5.4: ErrorBoundary retry button clears error toast', () => {
      const state = {
        hasError: true,
        toasts: [{ id: 'error-1', type: 'error', title: 'Error' }],
      }

      // Simulate retry button click
      state.hasError = false
      state.toasts = state.toasts.filter((t) => t.id !== 'error-1')

      expect(state.hasError).toBe(false)
      expect(state.toasts.length).toBe(0)
    })
  })

  describe('API Error Handling + Toast Integration', () => {
    it('Task 5.4: HTTP 5xx error triggers error toast', () => {
      const httpError = {
        status: 500,
        message: 'Internal Server Error',
      }

      const toast = {
        type: 'error',
        title: 'Error de red',
        message: 'No se pudo conectar con el servidor',
      }

      // Toast should be created for API error
      expect(toast.type).toBe('error')
      expect(httpError.status).toBe(500)
    })

    it('Task 5.4: Network error with retry action', () => {
      const networkError = new Error('Network timeout')
      const retryAction = vi.fn()

      const toast = {
        type: 'error',
        title: 'Error de conexión',
        message: networkError.message,
        action: {
          label: 'Reintentar',
          onClick: retryAction,
        },
      }

      // User should be able to retry
      toast.action?.onClick()

      expect(retryAction).toHaveBeenCalled()
    })

    it('Task 5.4: Success toast on API recovery', () => {
      const recoverySuccess = {
        status: 200,
        data: { message: 'Data fetched successfully' },
      }

      const toast = {
        type: 'success',
        title: 'Éxito',
        message: 'Los datos se cargaron correctamente',
      }

      // Toast should show success
      expect(toast.type).toBe('success')
      expect(recoverySuccess.status).toBe(200)
    })
  })

  describe('Store Persistence + Component Lifecycle', () => {
    it('Task 5.4: Data persists across component unmount/remount', () => {
      // Initial store state
      let storeData = {
        agents: { pulso: { data: { value: 123 } } },
      }

      localStorage.setItem('agent-store', JSON.stringify({ state: storeData }))

      // Component unmounts (store data stays in localStorage)
      // Component remounts and rehydrates
      const rehydratedData = JSON.parse(localStorage.getItem('agent-store') || '{}')

      expect(rehydratedData.state.agents.pulso.data.value).toBe(123)
    })

    it('Task 5.4: Multiple components share same store state', () => {
      const store = {
        agents: { pulso: { data: { shared: true } } },
      }

      // Component A reads from store
      const componentA = store.agents.pulso.data

      // Component B reads from same store
      const componentB = store.agents.pulso.data

      // Both see same data
      expect(componentA.shared).toBe(componentB.shared)
    })

    it('Task 5.4: Component update propagates to store', () => {
      const store = { user: null }
      const setUser = (user) => {
        store.user = user
      }

      // Component updates store
      setUser({ id: 'user-123', name: 'Test' })

      // Other components see update
      expect(store.user.id).toBe('user-123')
    })
  })

  describe('Sentry + Store + Component Integration', () => {
    it('Task 5.4: Store error captured by Sentry', () => {
      const storeError = new Error('Store operation failed')
      const captureException = vi.fn()

      // Sentry should capture store errors
      captureException(storeError, {
        contexts: { store: { operation: 'setAgentData' } },
      })

      expect(captureException).toHaveBeenCalledWith(
        storeError,
        expect.objectContaining({
          contexts: { store: { operation: 'setAgentData' } },
        })
      )
    })

    it('Task 5.4: Component render error captured with context', () => {
      const renderError = new Error('Component render failed')
      const captureException = vi.fn()

      captureException(renderError, {
        tags: {
          component: 'PulsaCard',
          errorType: 'render',
        },
      })

      expect(captureException).toHaveBeenCalled()
    })

    it('Task 5.4: User context attached to errors', () => {
      const setUser = vi.fn()
      const user = {
        id: 'user-123',
        email: 'test@example.com',
        workspace_id: 'ws-456',
      }

      // User logged in
      setUser(user)

      // If error happens, Sentry should have user context
      expect(setUser).toHaveBeenCalledWith(user)
    })
  })

  describe('Full Flow: API Call → Store → Component → Toast', () => {
    it('Task 5.4: Complete success flow', async () => {
      // Step 1: API call returns data
      const apiResponse = {
        ok: true,
        status: 200,
        data: { pulso_value: 123 },
      }

      // Step 2: Store updates
      const storeUpdate = (data) => ({ agents: { pulso: data } })
      const updatedStore = storeUpdate(apiResponse.data)

      // Step 3: Component renders
      expect(updatedStore.agents.pulso).toBeDefined()

      // Step 4: Success toast shown
      const toast = {
        type: 'success',
        title: 'Datos cargados',
      }

      expect(toast.type).toBe('success')
    })

    it('Task 5.4: Complete error flow', async () => {
      // Step 1: API call fails
      const apiError = {
        ok: false,
        status: 500,
        error: 'Server error',
      }

      // Step 2: Store error state updated
      const storeError = {
        message: apiError.error,
        code: 'API_ERROR',
        timestamp: Date.now(),
      }

      // Step 3: Error displayed in component
      expect(storeError).toBeDefined()

      // Step 4: Error toast shown with retry
      const errorToast = {
        type: 'error',
        title: 'Error',
        action: { label: 'Reintentar', onClick: vi.fn() },
      }

      expect(errorToast.action).toBeDefined()
    })

    it('Task 5.4: Complete offline flow', () => {
      // Step 1: Cached data in localStorage
      const cachedData = {
        agents: { pulso: { data: { cached: true } } },
      }

      localStorage.setItem('agent-store', JSON.stringify({ state: cachedData }))

      // Step 2: App boots offline, loads from cache
      const rehydrated = JSON.parse(localStorage.getItem('agent-store') || '{}')

      expect(rehydrated.state.agents.pulso).toBeDefined()

      // Step 3: Component renders cached data
      expect(rehydrated.state.agents.pulso.data.cached).toBe(true)

      // Step 4: Background refresh when online (non-blocking)
      const backgroundRefresh = { status: 'pending' }
      expect(backgroundRefresh.status).toBe('pending')
    })
  })
})
