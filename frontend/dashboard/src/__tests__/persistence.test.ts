/**
 * Persistence Verification Test
 * Ensures Zustand store data survives localStorage
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { useAgentStore } from '../stores/agentStore'

describe('Store Persistence Verification', () => {
  beforeEach(() => {
    localStorage.clear()
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
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('Task 1.5: Data persists to localStorage on update', () => {
    const store = useAgentStore.getState()

    // Add agent data
    store.setAgentData('pulso', {
      data: {
        caja_real: 42850000,
        dinero_tuyo: 38500000,
        ventas_ayer: 1250000,
        salidas_plata: 345000,
        estado_plata: 'bien',
      },
      timestamp: Date.now(),
      status: 'success',
    })

    // Verify localStorage contains the data
    const stored = localStorage.getItem('agent-store')
    expect(stored).toBeDefined()

    const parsed = JSON.parse(stored!)
    expect(parsed.state.agents.pulso).toBeDefined()
    expect(parsed.state.agents.pulso.data.caja_real).toBe(42850000)
  })

  it('Task 1.5: Multiple agents persist independently', () => {
    const store = useAgentStore.getState()

    // Add multiple agents
    store.setAgentData('pulso', {
      data: { pulso_value: 'test1' },
      timestamp: Date.now(),
      status: 'success',
    })

    store.setAgentData('centinela', {
      data: { centinela_value: 'test2' },
      timestamp: Date.now(),
      status: 'success',
    })

    const stored = localStorage.getItem('agent-store')
    const parsed = JSON.parse(stored!)

    expect(Object.keys(parsed.state.agents).length).toBe(2)
    expect(parsed.state.agents.pulso.data.pulso_value).toBe('test1')
    expect(parsed.state.agents.centinela.data.centinela_value).toBe('test2')
  })

  it('Task 1.5: Approvals persist with full metadata', () => {
    const store = useAgentStore.getState()
    const now = new Date().toISOString()

    store.addApproval({
      id: 'approval-1',
      type: 'expense_report',
      title: 'Test Approval',
      description: 'Test description',
      status: 'pending',
      created_at: now,
      updated_at: now,
      agent: 'approval',
      content: { amount: 50000, currency: 'COP' },
    })

    const stored = localStorage.getItem('agent-store')
    const parsed = JSON.parse(stored!)

    expect(parsed.state.approvals.length).toBe(1)
    expect(parsed.state.approvals[0].id).toBe('approval-1')
    expect(parsed.state.approvals[0].content.amount).toBe(50000)
  })

  it('Task 1.5: User profile persists with permissions', () => {
    const store = useAgentStore.getState()

    store.setUser({
      id: 'user-123',
      email: 'test@example.com',
      permissions: ['READ_PULSO', 'APPROVE_EXPENSES'],
      workspace_id: 'ws-456',
    })

    const stored = localStorage.getItem('agent-store')
    const parsed = JSON.parse(stored!)

    expect(parsed.state.user.id).toBe('user-123')
    expect(parsed.state.user.permissions.length).toBe(2)
    expect(parsed.state.user.permissions).toContain('READ_PULSO')
  })

  it('Task 1.5: Transient state (isLoading, error) is NOT persisted', () => {
    const store = useAgentStore.getState()

    store.setLoading(true)
    store.setError({
      message: 'Test error',
      code: 'TEST_ERROR',
      timestamp: Date.now(),
    })

    const stored = localStorage.getItem('agent-store')
    const parsed = JSON.parse(stored!)

    // These should NOT be in localStorage
    expect(parsed.state.isLoading).toBeUndefined()
    expect(parsed.state.error).toBeUndefined()
  })

  it('Task 1.5: Schema version is set correctly', () => {
    const store = useAgentStore.getState()

    store.setAgentData('pulso', {
      data: { test: true },
      timestamp: Date.now(),
      status: 'success',
    })

    const stored = localStorage.getItem('agent-store')
    const parsed = JSON.parse(stored!)

    expect(parsed.version).toBe(1)
  })

  it('Task 1.5: Settings persist with defaults', () => {
    const store = useAgentStore.getState()
    // Settings should be initialized with defaults
    const state = useAgentStore.getState()

    expect(state.settings.theme).toBe('light')
    expect(state.settings.notifications_enabled).toBe(true)
    expect(state.settings.language).toBe('en')

    const stored = localStorage.getItem('agent-store')
    const parsed = JSON.parse(stored!)

    expect(parsed.state.settings.theme).toBe('light')
  })
})
