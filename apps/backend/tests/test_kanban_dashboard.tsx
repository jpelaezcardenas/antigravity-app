/**
 * Tests for KanbanDashboard component (T11.7)
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { KanbanDashboard } from "../src/components/KanbanDashboard";

// Mock data
const mockMissions = [
  {
    id: "mission-001",
    type: "customer_registration",
    status: "pending" as const,
    objective: "Register customer@example.com (starter plan)",
    tasks: [
      {
        id: "task-001",
        type: "create_auth_user",
        operator: "auth_operator",
        payload: { email: "customer@example.com" },
        status: "assigned" as const,
        created_at: "2026-06-23T20:00:00Z",
      },
    ],
    checkpoints: [],
    cost: 0,
    cost_breakdown: {},
    progress: 0,
    created_at: "2026-06-23T20:00:00Z",
  },
  {
    id: "mission-002",
    type: "customer_registration",
    status: "executing" as const,
    objective: "Register newcustomer@example.com (pro plan)",
    tasks: [
      {
        id: "task-002",
        type: "create_auth_user",
        operator: "auth_operator",
        payload: { email: "newcustomer@example.com" },
        status: "executing" as const,
        created_at: "2026-06-23T19:50:00Z",
        started_at: "2026-06-23T19:55:00Z",
      },
      {
        id: "task-003",
        type: "create_tenant",
        operator: "db_operator",
        payload: { customer_email: "newcustomer@example.com", plan: "pro" },
        status: "queued" as const,
        created_at: "2026-06-23T19:50:00Z",
      },
    ],
    checkpoints: [
      {
        timestamp: "2026-06-23T19:56:00Z",
        task_type: "auth_operator",
        status: "✅" as const,
        proof: { user_id: "uuid-123" },
        operator_id: "auth_operator",
        duration_ms: 120,
        cost: 0.001,
      },
    ],
    cost: 0.003,
    cost_breakdown: { auth_operator: 0.001, db_operator: 0.002 },
    progress: 50,
    created_at: "2026-06-23T19:50:00Z",
    started_at: "2026-06-23T19:55:00Z",
  },
  {
    id: "mission-003",
    type: "customer_registration",
    status: "completed" as const,
    objective: "Register completed@example.com (enterprise plan)",
    tasks: [
      {
        id: "task-004",
        type: "create_auth_user",
        operator: "auth_operator",
        payload: { email: "completed@example.com" },
        status: "completed" as const,
        created_at: "2026-06-23T18:00:00Z",
        started_at: "2026-06-23T18:05:00Z",
        completed_at: "2026-06-23T18:06:00Z",
      },
    ],
    checkpoints: [
      {
        timestamp: "2026-06-23T18:06:00Z",
        task_type: "auth_operator",
        status: "✅" as const,
        proof: { user_id: "uuid-456" },
        operator_id: "auth_operator",
        duration_ms: 100,
        cost: 0.001,
      },
    ],
    cost: 0.047,
    cost_breakdown: { auth_operator: 0.001, db_operator: 0.002, comms_operator: 0.01 },
    progress: 100,
    created_at: "2026-06-23T18:00:00Z",
    started_at: "2026-06-23T18:05:00Z",
    completed_at: "2026-06-23T18:20:00Z",
    duration_seconds: 900,
  },
];

const mockMetrics = {
  total_missions: 3,
  active_missions: 1,
  completed_today: 1,
  total_cost: 0.05,
  avg_duration_minutes: 15,
  success_rate: 66.7,
};

describe("KanbanDashboard", () => {
  test("renders without crashing", () => {
    render(<KanbanDashboard missions={[]} />);
    expect(screen.getByText(/pending/i)).toBeInTheDocument();
  });

  test("displays loading state", () => {
    render(<KanbanDashboard missions={[]} isLoading={true} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  test("renders metrics panel when provided", () => {
    render(<KanbanDashboard missions={mockMissions} metrics={mockMetrics} />);

    expect(screen.getByText("3")).toBeInTheDocument(); // Total missions
    expect(screen.getByText("1")).toBeInTheDocument(); // Active missions
    expect(screen.getByText(/Total Missions/i)).toBeInTheDocument();
  });

  test("displays all four columns", () => {
    render(<KanbanDashboard missions={mockMissions} />);

    expect(screen.getByText(/pending/i)).toBeInTheDocument();
    expect(screen.getByText(/executing/i)).toBeInTheDocument();
    expect(screen.getByText(/checkpoints/i)).toBeInTheDocument();
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });

  test("categorizes missions into correct columns", () => {
    render(<KanbanDashboard missions={mockMissions} />);

    // Find the mission cards by their objectives
    const pendingMission = screen.getByText(/starter plan/i);
    const executingMission = screen.getByText(/pro plan/i);
    const completedMission = screen.getByText(/enterprise plan/i);

    expect(pendingMission).toBeInTheDocument();
    expect(executingMission).toBeInTheDocument();
    expect(completedMission).toBeInTheDocument();
  });

  test("displays task count on mission cards", () => {
    render(<KanbanDashboard missions={mockMissions} />);

    expect(screen.getByText("1 tasks")).toBeInTheDocument();
    expect(screen.getByText("2 tasks")).toBeInTheDocument();
  });

  test("displays cost on mission cards", () => {
    render(<KanbanDashboard missions={mockMissions} />);

    expect(screen.getByText(/\$0\.047/)).toBeInTheDocument();
  });

  test("displays progress bar for executing missions", () => {
    const { container } = render(
      <KanbanDashboard missions={[mockMissions[1]]} />
    );

    const progressFill = container.querySelector(".progress-fill");
    expect(progressFill).toHaveStyle({ width: "50%" });
  });

  test("calls onMissionClick when mission card is clicked", () => {
    const onMissionClick = jest.fn();
    render(
      <KanbanDashboard missions={mockMissions} onMissionClick={onMissionClick} />
    );

    const missionCard = screen.getByText(/starter plan/i).closest(".mission-card");
    fireEvent.click(missionCard!);

    expect(onMissionClick).toHaveBeenCalledWith(mockMissions[0]);
  });

  test("calls onTaskClick when task card is clicked", () => {
    const onTaskClick = jest.fn();
    render(
      <KanbanDashboard missions={mockMissions} onTaskClick={onTaskClick} />
    );

    const taskCards = screen.getAllByText("create_auth_user");
    if (taskCards.length > 0) {
      fireEvent.click(taskCards[0]);
      expect(onTaskClick).toHaveBeenCalled();
    }
  });

  test("displays checkpoints correctly", () => {
    render(<KanbanDashboard missions={[mockMissions[1], mockMissions[2]]} />);

    const checkpointStatuses = screen.getAllByText("✅");
    expect(checkpointStatuses.length).toBeGreaterThan(0);
  });

  test("handles empty missions array", () => {
    render(<KanbanDashboard missions={[]} />);

    expect(screen.getByText(/pending/i)).toBeInTheDocument();
    expect(screen.queryByText(/mission-/)).not.toBeInTheDocument();
  });

  test("responsive grid layout", () => {
    const { container } = render(<KanbanDashboard missions={mockMissions} />);

    const board = container.querySelector(".kanban-board");
    expect(board).toHaveClass("kanban-board");
  });
});
