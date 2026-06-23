/**
 * React Hook: useAgentWebSocket
 * Manages WebSocket connection to Hermes agents.
 *
 * Usage:
 * const { isConnected, agentData, subscribe, invoke } = useAgentWebSocket()
 *
 * Subscribe to agent:
 * useEffect(() => {
 *   subscribe('pulso')
 * }, [subscribe])
 *
 * Listen for updates:
 * useEffect(() => {
 *   console.log(agentData.pulso)
 * }, [agentData.pulso])
 */

import { useState, useCallback, useRef, useEffect } from 'react'

export interface AgentOutput {
  agent: string
  status: 'success' | 'error' | 'pending'
  data?: Record<string, any>
  timestamp?: string
  error?: string
}

export interface UseAgentWebSocketReturn {
  isConnected: boolean
  agentData: Record<string, AgentOutput>
  error: string | null
  subscribe: (agent: string) => void
  unsubscribe: (agent: string) => void
  invoke: (agent: string, params?: Record<string, any>) => Promise<AgentOutput | null>
  reconnect: () => void
}

const WS_URL = import.meta.env.VITE_WS_URL || 'wss://antigravity-app-production-175a.up.railway.app/api/v1/ws'
const RECONNECT_DELAY_MS = 3000
const RECONNECT_MAX_ATTEMPTS = 5

export function useAgentWebSocket(): UseAgentWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [agentData, setAgentData] = useState<Record<string, AgentOutput>>({})
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const messageQueueRef = useRef<any[]>([])
  const subscribedAgentsRef = useRef<Set<string>>(new Set())

  // Get JWT token from localStorage or auth context
  const getAuthToken = useCallback((): string | null => {
    // TODO: Replace with actual auth token retrieval
    // For now, read from localStorage (set by auth provider)
    const token = localStorage.getItem('auth_token')
    return token
  }, [])

  // Connect to WebSocket
  const connect = useCallback(() => {
    const token = getAuthToken()
    if (!token) {
      setError('No authentication token available')
      console.error('WebSocket: No auth token')
      return
    }

    try {
      const url = `${WS_URL}?token=${encodeURIComponent(token)}`
      const ws = new WebSocket(url)

      ws.onopen = () => {
        console.log('✅ WebSocket connected')
        setIsConnected(true)
        setError(null)
        reconnectAttemptsRef.current = 0

        // Flush queued messages
        while (messageQueueRef.current.length > 0) {
          const msg = messageQueueRef.current.shift()
          ws.send(JSON.stringify(msg))
        }

        // Re-subscribe to agents after reconnect
        subscribedAgentsRef.current.forEach((agent) => {
          ws.send(JSON.stringify({ type: 'subscribe', agent }))
        })
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)

          if (msg.type === 'heartbeat') {
            // Ignore heartbeat messages
            return
          }

          if (msg.type === 'agent_output') {
            setAgentData((prev) => ({
              ...prev,
              [msg.agent]: {
                agent: msg.agent,
                status: 'success',
                data: msg.data,
                timestamp: msg.timestamp,
              },
            }))
          }
        } catch (e) {
          console.error('WebSocket message parse error:', e)
        }
      }

      ws.onerror = (event) => {
        const errorMsg = 'WebSocket error occurred'
        console.error(errorMsg, event)
        setError(errorMsg)
      }

      ws.onclose = () => {
        console.log('❌ WebSocket disconnected')
        setIsConnected(false)
        wsRef.current = null

        // Attempt reconnect with exponential backoff
        if (reconnectAttemptsRef.current < RECONNECT_MAX_ATTEMPTS) {
          const delay = RECONNECT_DELAY_MS * Math.pow(1.5, reconnectAttemptsRef.current)
          console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1})`)

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++
            connect()
          }, delay)
        } else {
          setError('WebSocket connection failed. Falling back to polling.')
          console.error('Max reconnection attempts reached. Fallback to HTTP polling.')
        }
      }

      wsRef.current = ws
    } catch (e) {
      const errorMsg = `WebSocket connection failed: ${e}`
      console.error(errorMsg)
      setError(errorMsg)
    }
  }, [getAuthToken])

  // Disconnect
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  // Send message (with queueing if not connected)
  const sendMessage = useCallback((msg: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    } else {
      console.warn('WebSocket not connected. Queueing message.', msg)
      messageQueueRef.current.push(msg)
    }
  }, [])

  // Subscribe to agent
  const subscribe = useCallback((agent: string) => {
    if (subscribedAgentsRef.current.has(agent)) {
      return
    }
    subscribedAgentsRef.current.add(agent)
    sendMessage({ type: 'subscribe', agent })
  }, [sendMessage])

  // Unsubscribe from agent
  const unsubscribe = useCallback((agent: string) => {
    subscribedAgentsRef.current.delete(agent)
    sendMessage({ type: 'unsubscribe', agent })
  }, [sendMessage])

  // Invoke agent synchronously
  const invoke = useCallback(
    async (agent: string, params?: Record<string, any>): Promise<AgentOutput | null> => {
      if (!isConnected) {
        setError('WebSocket not connected')
        return null
      }

      return new Promise((resolve) => {
        // Mark as pending
        setAgentData((prev) => ({
          ...prev,
          [agent]: {
            agent,
            status: 'pending',
            timestamp: new Date().toISOString(),
          },
        }))

        // Send invoke request
        sendMessage({
          type: 'agent_invoke',
          agent,
          params: params || {},
        })

        // TODO: Implement proper request tracking with message IDs
        // For now, resolve after a timeout when data arrives
        const timeout = setTimeout(() => {
          resolve(agentData[agent] || null)
        }, 5000)

        // Listen for response (simplified)
        const checkResponse = () => {
          const response = agentData[agent]
          if (response && response.status !== 'pending') {
            clearTimeout(timeout)
            resolve(response)
          } else {
            setTimeout(checkResponse, 100)
          }
        }
        checkResponse()
      })
    },
    [isConnected, sendMessage, agentData],
  )

  // Reconnect
  const reconnect = useCallback(() => {
    disconnect()
    reconnectAttemptsRef.current = 0
    connect()
  }, [connect, disconnect])

  // Auto-connect on mount
  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, []) // Only on mount/unmount

  return {
    isConnected,
    agentData,
    error,
    subscribe,
    unsubscribe,
    invoke,
    reconnect,
  }
}
