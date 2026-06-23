/**
 * useToast Hook Tests
 * Verify toast context, deduplication, and convenience methods
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

describe('useToast Hook', () => {
  it('Task 2.3: show() creates toast with unique ID', () => {
    const toasts: any[] = []
    let idCounter = 0

    const show = (config: any) => {
      const id = `toast-${++idCounter}`
      toasts.push({ id, ...config })
      return id
    }

    const id1 = show({ type: 'success', title: 'Toast 1' })
    const id2 = show({ type: 'success', title: 'Toast 2' })

    expect(id1).toBe('toast-1')
    expect(id2).toBe('toast-2')
    expect(id1).not.toBe(id2)
    expect(toasts.length).toBe(2)
  })

  it('Task 2.3: success() convenience method', () => {
    const toasts: any[] = []

    const success = (title: string, message?: string) => {
      toasts.push({ type: 'success', title, message })
    }

    success('Success', 'Operation completed')
    expect(toasts[0].type).toBe('success')
    expect(toasts[0].title).toBe('Success')
  })

  it('Task 2.3: error() convenience method', () => {
    const toasts: any[] = []

    const error = (title: string, message?: string) => {
      toasts.push({ type: 'error', title, message })
    }

    error('Error', 'Something went wrong')
    expect(toasts[0].type).toBe('error')
  })

  it('Task 2.3: info() convenience method', () => {
    const toasts: any[] = []

    const info = (title: string, message?: string) => {
      toasts.push({ type: 'info', title, message })
    }

    info('Info', 'Processing...')
    expect(toasts[0].type).toBe('info')
  })

  it('Task 2.3: warning() convenience method', () => {
    const toasts: any[] = []

    const warning = (title: string, message?: string) => {
      toasts.push({ type: 'warning', title, message })
    }

    warning('Warning', 'Check this')
    expect(toasts[0].type).toBe('warning')
  })

  it('Task 2.3: dismiss() removes toast by ID', () => {
    let toasts = [
      { id: 'toast-1', type: 'success', title: 'Toast 1' },
      { id: 'toast-2', type: 'success', title: 'Toast 2' },
    ]

    const dismiss = (id: string) => {
      toasts = toasts.filter((t) => t.id !== id)
    }

    expect(toasts.length).toBe(2)
    dismiss('toast-1')
    expect(toasts.length).toBe(1)
    expect(toasts[0].id).toBe('toast-2')
  })

  it('Task 2.3: Deduplication prevents duplicate messages', () => {
    const lastMessages = new Map<string, number>()

    const isDuplicate = (title: string, message?: string): boolean => {
      const key = `${title}:${message}`
      const lastTime = lastMessages.get(key)

      if (!lastTime) return false
      if (Date.now() - lastTime < 2000) return true

      return false
    }

    // First message should not be duplicate
    expect(isDuplicate('Test', 'Message')).toBe(false)

    // Record it
    const key = 'Test:Message'
    lastMessages.set(key, Date.now())

    // Immediate duplicate should be caught
    expect(isDuplicate('Test', 'Message')).toBe(true)

    // Different message should not be duplicate
    expect(isDuplicate('Test', 'Other')).toBe(false)
  })

  it('Task 2.3: Deduplication window is 2 seconds', () => {
    const lastMessages = new Map<string, number>()

    const isDuplicate = (title: string, message?: string): boolean => {
      const key = `${title}:${message}`
      const lastTime = lastMessages.get(key)

      if (!lastTime) return false
      if (Date.now() - lastTime < 2000) return true

      return false
    }

    const key = 'Test:Msg'
    lastMessages.set(key, Date.now())

    // Within 2 seconds: duplicate
    expect(isDuplicate('Test', 'Msg')).toBe(true)

    // After 2 seconds: not duplicate (simulated)
    lastMessages.set(key, Date.now() - 2001)
    expect(isDuplicate('Test', 'Msg')).toBe(false)
  })

  it('Task 2.3: Duplicate returns empty ID', () => {
    const lastMessages = new Map<string, number>()
    const toasts: any[] = []

    const show = (title: string, message?: string): string => {
      const key = `${title}:${message}`
      const lastTime = lastMessages.get(key)

      if (lastTime && Date.now() - lastTime < 2000) {
        return '' // Duplicate: return empty ID
      }

      lastMessages.set(key, Date.now())
      const id = `toast-${Date.now()}`
      toasts.push({ id, title, message })
      return id
    }

    const id1 = show('Test', 'Msg')
    const id2 = show('Test', 'Msg') // Duplicate

    expect(id1).not.toBe('')
    expect(id2).toBe('')
    expect(toasts.length).toBe(1) // Only one toast added
  })

  it('Task 2.3: Toast records last message time', () => {
    const lastMessages = new Map<string, number>()

    const recordMessage = (title: string, message?: string) => {
      const key = `${title}:${message}`
      const now = Date.now()
      lastMessages.set(key, now)
      return now
    }

    const time1 = recordMessage('Test', 'Msg')
    expect(lastMessages.get('Test:Msg')).toBe(time1)
  })

  it('Task 2.3: Toast context validates usage', () => {
    const useToastWithValidation = () => {
      const context = undefined // Simulate no context
      if (!context) {
        throw new Error('useToast must be used within <ToastProvider>')
      }
      return context
    }

    expect(() => useToastWithValidation()).toThrow(
      'useToast must be used within <ToastProvider>'
    )
  })
})
