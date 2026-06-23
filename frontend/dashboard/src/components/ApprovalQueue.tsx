/**
 * ApprovalQueue Component
 * Human-in-the-Loop interface for approving/rejecting agent drafts
 *
 * Data structure:
 * {
 *   drafts: [
 *     {
 *       id: "draft-123",
 *       type: "tax_correction" | "command" | "sales" | "service_desk",
 *       title: "Reclasificación de gasto",
 *       description: "Ajuste contable propuesto por el sistema",
 *       agent: "centinela",
 *       content: { ... },
 *       status: "pending" | "approved" | "rejected",
 *       created_at: "2026-06-22T10:30:00Z"
 *     }
 *   ]
 * }
 */

import React, { useState, useEffect } from 'react'
import { useAgentWebSocket } from '../hooks/useAgentWebSocket'

export interface Draft {
  id: string
  type: 'tax_correction' | 'command' | 'sales' | 'service_desk'
  title: string
  description: string
  agent: string
  content: Record<string, any>
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
}

interface ApprovalQueueProps {
  drafts?: Draft[]
  isLoading?: boolean
  error?: string | null
  onApprove?: (draftId: string) => Promise<void>
  onReject?: (draftId: string, reason?: string) => Promise<void>
}

const getDraftIcon = (type: string): string => {
  switch (type) {
    case 'tax_correction':
      return '💰'
    case 'command':
      return '⚙️'
    case 'sales':
      return '📊'
    case 'service_desk':
      return '🎫'
    default:
      return '📝'
  }
}

const getStatusBadge = (status: string): { color: string; label: string } => {
  switch (status) {
    case 'pending':
      return { color: 'bg-yellow-500/20 text-yellow-400', label: 'Pendiente' }
    case 'approved':
      return { color: 'bg-green-500/20 text-green-400', label: 'Aprobado' }
    case 'rejected':
      return { color: 'bg-red-500/20 text-red-400', label: 'Rechazado' }
    default:
      return { color: 'bg-gray-500/20 text-gray-400', label: 'Desconocido' }
  }
}

