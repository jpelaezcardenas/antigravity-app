/**
 * useKanban Hook (T11.7)
 *
 * Manages Kanban dashboard state:
 * - Fetches missions from API
 * - Computes metrics
 * - Handles WebSocket updates
 * - Auto-refresh
 */

import { useState, useEffect, useCallback } from "react";

interface Checkpoint {
  timestamp: string;
  task_type: string;
  status: "✅" | "⏳" | "❌";
  proof: Record<string, any>;
  operator_id: string;
  duration_ms: number;
  cost: number;
}

interface Task {
  id: string;
  type: string;
  operator: string;
  payload: Record<string, any>;
  status: "assigned" | "queued" | "executing" | "completed" | "failed" | "blocked" | "timed_out";
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

interface Mission {
  id: string;
  type: string;
  status: "pending" | "executing" | "completed" | "failed" | "blocked";
  objective: string;
  tasks: Task[];
  checkpoints: Checkpoint[];
  cost: number;
  cost_breakdown: Record<string, number>;
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
}

interface DashboardMetrics {
  total_missions: number;
  active_missions: number;
  completed_today: number;
  total_cost: number;
  avg_duration_minutes: number;
  success_rate: number;
}

interface UseKanbanOptions {
  apiBaseUrl?: string;
  autoRefreshInterval?: number; // ms, 0 = disabled
  enableWebSocket?: boolean;
}

/**
 * Compute metrics from missions array
 */
const computeMetrics = (missions: Mission[]): DashboardMetrics => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const completedToday = missions.filter((m) => {
    if (m.status !== "completed" || !m.completed_at) return false;
    const completed = new Date(m.completed_at);
    completed.setHours(0, 0, 0, 0);
    return completed.getTime() === today.getTime();
  }).length;

  const totalCost = missions.reduce((sum, m) => sum + m.cost, 0);
  const completedMissions = missions.filter((m) => m.status === "completed");
  const avgDuration =
    completedMissions.length > 0
      ? completedMissions.reduce((sum, m) => sum + (m.duration_seconds || 0), 0) /
        completedMissions.length /
        60 // Convert to minutes
      : 0;

  const successRate =
    missions.length > 0
      ? (completedMissions.length / missions.length) * 100
      : 0;

  return {
    total_missions: missions.length,
    active_missions: missions.filter((m) => m.status === "executing").length,
    completed_today: completedToday,
    total_cost: totalCost,
    avg_duration_minutes: avgDuration,
    success_rate: successRate,
  };
};

/**
 * useKanban Hook
 */
export const useKanban = (options: UseKanbanOptions = {}) => {
  const {
    apiBaseUrl = "/api/v1",
    autoRefreshInterval = 5000, // 5 seconds default
    enableWebSocket = false,
  } = options;

  const [missions, setMissions] = useState<Mission[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    total_missions: 0,
    active_missions: 0,
    completed_today: 0,
    total_cost: 0,
    avg_duration_minutes: 0,
    success_rate: 0,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  /**
   * Fetch missions from API
   */
  const fetchMissions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${apiBaseUrl}/missions`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: Mission[] = await response.json();
      setMissions(data);
      setMetrics(computeMetrics(data));
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch missions";
      setError(message);
      console.error("useKanban: fetch error", message);
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl]);

  /**
   * Setup WebSocket for real-time updates (optional)
   */
  useEffect(() => {
    if (!enableWebSocket) return;

    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}${apiBaseUrl}/kanban/subscribe`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
        console.log("useKanban: WebSocket connected");
      };

      ws.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
          if (update.type === "mission_update") {
            fetchMissions();
          }
        } catch (err) {
          console.error("useKanban: WebSocket parse error", err);
        }
      };

      ws.onerror = (err) => {
        console.error("useKanban: WebSocket error", err);
        setWsConnected(false);
      };

      ws.onclose = () => {
        setWsConnected(false);
        console.log("useKanban: WebSocket closed");
      };

      return () => {
        ws.close();
      };
    } catch (err) {
      console.error("useKanban: WebSocket setup error", err);
    }
  }, [enableWebSocket, apiBaseUrl, fetchMissions]);

  /**
   * Setup auto-refresh interval
   */
  useEffect(() => {
    if (autoRefreshInterval <= 0) return;

    const interval = setInterval(() => {
      fetchMissions();
    }, autoRefreshInterval);

    return () => clearInterval(interval);
  }, [autoRefreshInterval, fetchMissions]);

  /**
   * Initial fetch
   */
  useEffect(() => {
    fetchMissions();
  }, [fetchMissions]);

  /**
   * Manually trigger mission start
   */
  const startMission = useCallback(
    async (
      inviteId: string,
      customerEmail: string,
      plan: string
    ): Promise<Mission | null> => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch(`${apiBaseUrl}/missions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ invite_id: inviteId, customer_email: customerEmail, plan }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const newMission: Mission = await response.json();
        setMissions([...missions, newMission]);
        setMetrics(computeMetrics([...missions, newMission]));
        return newMission;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to start mission";
        setError(message);
        console.error("useKanban: startMission error", message);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [apiBaseUrl, missions]
  );

  return {
    missions,
    metrics,
    isLoading,
    error,
    wsConnected,
    fetchMissions,
    startMission,
  };
};

export default useKanban;
