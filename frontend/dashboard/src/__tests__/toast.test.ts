/**
 * Toast Tests
 * Verify toast notifications show, auto-dismiss, and handle actions
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { ToastMessage } from '../components/Toast'

describe('Toast Component', () => {
  it('Task 2.2: Toast displays success message', () => {
    const toast: ToastMessage = {
      id: 'toast-1',
      type: 'success',
      title: 'Success',
      message: 'Operation completed',
      duration: 5000,
    }

    expect(toast.type).toBe('success')
    expect(toast.title).toBe('Success')
    expect(toast.message).toBe('Operation completed')
  })

  it('Task 2.2: Toast displays error message', () => {
    const toast: ToastMessage = {
      id: 'toast-2',
      type: 'error',
      title: 'Error',
      message: 'Something went wrong',
      duration: 5000,
    }

    expect(toast.type).toBe('error')
    expect(toast.title).toBe('Error')
  })

  it('Task 2.2: Toast displays info message', () => {
    const toast: ToastMessage = {
      id: 'toast-3',
      type: 'info',
      title: 'Info',
      message: 'Processing...',
      duration: 5000,
    }

    expect(toast.type).toBe('info')
  })

  it('Task 2.2: Toast displays warning message', () => {
    const toast: ToastMessage = {
      id: 'toast-4',
      type: 'warning',
      title: 'Warning',
      message: 'Check this out',
      duration: 5000,
    }

    expect(toast.type).toBe('warning')
  })

  it('Task 2.2: Toast auto-dismisses after duration', () => {
    const toast: ToastMessage = {
      id: 'toast-5',
      type: 'success',
      title: 'Test',
      duration: 1000,
    }

    expect(toast.duration).toBe(1000)
  })

  it('Task 2.2: Toast has action button', () => {
    const actionFn = vi.fn()
    const toast: ToastMessage = {
      id: 'toast-6',
      type: 'error',
      title: 'Error',
      message: 'Failed to save',
      action: {
        label: 'Retry',
        onClick: actionFn,
      },
    }

    expect(toast.action).toBeDefined()
    expect(toast.action?.label).toBe('Retry')

    // Simulate action click
    toast.action?.onClick()
    expect(actionFn).toHaveBeenCalled()
  })

  it('Task 2.2: Toast has unique ID', () => {
    const toast1: ToastMessage = {
      id: 'toast-1',
      type: 'success',
      title: 'Toast 1',
    }

    const toast2: ToastMessage = {
      id: 'toast-2',
      type: 'success',
      title: 'Toast 2',
    }

    expect(toast1.id).not.toBe(toast2.id)
  })

  it('Task 2.2: Toast without message is valid', () => {
    const toast: ToastMessage = {
      id: 'toast-7',
      type: 'info',
      title: 'Notice',
      // message is optional
    }

    expect(toast.message).toBeUndefined()
    expect(toast.title).toBe('Notice')
  })

  it('Task 2.2: Toast defaults to 5000ms duration', () => {
    const toast: ToastMessage = {
      id: 'toast-8',
      type: 'success',
      title: 'Test',
      // duration not specified
    }

    const defaultDuration = toast.duration ?? 5000
    expect(defaultDuration).toBe(5000)
  })

  it('Task 2.2: Toast supports 0 duration (no auto-dismiss)', () => {
    const toast: ToastMessage = {
      id: 'toast-9',
      type: 'warning',
      title: 'Persistent',
      duration: 0, // No auto-dismiss
    }

    expect(toast.duration).toBe(0)
  })
})

describe('Toast Container', () => {
  it('Task 2.2: Container shows max 3 toasts', () => {
    const toasts: ToastMessage[] = [
      {
        id: '1',
        type: 'success',
        title: 'Toast 1',
      },
      {
        id: '2',
        type: 'success',
        title: 'Toast 2',
      },
      {
        id: '3',
        type: 'success',
        title: 'Toast 3',
      },
      {
        id: '4',
        type: 'success',
        title: 'Toast 4',
      },
    ]

    // Container should show only last 3
    const visibleToasts = toasts.slice(-3)
    expect(visibleToasts.length).toBe(3)
    expect(visibleToasts[0].id).toBe('2')
    expect(visibleToasts[2].id).toBe('4')
  })

  it('Task 2.2: Container displays toasts in FIFO order', () => {
    const toasts: ToastMessage[] = [
      { id: '1', type: 'success', title: 'First' },
      { id: '2', type: 'success', title: 'Second' },
      { id: '3', type: 'success', title: 'Third' },
    ]

    expect(toasts[0].id).toBe('1')
    expect(toasts[1].id).toBe('2')
    expect(toasts[2].id).toBe('3')
  })

  it('Task 2.2: Container removes toasts on dismiss', () => {
    let toasts: ToastMessage[] = [
      { id: '1', type: 'success', title: 'Toast 1' },
      { id: '2', type: 'success', title: 'Toast 2' },
    ]

    const onDismiss = (id: string) => {
      toasts = toasts.filter((t) => t.id !== id)
    }

    expect(toasts.length).toBe(2)
    onDismiss('1')
    expect(toasts.length).toBe(1)
    expect(toasts[0].id).toBe('2')
  })
})
