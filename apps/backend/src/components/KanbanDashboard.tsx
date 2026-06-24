/**
 * Kanban Dashboard (T11.7)
 *
 * Visualizes Hermes missions in a 4-column Kanban board:
 * PENDING → EXECUTING → CHECKPOINTS → COMPLETED
 *
 * Shows:
 * - Missions and tasks in appropriate columns
 * - Checkpoint status (✅ success, ⏳ pending, ❌ failed)
 * - Cost tracking per mission
 * - Progress and metrics
 */

import React, { useState, useEffect } from "react";

// Types
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

interface KanbanDashboardProps {
  missions: Mission[];
  metrics?: DashboardMetrics;
  onMissionClick?: (mission: Mission) => void;
  onTaskClick?: (task: Task) => void;
  isLoading?: boolean;
}

// Column Components
const KanbanColumn: React.FC<{
  title: string;
  count: number;
  children: React.ReactNode;
  className?: string;
}> = ({ title, count, children, className = "" }) => (
  <div className={`kanban-column ${className}`}>
    <div className="column-header">
      <h3>{title}</h3>
      <span className="count">{count}</span>
    </div>
    <div className="column-content">{children}</div>
  </div>
);

const MissionCard: React.FC<{
  mission: Mission;
  onClick?: (m: Mission) => void;
}> = ({ mission, onClick }) => (
  <div className="mission-card" onClick={() => onClick?.(mission)}>
    <div className="card-header">
      <h4>{mission.id}</h4>
      <span className={`status status-${mission.status}`}>{mission.status}</span>
    </div>
    <div className="card-body">
      <p className="objective">{mission.objective}</p>
      <div className="task-count">{mission.tasks.length} tasks</div>
      {mission.cost > 0 && <div className="cost">${mission.cost.toFixed(4)}</div>}
      {mission.progress > 0 && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${mission.progress}%` }} />
        </div>
      )}
    </div>
  </div>
);

const TaskCard: React.FC<{
  task: Task;
  onClick?: (t: Task) => void;
}> = ({ task, onClick }) => (
  <div className="task-card" onClick={() => onClick?.(task)}>
    <div className="task-header">
      <h5>{task.type}</h5>
      <span className={`status-badge status-${task.status}`}>{task.status}</span>
    </div>
    <div className="task-body">
      <p className="operator">{task.operator}</p>
    </div>
  </div>
);

const CheckpointCard: React.FC<{
  checkpoint: Checkpoint;
}> = ({ checkpoint }) => (
  <div className="checkpoint-card">
    <div className="checkpoint-header">
      <span className="status">{checkpoint.status}</span>
      <span className="task-type">{checkpoint.task_type}</span>
    </div>
    <div className="checkpoint-body">
      <p className="duration">{checkpoint.duration_ms}ms</p>
      <p className="cost">${checkpoint.cost.toFixed(4)}</p>
    </div>
  </div>
);

// Metrics Panel
const MetricsPanel: React.FC<{ metrics: DashboardMetrics }> = ({ metrics }) => (
  <div className="metrics-panel">
    <div className="metric-card">
      <div className="metric-value">{metrics.total_missions}</div>
      <div className="metric-label">Total Missions</div>
    </div>
    <div className="metric-card">
      <div className="metric-value">{metrics.active_missions}</div>
      <div className="metric-label">Active Now</div>
    </div>
    <div className="metric-card">
      <div className="metric-value">{metrics.completed_today}</div>
      <div className="metric-label">Completed Today</div>
    </div>
    <div className="metric-card">
      <div className="metric-value">${metrics.total_cost.toFixed(2)}</div>
      <div className="metric-label">Total Cost</div>
    </div>
    <div className="metric-card">
      <div className="metric-value">{metrics.avg_duration_minutes.toFixed(1)}m</div>
      <div className="metric-label">Avg Duration</div>
    </div>
    <div className="metric-card">
      <div className="metric-value">{metrics.success_rate.toFixed(0)}%</div>
      <div className="metric-label">Success Rate</div>
    </div>
  </div>
);

// Main Component
export const KanbanDashboard: React.FC<KanbanDashboardProps> = ({
  missions,
  metrics,
  onMissionClick,
  onTaskClick,
  isLoading = false,
}) => {
  // Compute column data
  const pending = missions.filter((m) => m.status === "pending");
  const executing = missions.filter((m) => m.status === "executing");
  const checkpoints = missions.flatMap((m) => m.checkpoints);
  const completed = missions.filter((m) => m.status === "completed");

  if (isLoading) {
    return <div className="kanban-dashboard loading">Loading...</div>;
  }

  return (
    <div className="kanban-dashboard">
      {metrics && <MetricsPanel metrics={metrics} />}

      <div className="kanban-board">
        {/* PENDING Column */}
        <KanbanColumn title="PENDING" count={pending.length} className="pending">
          {pending.map((mission) => (
            <MissionCard
              key={mission.id}
              mission={mission}
              onClick={onMissionClick}
            />
          ))}
        </KanbanColumn>

        {/* EXECUTING Column */}
        <KanbanColumn
          title="EXECUTING"
          count={executing.length}
          className="executing"
        >
          {executing.map((mission) => (
            <div key={mission.id}>
              <MissionCard mission={mission} onClick={onMissionClick} />
              <div className="subtasks">
                {mission.tasks
                  .filter((t) => t.status === "executing")
                  .map((task) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      onClick={onTaskClick}
                    />
                  ))}
              </div>
            </div>
          ))}
        </KanbanColumn>

        {/* CHECKPOINTS Column */}
        <KanbanColumn
          title="CHECKPOINTS"
          count={checkpoints.length}
          className="checkpoints"
        >
          {checkpoints.map((checkpoint, idx) => (
            <CheckpointCard key={idx} checkpoint={checkpoint} />
          ))}
        </KanbanColumn>

        {/* COMPLETED Column */}
        <KanbanColumn title="COMPLETED" count={completed.length} className="completed">
          {completed.map((mission) => (
            <MissionCard
              key={mission.id}
              mission={mission}
              onClick={onMissionClick}
            />
          ))}
        </KanbanColumn>
      </div>
    </div>
  );
};

// Default export
export default KanbanDashboard;
