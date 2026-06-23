/**
 * PulsaCard Component
 * Displays real-time financial pulse: "Hoy en tu negocio"
 * Updates via Hermes Pulso agent via WebSocket
 *
 * Data structure from agent:
 * {
 *   caja_real: 42850000,
 *   dinero_tuyo: 38500000,
 *   ventas_ayer: 1250000,
 *   salidas_plata: 345000,
 *   estado_plata: "bien" | "alerta" | "critico"
 * }
 */

import React, { useEffect } from 'react'
import { useAgentWebSocket } from '../hooks/useAgentWebSocket'

interface PulsaData {
  caja_real: number
  dinero_tuyo: number
  ventas_ayer: number
  salidas_plata: number
  estado_plata: 'bien' | 'alerta' | 'critico'
}

interface PulsaCardProps {
  data?: PulsaData
  isLoading?: boolean
  error?: string | null
}

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

const getStatusIcon = (estado: string): string => {
  switch (estado) {
    case 'bien':
      return '✅'
    case 'alerta':
      return '⚠️'
    case 'critico':
      return '🔴'
    default:
      return '❓'
  }
}

const getStatusColor = (estado: string): string => {
  switch (estado) {
    case 'bien':
      return 'text-green-500'
    case 'alerta':
      return 'text-yellow-500'
    case 'critico':
      return 'text-red-500'
    default:
      return 'text-gray-500'
  }
}

export const PulsaCard: React.FC<PulsaCardProps> = ({ data: propsData, isLoading: propsLoading, error: propsError }) => {
  const { agentData, subscribe } = useAgentWebSocket()

  // Subscribe to pulso agent on mount
  useEffect(() => {
    subscribe('pulso')
  }, [subscribe])

  // Get data from hook or props (props take precedence for standalone mode)
  const agentOutput = agentData.pulso
  const isHookLoading = agentOutput?.status === 'pending'
  const hookError = agentOutput?.status === 'error' ? agentOutput.error : null

  // Use props if provided (standalone mode), otherwise use hook (connected mode)
  const data = propsData || agentOutput?.data
  const isLoading = propsLoading ?? isHookLoading
  const error = propsError ?? hookError

  // Placeholder data when no real data available
  const defaultData: PulsaData = {
    caja_real: 42850000,
    dinero_tuyo: 38500000,
    ventas_ayer: 1250000,
    salidas_plata: 345000,
    estado_plata: 'bien',
  }

  const displayData = data || defaultData
  const isPlaceholder = !data

  return (
    <div className="space-y-4">
      {/* Header: Hoy en tu negocio */}
      <div className="bg-slate-900 border border-purple-500/30 rounded-lg p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-white mb-1">Hoy en tu negocio</h2>
            <p className="text-sm text-gray-400">
              {isLoading ? '⏳ Cargando...' : 'Tu plata está sana, pero bajó un poco por una cuota del banco. Nada grave, sigue tranqui 💪'}
            </p>
          </div>
          {error && (
            <div className="text-red-400 text-sm bg-red-500/10 px-3 py-1 rounded">
              Error: {error}
            </div>
          )}
        </div>

        {/* Caja Real de Hoy */}
        <div className="space-y-2">
          <p className="text-sm text-gray-400">Caja Real de Hoy</p>
          <div className="text-4xl font-bold text-cyan-400">
            {formatCurrency(displayData.caja_real)}
          </div>
          <p className="text-xs text-gray-500">
            Dinero tuyo de verdad: {formatCurrency(displayData.dinero_tuyo)}
          </p>
        </div>
      </div>

      {/* Row: Ventas y Salidas */}
      <div className="grid grid-cols-2 gap-4">
        {/* Ventas de ayer */}
        <div className="bg-slate-900 border border-gray-700 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-2">Ventas de ayer:</p>
          <p className="text-2xl font-bold text-white">
            {formatCurrency(displayData.ventas_ayer)}
          </p>
        </div>

        {/* Salidas de plata */}
        <div className="bg-slate-900 border border-gray-700 rounded-lg p-4">
          <p className="text-xs text-gray-400 mb-2">Salidas de plata:</p>
          <p className="text-2xl font-bold text-white">
            {formatCurrency(displayData.salidas_plata)}
          </p>
        </div>
      </div>

      {/* Call-to-action: "Ver de dónde viene tu plata" */}
      <button className="w-full bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/50 text-cyan-400 py-3 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
        <span>Ver de dónde viene tu plata</span>
        <span>→</span>
      </button>

      {/* Status Metrics Row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Plata disponible */}
        <div className="bg-slate-900 border border-gray-700 rounded-lg p-4 text-center">
          <div className="text-xl mb-1">💧</div>
          <p className="text-xs text-gray-400 mb-2">PLATA DISPONIBLE</p>
          <p className={`text-sm font-semibold ${getStatusColor(displayData.estado_plata)}`}>
            {getStatusIcon(displayData.estado_plata)} Bien
          </p>
        </div>

        {/* Tu ganancia */}
        <div className="bg-slate-900 border border-gray-700 rounded-lg p-4 text-center">
          <div className="text-xl mb-1">📈</div>
          <p className="text-xs text-gray-400 mb-2">TU GANANCIA</p>
          <p className="text-sm font-semibold text-green-400">Bien</p>
        </div>
      </div>

      {/* Lo que debes + Aprovecha tu plata */}
      <div className="grid grid-cols-2 gap-4">
        {/* Lo que debes */}
        <div className="bg-slate-900 border border-gray-700 rounded-lg p-4 text-center">
          <div className="text-xl mb-1">💳</div>
          <p className="text-xs text-gray-400 mb-2">LO QUE DEBES</p>
          <p className="text-sm font-semibold text-yellow-500">Ojo</p>
        </div>

        {/* Aprovechas tu plata */}
        <div className="bg-slate-900 border border-gray-700 rounded-lg p-4 text-center cursor-pointer hover:bg-slate-800 transition-colors">
          <div className="text-xl mb-1">⚡</div>
          <p className="text-xs text-gray-400 mb-2">APROVECHAS TU PLATA</p>
          <p className="text-sm font-semibold text-green-400">
            Bien
            <span className="ml-1">→</span>
          </p>
        </div>
      </div>

      {/* Data freshness indicator */}
      {isPlaceholder && (
        <div className="text-center text-xs text-gray-500 bg-slate-900/50 py-2 rounded">
          📊 Datos de ejemplo (conectando con Hermes...)
        </div>
      )}
    </div>
  )
}
