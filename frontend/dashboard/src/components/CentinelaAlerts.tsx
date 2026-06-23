/**
 * CentinelaAlerts Component
 * Displays real-time tax/fiscal alerts from Centinela agent
 * Auto-refreshes via WebSocket
 *
 * Data structure:
 * {
 *   alerts: [
 *     {
 *       id: "alert-1",
 *       type: "iva-due",
 *       title: "En 3 días vence tu IVA",
 *       description: "Separa la plata ahora",
 *       urgency: "high" | "medium" | "low",
 *       action_label: "Resolver con Taty",
 *       due_date: "2026-06-25"
 *     }
 *   ]
 * }
 */

import React, { useEffect } from 'react'
import { useAgentWebSocket } from '../hooks/useAgentWebSocket'

export interface Alert {
  id: string
  type: string
  title: string
  description: string
  urgency: 'high' | 'medium' | 'low'
  action_label?: string
  due_date?: string
}

interface CentinelaAlertsProps {
  alerts?: Alert[]
  isLoading?: boolean
  error?: string | null
  onAction?: (alertId: string, action: string) => void
}

const getAlertIcon = (type: string): string => {
  switch (type) {
    case 'iva-due':
      return '📋'
    case 'tax-warning':
      return '⚠️'
    case 'payment-overdue':
      return '🔴'
    case 'compliance':
      return '✓'
    default:
      return '📌'
  }
}

const getAlertColor = (urgency: string): { border: string; bg: string; text: string } => {
  switch (urgency) {
    case 'high':
      return {
        border: 'border-red-500/50',
        bg: 'bg-red-500/10',
        text: 'text-red-400',
      }
    case 'medium':
      return {
        border: 'border-yellow-500/50',
        bg: 'bg-yellow-500/10',
        text: 'text-yellow-400',
      }
    case 'low':
      return {
        border: 'border-blue-500/50',
        bg: 'bg-blue-500/10',
        text: 'text-blue-400',
      }
    default:
      return {
        border: 'border-gray-500/50',
        bg: 'bg-gray-500/10',
        text: 'text-gray-400',
      }
  }
}

export const CentinelaAlerts: React.FC<CentinelaAlertsProps> = ({
  alerts: propsAlerts,
  isLoading: propsLoading,
  error: propsError,
  onAction,
}) => {
  const { agentData, subscribe, invoke } = useAgentWebSocket()

  // Subscribe to centinela agent on mount
  useEffect(() => {
    subscribe('centinela')
  }, [subscribe])

  // Get data from hook or props (props take precedence for standalone mode)
  const agentOutput = agentData.centinela
  const isHookLoading = agentOutput?.status === 'pending'
  const hookError = agentOutput?.status === 'error' ? agentOutput.error : null
  const hookAlerts = Array.isArray(agentOutput?.data) ? agentOutput.data : []

  // Use props if provided, otherwise use hook
  const alerts = propsAlerts || hookAlerts
  const isLoading = propsLoading ?? isHookLoading
  const error = propsError ?? hookError

  // Handle action: call Taty to resolve
  const handleAction = async (alertId: string, action: string) => {
    await invoke('taty', { alert_id: alertId, action })
    onAction?.(alertId, action)
  }

  // Placeholder alerts
  const defaultAlerts: Alert[] = [
    {
      id: 'alert-iva',
      type: 'iva-due',
      title: 'En 3 días vence tu IVA',
      description: 'Separa la plata ahora',
      urgency: 'high',
      action_label: 'Resolver con Taty',
      due_date: '2026-06-25',
    },
    {
      id: 'alert-movements',
      type: 'pending-organization',
      title: 'Hay 5 movimientos sin organizar',
      description: 'Taty te ayuda a clasificarlos',
      urgency: 'medium',
      action_label: 'Organizar ahora',
      due_date: '2026-06-22',
    },
  ]

  const displayAlerts = alerts.length > 0 ? alerts : defaultAlerts
  const isPlaceholder = alerts.length === 0

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <span>🚨</span> Atento a esto
        </h3>
        {isLoading && <span className="text-xs text-gray-500">⏳ Actualizando...</span>}
        {error && <span className="text-xs text-red-400">Error: {error}</span>}
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {displayAlerts.length === 0 ? (
          <div className="bg-slate-900 border border-green-500/30 rounded-lg p-6 text-center">
            <p className="text-green-400">✅ No hay alertas pendientes</p>
            <p className="text-xs text-gray-500 mt-2">Todo está bajo control</p>
          </div>
        ) : (
          displayAlerts.map((alert) => {
            const colors = getAlertColor(alert.urgency)
            return (
              <div
                key={alert.id}
                className={`bg-slate-900 border ${colors.border} ${colors.bg} rounded-lg p-4`}
              >
                <div className="flex gap-3">
                  {/* Icon */}
                  <div className="text-2xl flex-shrink-0 mt-1">
                    {getAlertIcon(alert.type)}
                  </div>

                  {/* Content */}
                  <div className="flex-1">
                    <h4 className={`font-semibold ${colors.text} mb-1`}>{alert.title}</h4>
                    <p className="text-sm text-gray-400 mb-3">{alert.description}</p>

                    {/* Due date if available */}
                    {alert.due_date && (
                      <p className="text-xs text-gray-500 mb-3">
                        Vence: {new Date(alert.due_date).toLocaleDateString('es-CO')}
                      </p>
                    )}

                    {/* Action button */}
                    {alert.action_label && (
                      <button
                        onClick={() => handleAction(alert.id, 'resolve')}
                        className={`text-sm font-medium ${colors.text} hover:underline flex items-center gap-1`}
                      >
                        <span>{alert.action_label}</span>
                        <span>→</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Data freshness indicator */}
      {isPlaceholder && (
        <div className="text-center text-xs text-gray-500 bg-slate-900/50 py-2 rounded">
          📡 Datos de ejemplo (conectando con Centinela...)
        </div>
      )}
    </div>
  )
}