export const ApprovalQueue: React.FC<ApprovalQueueProps> = ({
  drafts: propsDrafts,
  isLoading: propsLoading,
  error: propsError,
  onApprove,
  onReject,
}) => {
  const { agentData, subscribe, invoke } = useAgentWebSocket()
  const [expandedDraft, setExpandedDraft] = useState<string | null>(null)
  const [approving, setApproving] = useState<Set<string>>(new Set())
  const [rejecting, setRejecting] = useState<Set<string>>(new Set())

  // Subscribe to approval queue agent on mount
  useEffect(() => {
    subscribe('approval')
  }, [subscribe])

  // Get data from hook or props (props take precedence for standalone mode)
  const agentOutput = agentData.approval
  const isHookLoading = agentOutput?.status === 'pending'
  const hookError = agentOutput?.status === 'error' ? agentOutput.error : null
  const hookDrafts = Array.isArray(agentOutput?.data) ? agentOutput.data : []

  // Use props if provided, otherwise use hook
  const drafts = propsDrafts || hookDrafts
  const isLoading = propsLoading ?? isHookLoading
  const error = propsError ?? hookError

  // Placeholder drafts
  const defaultDrafts: Draft[] = [
    {
      id: 'draft-1',
      type: 'tax_correction',
      title: 'Reclasificación de gasto operativo',
      description:
        'El sistema propone reclasificar $500.000 de "Gastos Operativos" a "Activos Diferidos" para el proyecto X',
      agent: 'centinela',
      content: {
        account_from: '5101',
        account_to: '1710',
        amount: 500000,
        currency: 'COP',
        reason: 'Project allocation - Project X phase 2',
      },
      status: 'pending',
      created_at: '2026-06-22T10:30:00Z',
    },
    {
      id: 'draft-2',
      type: 'command',
      title: 'Crear alerta de vencimiento',
      description: 'Crear alerta automática para IVA que vence en 3 días',
      agent: 'taty',
      content: {
        alert_type: 'iva',
        due_date: '2026-06-25',
        notification_channels: ['email', 'push'],
      },
      status: 'pending',
      created_at: '2026-06-22T09:15:00Z',
    },
  ]

  const displayDrafts = drafts.length > 0 ? drafts : defaultDrafts
  const isPlaceholder = drafts.length === 0
  const pendingCount = displayDrafts.filter((d) => d.status === 'pending').length

  const handleApprove = async (draftId: string) => {
    setApproving((prev) => new Set([...prev, draftId]))
    try {
      await invoke('approval', { draft_id: draftId, action: 'approve' })
      await onApprove?.(draftId)
    } finally {
      setApproving((prev) => {
        const next = new Set(prev)
        next.delete(draftId)
        return next
      })
    }
  }

  const handleReject = async (draftId: string) => {
    setRejecting((prev) => new Set([...prev, draftId]))
    try {
      await invoke('approval', { draft_id: draftId, action: 'reject', reason: 'Rechazado por el usuario' })
      await onReject?.(draftId, 'Rechazado por el usuario')
    } finally {
      setRejecting((prev) => {
        const next = new Set(prev)
        next.delete(draftId)
        return next
      })
    }
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <span>📋</span> Cola de Aprobación
          {pendingCount > 0 && (
            <span className="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
              {pendingCount}
            </span>
          )}
        </h3>
        {isLoading && <span className="text-xs text-gray-500">⏳ Cargando...</span>}
        {error && <span className="text-xs text-red-400">Error: {error}</span>}
      </div>

      {/* Drafts List */}
      <div className="space-y-3">
        {displayDrafts.length === 0 ? (
          <div className="bg-slate-900 border border-green-500/30 rounded-lg p-6 text-center">
            <p className="text-green-400">✅ No hay cambios pendientes de aprobación</p>
            <p className="text-xs text-gray-500 mt-2">Todos los cambios han sido procesados</p>
          </div>
        ) : (
          displayDrafts.map((draft) => {
            const statusBadge = getStatusBadge(draft.status)
            const isExpanded = expandedDraft === draft.id
            const isApproving = approving.has(draft.id)
            const isRejecting = rejecting.has(draft.id)

            return (
              <div key={draft.id} className="bg-slate-900 border border-gray-700 rounded-lg overflow-hidden">
                {/* Header (always visible) */}
                <button
                  onClick={() => setExpandedDraft(isExpanded ? null : draft.id)}
                  className="w-full p-4 flex items-start gap-3 hover:bg-slate-800 transition-colors text-left"
                  disabled={draft.status !== 'pending'}
                >
                  {/* Icon */}
                  <div className="text-2xl flex-shrink-0 mt-1">{getDraftIcon(draft.type)}</div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <h4 className="font-semibold text-white">{draft.title}</h4>
                        <p className="text-sm text-gray-400 mt-1">{draft.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-gray-500">Agente: {draft.agent}</span>
                          <span className={`text-xs px-2 py-1 rounded ${statusBadge.color}`}>
                            {statusBadge.label}
                          </span>
                        </div>
                      </div>

                      {/* Expand indicator */}
                      <div className={`text-2xl flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                        ▼
                      </div>
                    </div>
                  </div>
                </button>

                {/* Expanded content */}
                {isExpanded && draft.status === 'pending' && (
                  <div className="border-t border-gray-700 bg-slate-800/50 p-4 space-y-4">
                    {/* JSON content preview */}
                    <div>
                      <p className="text-xs text-gray-400 mb-2">Cambios propuestos:</p>
                      <pre className="bg-slate-900 p-3 rounded text-xs text-gray-300 overflow-x-auto">
                        {JSON.stringify(draft.content, null, 2)}
                      </pre>
                    </div>

                    {/* Action buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApprove(draft.id)}
                        disabled={isApproving || isRejecting}
                        className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white py-2 rounded font-medium transition-colors"
                      >
                        {isApproving ? '⏳ Aprobando...' : '✅ Aprobar'}
                      </button>
                      <button
                        onClick={() => handleReject(draft.id)}
                        disabled={isApproving || isRejecting}
                        className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white py-2 rounded font-medium transition-colors"
                      >
                        {isRejecting ? '⏳ Rechazando...' : '❌ Rechazar'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Data freshness indicator */}
      {isPlaceholder && (
        <div className="text-center text-xs text-gray-500 bg-slate-900/50 py-2 rounded">
          📡 Datos de ejemplo (conectando con Hermes...)
        </div>
      )}
    </div>
  )
}
