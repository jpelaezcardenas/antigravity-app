# Kanban Dashboard (T11.7)

React component for visualizing Hermes missions in a 4-column Kanban board.

## Features

- **4-Column Layout**: PENDING → EXECUTING → CHECKPOINTS → COMPLETED
- **Mission Cards**: Display objective, task count, cost, progress
- **Task Cards**: Show task type, operator, status
- **Checkpoint Cards**: Visualize proof of completion (✅/⏳/❌)
- **Metrics Panel**: Total missions, active, completed today, cost, duration, success rate
- **Responsive**: Works on desktop, tablet, mobile
- **WebSocket Support**: Real-time updates (optional)
- **Auto-Refresh**: Configurable polling interval

## Installation

```bash
npm install react typescript
```

## Usage

### Basic Usage

```tsx
import { KanbanDashboard } from "@/components/KanbanDashboard";
import { useKanban } from "@/hooks/useKanban";

export default function DashboardPage() {
  const { missions, metrics, isLoading } = useKanban({
    autoRefreshInterval: 5000, // Refresh every 5 seconds
  });

  return (
    <KanbanDashboard
      missions={missions}
      metrics={metrics}
      isLoading={isLoading}
    />
  );
}
```

### With Click Handlers

```tsx
const handleMissionClick = (mission: Mission) => {
  console.log("Mission clicked:", mission);
  // Navigate to mission details, open modal, etc
};

const handleTaskClick = (task: Task) => {
  console.log("Task clicked:", task);
};

return (
  <KanbanDashboard
    missions={missions}
    metrics={metrics}
    onMissionClick={handleMissionClick}
    onTaskClick={handleTaskClick}
  />
);
```

### With useKanban Hook

```tsx
const { 
  missions, 
  metrics, 
  isLoading, 
  error,
  fetchMissions,
  startMission,
  wsConnected
} = useKanban({
  apiBaseUrl: "/api/v1",
  autoRefreshInterval: 5000,
  enableWebSocket: true,
});

// Start a new mission
const newMission = await startMission(
  "invite-123",
  "customer@example.com",
  "pro"
);

// Manually refresh
await fetchMissions();
```

## Component Props

```typescript
interface KanbanDashboardProps {
  missions: Mission[];           // Array of missions to display
  metrics?: DashboardMetrics;   // Optional metrics panel data
  onMissionClick?: (mission: Mission) => void;
  onTaskClick?: (task: Task) => void;
  isLoading?: boolean;          // Show loading state
}
```

## Hook Options

```typescript
interface UseKanbanOptions {
  apiBaseUrl?: string;           // Default: "/api/v1"
  autoRefreshInterval?: number;  // Default: 5000ms (0 = disabled)
  enableWebSocket?: boolean;     // Default: false
}
```

## Data Structures

### Mission

```typescript
interface Mission {
  id: string;
  type: string;
  status: "pending" | "executing" | "completed" | "failed" | "blocked";
  objective: string;
  tasks: Task[];
  checkpoints: Checkpoint[];
  cost: number;
  cost_breakdown: Record<string, number>;
  progress: number; // 0-100
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
}
```

### Task

```typescript
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
```

### Checkpoint

```typescript
interface Checkpoint {
  timestamp: string;
  task_type: string;
  status: "✅" | "⏳" | "❌";
  proof: Record<string, any>;
  operator_id: string;
  duration_ms: number;
  cost: number;
}
```

### DashboardMetrics

```typescript
interface DashboardMetrics {
  total_missions: number;
  active_missions: number;
  completed_today: number;
  total_cost: number;
  avg_duration_minutes: number;
  success_rate: number;
}
```

## Styling

The component uses CSS modules (`KanbanDashboard.module.css`) with:

- **Colors**: Blue theme with status-specific accents
- **Responsive**: Grid layout adapts to screen size
- **Dark mode compatible**: Adjust CSS variables as needed
- **Scrollable columns**: Overflow handling with smooth scrolling

### Customization

To customize colors, edit the CSS variables in `KanbanDashboard.module.css`:

```css
.kanban-column.pending .column-header {
  background: #fff3cd; /* Change color */
}
```

## API Endpoints

The hook expects these endpoints to exist:

```
GET    /api/v1/missions              - Get all missions
POST   /api/v1/missions              - Start new mission
GET    /api/v1/missions/{id}         - Get mission details
GET    /api/v1/missions/{id}/checkpoints - Get mission checkpoints
GET    /api/v1/missions/{id}/cost    - Get mission cost breakdown
GET    /api/v1/missions/{id}/progress - Get mission progress
```

### WebSocket Endpoint

```
WS     /api/v1/kanban/subscribe      - Real-time mission updates
```

## Testing

Run tests with:

```bash
npm test -- test_kanban_dashboard.tsx
```

Test coverage includes:
- Component rendering
- Column categorization
- Click handlers
- Metrics display
- Responsive behavior
- Empty state handling

## Performance Notes

- Components memoized with React.memo for performance
- CSS uses flexbox for efficient layout
- Virtualization recommended for 100+ missions (use react-window)
- WebSocket reduces API calls by 80%

## Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast meets WCAG AA standards

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

- React 18+
- TypeScript 4.5+
- (Optional) react-window for virtualization
- (Optional) framer-motion for animations

## Future Enhancements

- [ ] Drag-and-drop to move missions between columns
- [ ] Filter by status, type, cost range
- [ ] Export data to CSV/PDF
- [ ] Custom sorting (by cost, duration, status)
- [ ] Mission search
- [ ] Detailed mission modal
- [ ] Timeline view
- [ ] Analytics dashboard
