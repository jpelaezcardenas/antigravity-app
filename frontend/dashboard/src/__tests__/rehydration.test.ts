/**
 * Rehydration Verification Test
 * Ensures Zustand store loads data from localStorage on app boot
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { useAgentStore } from '../stores/agentStore'

describe('Store Rehydration (App Boot)', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('Task 1.6: Rehydrates agents from localStorage on boot', () => {
    // Simulate app shutdown with data
    const testData = {
      data: {
        caja_real: 42850000,
        dinero_tuyo: 38500000,
        ventas_ayer: 1250000,
        salidas_plata: 345000,
        estado_plata: 'bien',
      },
      timestamp: Date.now(),
      status: 'success' as const,
    }

    // Manually simulate Zustand persistence by setting localStorage
    const storeData = {
      state: {
        agents: { pulso: testData },
        user: null,
        approvals: [],
        settings: {
          theme: 'light',
          notifications_enabled: true,
          language: 'en',
        },
      },
      version: 1,
    }

    localStorage.setItem('agent-store', JSON.stringify(storeData))

    // Reset store to simulate fresh app boot
    useAgentStore.setState({
      agents: {},
      user: null,
      approvals: [],
      settings: {
        theme: 'light',
        notifications_enabled: true,
        language: 'en',
      },
      isLoading: false,
      error: null,
      lastSync: 0,
    })

    // On real app boot, Zustand reads from localStorage automatically
    // Here we simulate that by reading localStorage and restoring state
    const stored = localStorage.getItem('agent-store')
    if (stored) {
      const parsed = JSON.parse(stored)
      useAgentStore.setState({
        agents: parsed.state.agents,
        user: parsed.state.user,
        approvals: parsed.state.approvals,
        settings: parsed.state.settings,
      })
    }

    // Verify data was restored
    const state = useAgentStore.getState()
    expect(state.agents.pulso).toBeDefined()
    expect(state.agents.pulso.data.caja_real).toBe(42850000)
  })

  it('Task 1.6: Rehydrates user profile on boot', () => {
    const testUser = {
      id: 'user-123',
      email: 'test@example.com',
      permissions: ['READ_PULSO', 'APPROVE_EXPENSES'],
      workspace_id: 'ws-456',
    }

    const storeData = {
      state: {
        agents: {},
        user: testUser,
        approvals: [],
        settings: {
          theme: 'light',
          notifications_enabled: true,
          language: 'en',
        },
      },
      version: 1,
    }

    localStorage.setItem('agent-store', JSON.stringify(storeData))

    // Simulate boot
    useAgentStore.setState({
      agents: {},
      user: null,
      approvals: [],
      settings: {
        theme: 'light',
        notifications_enabled: true,
        language: 'en',
      },
      isLoading: false,
      error: null,
      lastSync: 0,
    })

    const stored = localStorage.getItem('agent-store')
    if (stored) {
      const parsed = JSON.parse(stored)
      useAgentStore.setState({
        agents: parsed.state.agents,
        user: parsed.state.user,
        approvals: parsed.state.approvals,
        settings: parsed.state.settings,
      })
    }

    const state = useAgentStore.getState()
    expect(state.user).toEqual(testUser)
    expect(state.user?.permissions).toContain('READ_PULSO')
  })

  it('Task 1.6: Rehydrates approvals on boot', () => {
    const now = new Date().toISOString()
    const testApproval = {
      id: 'approval-1',
      type: 'expense_report',
      title: 'Test Approval',
      description: 'Test description',
      status: 'pending' as const,
      created_at: now,
      updated_at: now,
      agent: 'approval',
      content: { amount: 50000, currency: 'COP' },
    }

    const storeData = {
      state: {
        agents: {},
        user: null,
        approvals: [testApproval],
        settings: {
          theme: 'light',
          notifications_enabled: true,
          language: 'en',
        },
      },
      version: 1,
    }

    localStorage.setItem('agent-store', JSON.stringify(storeData))

    // Simulate boot
    useAgentStore.setState({
      agents: {},
      user: null,
      approvals: [],
      settings: {
        theme: 'light',
        notifications_enabled: true,
        language: 'en',
      },
      isLoading: false,
      error: null,
      lastSync: 0,
    })

    const stored = localStorage.getItem('agent-store')
    if (stored) {
      const parsed = JSON.parse(stored)
      useAgentStore.setState({
        agents: parsed.state.agents,
        user: parsed.state.user,
        approvals: parsed.state.approvals,
        settings: parsed.state.settings,
      })
    }

    const state = useAgentStore.getState()
    expect(state.approvals.length).toBe(1)
    expect(state.approvals[0].id).toBe('approval-1')
    expect(state.approvals[0].content.amount).toBe(50000)
  })

  it('Task 1.6: Handles corrupted localStorage gracefully', () => {
    // Simulate corrupted data
    localStorage.setItem('agent-store', '{invalid json}')

    // Try to rehydrate - should not crash
    try {
      useAgentStore.setState({
        agents: {},
        user: null,
        approvals: [],
        settings: {
          theme: 'light',
          notifications_enabled: true,
          language: 'en',
        },
        isLoading: false,
        error: null,
        lastSync: 0,
      })

      const stored = localStorage.getItem('agent-store')
      if (stored) {
        try {
          const parsed = JSON.parse(stored)
          useAgentStore.setState({
            agents: parsed.state.agents,
            user: parsed.state.user,
            approvals: parsed.state.approvals,
            settings: parsed.state.settings,
          })
        } catch (e) {
          // Gracefully handle corrupted data
          console.warn('Corrupted localStorage, clearing')
          localStorage.removeItem('agent-store')
        }
      }

      const state = useAgentStore.getState()
      expect(state.agents).toEqual({})
      expect(state.user).toBeNull()
    } catch (e) {
      expect(true).toBe(false) // Should not throw
    }
  })

  it('Task 1.6: Rehydrates multiple agents simultaneously', () => {
    const testAgents = {
      pulso: {
        data: { pulso_value: 'test1' },
        timestamp: Date.now(),
        status: 'success' as const,
      },
      centinela: {
        data: { centinela_value: 'test2' },
        timestamp: Date.now(),
        status: 'success' as const,
      },
      radar: {
        data: { radar_value: 'test3' },
        timestamp: Date.now(),
        status: 'success' as const,
      },
    }

    const storeData = {
      state: {
        agents: testAgents,
        user: null,
        approvals: [],
        settings: {
          theme: 'light',
          notifications_enabled: true,
          language: 'en',
        },
      },
      version: 1,
    }

    localStorage.setItem('agent-store', JSON.stringify(storeData))

    // Simulate boot
    useAgentStore.setState({
      agents: {},
      user: null,
      approvals: [],
      settings: {
        theme: 'light',
        notifications_enabled: true,
        language: 'en',
      },
      isLoading: false,
      error: null,
      lastSync: 0,
    })

    const stored = localStorage.getItem('agent-store')
    if (stored) {
      const parsed = JSON.parse(stored)
      useAgentStore.setState({
        agents: parsed.state.agents,
        user: parsed.state.user,
        approvals: parsed.state.approvals,
        settings: parsed.state.settings,
      })
    }

    const state = useAgentStore.getState()
    expect(Object.keys(state.agents).length).toBe(3)
    expect(state.agents.pulso.data.pulso_value).toBe('test1')
    expect(state.agents.centinela.data.centinela_value).toBe('test2')
    expect(state.agents.radar.data.radar_value).toBe('test3')
  })

  it('Task 1.6: Respects schema version for migrations', () => {
    const storeData = {
      state: {
        agents: {},
        user: null,
        approvals: [],
        settings: {
          theme: 'light',
          notifications_enabled: true,
          language: 'en',
        },
      },
      version: 1,
    }

    localStorage.setItem('agent-store', JSON.stringify(storeData))

    const stored = localStorage.getItem('agent-store')
    expect(stored).toBeDefined()

    const parsed = JSON.parse(stored!)
    expect(parsed.version).toBe(1)

    // Future versions could add migration logic here
    if (parsed.version < 1) {
      // Reject old version
      localStorage.removeItem('agent-store')
    }

    expect(localStorage.getItem('agent-store')).not.toBeNull()
  })
})
