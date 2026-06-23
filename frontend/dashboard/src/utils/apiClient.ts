/**
 * API Client Utility
 * Centralizes fetch calls with error handling and toast notifications
 * Task 2.6: Toast calls integrated into all API error handlers
 * Task 3.3: Sentry error capture for network errors
 */

import { useToast } from '../hooks/useToast'
import * as Sentry from '@sentry/react'

export interface ApiResponse<T = any> {
  ok: boolean
  status: number
  data?: T
  error?: string
}

/**
 * Fetch wrapper with error handling and Sentry integration
 * Task 3.3: Capture errors to Sentry for production monitoring
 */
export async function apiFetch(
  url: string,
  options?: RequestInit
): Promise<ApiResponse> {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorText = await response.text()

      // Capture HTTP errors to Sentry (4xx, 5xx)
      if (response.status >= 500) {
        Sentry.captureMessage(
          `API Error: ${response.status} ${url}`,
          'error'
        )
      } else if (response.status >= 400) {
        Sentry.captureMessage(
          `API Client Error: ${response.status} ${url}`,
          'warning'
        )
      }

      return {
        ok: false,
        status: response.status,
        error: errorText || `HTTP ${response.status}`,
      }
    }

    const data = await response.json()
    return {
      ok: true,
      status: response.status,
      data,
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error'

    // Capture network/parsing errors to Sentry
    Sentry.captureException(error, {
      tags: {
        errorType: 'api_error',
        url,
      },
      contexts: {
        api: {
          url,
          method: options?.method || 'GET',
        },
      },
    })

    return {
      ok: false,
      status: 0,
      error: message,
    }
  }
}

/**
 * Hook-aware API fetch with automatic toast on error
 * Use this from React components
 */
export const useApiFetch = () => {
  const toast = useToast()

  const fetchWithToast = async (
    url: string,
    options?: RequestInit & { silentFail?: boolean }
  ): Promise<ApiResponse> => {
    const result = await apiFetch(url, options)

    if (!result.ok && !options?.silentFail) {
      toast.error('Error de red', result.error || 'No se pudo conectar con el servidor')
    }

    return result
  }

  return { fetchWithToast }
}

/**
 * Utility function for non-hook contexts
 * Logs errors to console but doesn't show toast
 * (toast requires useToast hook)
 */
export const fetchWithErrorLogging = async (
  url: string,
  options?: RequestInit
): Promise<ApiResponse> => {
  const result = await apiFetch(url, options)

  if (!result.ok) {
    console.error(`[API] Error fetching ${url}:`, result.error)
  }

  return result
}

/**
 * Common API methods with error handling
 */
export const apiGet = (url: string) =>
  fetchWithErrorLogging(url, { method: 'GET' })

export const apiPost = (url: string, data: any) =>
  fetchWithErrorLogging(url, {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const apiPut = (url: string, data: any) =>
  fetchWithErrorLogging(url, {
    method: 'PUT',
    body: JSON.stringify(data),
  })

export const apiDelete = (url: string) =>
  fetchWithErrorLogging(url, { method: 'DELETE' })
