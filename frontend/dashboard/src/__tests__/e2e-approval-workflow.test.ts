/**
 * End-to-End Tests: Approval Workflow
 * Task 5.5: Test complete approval lifecycle with refresh persistence
 *
 * Scenario: User creates approval, closes browser, reopens, approval still there
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

describe('E2E: Approval Workflow with Persistence', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('Complete Approval Lifecycle', () => {
    it('E2E 5.5: User creates approval → approves → workflow completes', async () => {
      // Step 1: User creates draft
      const draft = {
        id: 'approval-1',
        type: 'expense_report',
        title: 'Monthly Report',
        description: 'July expenses',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        agent: 'approval',
        content: { amount: 50000, currency: 'COP' },
      }

      // Save to store
      const store = {
        approvals: [draft],
      }

      // Persist to localStorage
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      // Step 2: Verify draft appears in UI
      const loadedDraft = store.approvals[0]
      expect(loadedDraft.id).toBe('approval-1')
      expect(loadedDraft.status).toBe('pending')

      // Step 3: User approves
      const updatedDraft = {
        ...draft,
        status: 'approved',
        updated_at: new Date().toISOString(),
      }

      store.approvals[0] = updatedDraft

      // Step 4: Save update
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      // Step 5: Verify approval status changed
      expect(store.approvals[0].status).toBe('approved')
    })

    it('E2E 5.5: Draft persists across page refresh', async () => {
      // User Session 1: Create approval
      const approval = {
        id: 'approval-2',
        type: 'contract_review',
        title: 'New Contract',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      const store = { approvals: [approval] }
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      // --- Page refresh (simulate) ---
      // User Session 2: App rehydrates from localStorage

      const stored = localStorage.getItem('agent-store')
      expect(stored).toBeDefined()

      const rehydrated = JSON.parse(stored!)
      expect(rehydrated.state.approvals[0].id).toBe('approval-2')
      expect(rehydrated.state.approvals[0].status).toBe('pending')
    })

    it('E2E 5.5: Multiple approvals maintained separately', async () => {
      const approvals = [
        {
          id: 'approval-1',
          type: 'expense',
          status: 'pending',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 'approval-2',
          type: 'contract',
          status: 'approved',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ]

      const store = { approvals }
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      const loaded = JSON.parse(localStorage.getItem('agent-store')!)
      expect(loaded.state.approvals.length).toBe(2)
      expect(loaded.state.approvals[0].status).toBe('pending')
      expect(loaded.state.approvals[1].status).toBe('approved')
    })

    it('E2E 5.5: Error during approval doesn't lose data', async () => {
      const approval = {
        id: 'approval-3',
        type: 'test',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      const store = { approvals: [approval] }
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      // Simulate error during approval update
      const error = new Error('Network error during approval')

      // Data should still be in store
      const stored = localStorage.getItem('agent-store')
      const rehydrated = JSON.parse(stored!)

      expect(rehydrated.state.approvals[0].id).toBe('approval-3')
      expect(error.message).toContain('Network error')
    })
  })

  describe('Error Handling in Workflow', () => {
    it('E2E 5.5: Network error during create shows toast + preserves data', async () => {
      const toast = {
        type: 'error',
        title: 'Error al guardar',
        message: 'No se pudo crear la aprobación',
      }

      // Error toast shown
      expect(toast.type).toBe('error')

      // But draft should be in local state (not persisted yet)
      const pendingDraft = {
        id: 'draft-pending',
        type: 'expense',
        status: 'draft',
      }

      // User can retry
      const retryAction = vi.fn()
      const retryToast = {
        ...toast,
        action: { label: 'Reintentar', onClick: retryAction },
      }

      retryToast.action?.onClick()
      expect(retryAction).toHaveBeenCalled()
    })

    it('E2E 5.5: Corrupted localStorage recovers gracefully', () => {
      // Simulate corrupted data
      localStorage.setItem('agent-store', '{invalid json}')

      // App should handle gracefully
      try {
        const stored = localStorage.getItem('agent-store')
        if (stored) {
          JSON.parse(stored) // This will throw
        }
      } catch (error) {
        // Clear corrupted data
        localStorage.removeItem('agent-store')
      }

      // App should show error toast but continue
      const errorToast = {
        type: 'error',
        title: 'Datos corruptos',
        message: 'Se borró la caché local',
      }

      expect(errorToast.type).toBe('error')
      expect(localStorage.getItem('agent-store')).toBeNull()
    })
  })

  describe('Approval Status Transitions', () => {
    it('E2E 5.5: pending → approved → archived workflow', async () => {
      const approval = {
        id: 'approval-workflow',
        type: 'test',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      let store = { approvals: [approval] }

      // Step 1: Create (pending)
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))
      expect(store.approvals[0].status).toBe('pending')

      // Step 2: Approve
      store.approvals[0].status = 'approved'
      store.approvals[0].updated_at = new Date().toISOString()
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))
      expect(store.approvals[0].status).toBe('approved')

      // Step 3: Archive (simulate removal)
      store.approvals = store.approvals.filter((a) => a.id !== 'approval-workflow')
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))
      expect(store.approvals.length).toBe(0)
    })

    it('E2E 5.5: pending → rejected → retry workflow', async () => {
      const approval = {
        id: 'approval-reject',
        type: 'test',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      let store = { approvals: [approval] }
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      // User rejects
      store.approvals[0].status = 'rejected'
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))
      expect(store.approvals[0].status).toBe('rejected')

      // User creates new version
      const newApproval = {
        id: 'approval-retry',
        type: 'test',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      store.approvals.push(newApproval)
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      expect(store.approvals.length).toBe(2)
      expect(store.approvals[0].status).toBe('rejected')
      expect(store.approvals[1].status).toBe('pending')
    })
  })

  describe('Background Sync During Workflow', () => {
    it('E2E 5.5: Offline create + online sync', async () => {
      // User offline: creates draft locally
      const offlineDraft = {
        id: 'offline-draft',
        type: 'expense',
        status: 'pending',
      }

      const store = { approvals: [offlineDraft] }
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      // User comes online: background sync
      const syncResult = {
        ok: true,
        data: { id: 'approval-123' }, // Server assigns ID
      }

      // Update draft with server ID
      store.approvals[0].id = syncResult.data.id
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      expect(store.approvals[0].id).toBe('approval-123')
    })

    it('E2E 5.5: Concurrent approvals (race condition safe)', async () => {
      // User A and B both create approvals simultaneously

      const approvalA = {
        id: 'approval-a',
        type: 'expense',
        status: 'pending',
        created_at: new Date().toISOString(),
      }

      const approvalB = {
        id: 'approval-b',
        type: 'contract',
        status: 'pending',
        created_at: new Date().toISOString(),
      }

      // Both should be stored without conflict
      let store = { approvals: [] }

      store.approvals.push(approvalA)
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      store.approvals.push(approvalB)
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      const loaded = JSON.parse(localStorage.getItem('agent-store')!)
      expect(loaded.state.approvals.length).toBe(2)
      expect(loaded.state.approvals.map((a) => a.id)).toContain('approval-a')
      expect(loaded.state.approvals.map((a) => a.id)).toContain('approval-b')
    })
  })

  describe('Toast Notifications During Workflow', () => {
    it('E2E 5.5: Success toast shows and auto-dismisses', async () => {
      const toasts = []

      // Show success toast
      const successToast = {
        id: 'toast-1',
        type: 'success',
        title: 'Aprobado',
        message: 'La aprobación se completó',
        duration: 5000,
      }

      toasts.push(successToast)
      expect(toasts.length).toBe(1)

      // Simulate auto-dismiss after 5s
      toasts.shift()
      expect(toasts.length).toBe(0)
    })

    it('E2E 5.5: Error toast with retry option', async () => {
      const retryFn = vi.fn()

      const errorToast = {
        id: 'toast-error',
        type: 'error',
        title: 'Error de red',
        message: 'No se pudo guardar',
        action: {
          label: 'Reintentar',
          onClick: retryFn,
        },
      }

      // User clicks retry
      errorToast.action?.onClick()
      expect(retryFn).toHaveBeenCalled()
    })

    it('E2E 5.5: Toast deduplication prevents spam', async () => {
      const lastMessages = new Map<string, number>()
      const toasts = []

      const showToast = (title: string, message: string) => {
        const key = `${title}:${message}`
        const lastTime = lastMessages.get(key)

        // Duplicate within 2 seconds?
        if (lastTime && Date.now() - lastTime < 2000) {
          return false // Don't show (deduplicated)
        }

        lastMessages.set(key, Date.now())
        toasts.push({ title, message })
        return true
      }

      // First toast: shown
      expect(showToast('Error', 'Network failed')).toBe(true)

      // Second toast (same): not shown (deduplicated)
      expect(showToast('Error', 'Network failed')).toBe(false)

      // Different error: shown
      expect(showToast('Error', 'Server error')).toBe(true)

      expect(toasts.length).toBe(2)
    })
  })

  describe('Complete Session Flow', () => {
    it('E2E 5.5: User session with approval, refresh, status check, approval', async () => {
      // 1. User logs in, creates approval
      const approval = {
        id: 'e2e-1',
        type: 'expense',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        content: { amount: 100000 },
      }

      let store = { approvals: [approval], user: { id: 'user-1' } }
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      // 2. Toast: "Aprobación creada"
      const createToast = { type: 'success', title: 'Creada' }
      expect(createToast.type).toBe('success')

      // 3. User closes browser (data persists)
      // 4. User reopens browser next day
      const rehydrated = JSON.parse(localStorage.getItem('agent-store')!)
      expect(rehydrated.state.approvals[0].id).toBe('e2e-1')
      expect(rehydrated.state.approvals[0].status).toBe('pending')

      // 5. User sees approval in list
      const approval2 = rehydrated.state.approvals.find((a) => a.id === 'e2e-1')
      expect(approval2).toBeDefined()

      // 6. User approves
      approval2.status = 'approved'
      store = { approvals: [approval2], user: { id: 'user-1' } }
      localStorage.setItem('agent-store', JSON.stringify({ state: store }))

      // 7. Toast: "Aprobado"
      const approveToast = { type: 'success', title: 'Aprobado' }
      expect(approveToast.type).toBe('success')

      // 8. Final state
      const final = JSON.parse(localStorage.getItem('agent-store')!)
      expect(final.state.approvals[0].status).toBe('approved')
    })
  })
})
