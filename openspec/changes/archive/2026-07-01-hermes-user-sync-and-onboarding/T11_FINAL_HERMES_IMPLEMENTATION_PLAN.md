# T11: Final Hermes Operators Implementation Plan

**Date:** 2026-06-25  
**Status:** Ready to Execute  
**Duration:** 21 hours (Jun 26-27)  
**Architecture:** Fully aligned with real Hermes (Missions + Swarms + Kanban + Dispatcher)

---

## ✅ HERMES ARCHITECTURE (COMPLETE UNDERSTANDING)

### Multi-Layer Structure

```
PROFILES (Agent Personas)
├─ builder (Worker ID: builder)
├─ centinela (Worker ID: centinela)
├─ writer, admin, coder, researcher, [N more...]
└─ Each profile has own memory + missions + checkpoints

GATEWAYS (One per Profile)
├─ Default gateway (dispatch_in_gateway: true)
│  └─ Owns kanban dispatcher + notifier watcher
├─ Other gateways (dispatch_in_gateway: false)
│  └─ Deliver messages only (no kanban writes)
└─ All gateways deliver messages for platform APIs (Telegram, Discord, etc)

KANBAN SYSTEM (Per-board)
├─ Kanban board (SQLite-based per profile)
├─ Tasks (work items with state machine)
├─ Subscriptions (users subscribe to terminal events)
├─ Notifier (watches for completed/blocked/crashed/timed_out)
├─ Dispatcher (auto-decomposes tasks into subtasks)
└─ Watcher (background loops polling every 5 seconds)

MISSIONS (Coordinated work units)
├─ mission-mqo426sc-ehjqe7 (example)
├─ Status: executing
├─ Checkpoints: proof of each step
├─ Tasks: dispatched to swarm operators
└─ Results: collected by conductor
```

### Terminal Task States (Kanban)

```
Task Lifecycle:
assigned → queued → executing → [terminal states]

Terminal States:
✅ completed     (task finished successfully)
✅ archived      (completed + archived)
⏸️ blocked       (blocked by dependency)
❌ crashed       (error during execution)
❌ gave_up       (retries exceeded)
❌ timed_out     (exceeded timeout)

Notifier watches for: completed, blocked, gave_up, crashed, timed_out
Then sends notifications to users (platform adapters: Telegram, Discord, etc)
```

---

## 🎯 T11 IMPLEMENTATION: CONDUCTOR-BASED CUSTOMER ONBOARDING

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXIA CONDUCTOR                       │
│  (Orchestrates customer onboarding as Hermes Mission)       │
└──────────────┬────────────────────────────────────┬─────────┘
               │                                    │
         ┌─────▼────────┐                  ┌───────▼────────┐
         │   MISSION    │                  │   KANBAN DB    │
         ├──────────────┤                  ├────────────────┤
         │ mission-xxxx │                  │ kanban.db      │
         │ Status:      │                  │ (SQLite)       │
         │  executing   │                  │                │
         │              │                  │ Tables:        │
         │ Tasks: 5     │                  │ ├─ tasks       │
         │ Cost: $0.017 │                  │ ├─ task_events │
         │ Progress:    │                  │ ├─ subscriptions
         │  100%        │                  │ └─ [more...]   │
         └──────────────┘                  └────────────────┘
               │
         ┌─────┴──────────────────────────────────┬──────────┐
         │                                        │          │
    ┌────▼─────┐  ┌──────────┐  ┌──────────┐ ┌──▼──────┐ ┌▼────────┐
    │   AUTH   │  │    DB    │  │  ROLES   │ │ COMMS   │ │WORKFLOW │
    │ OPERATOR │  │ OPERATOR │  │OPERATOR  │ │OPERATOR │ │ TRACKER │
    │          │  │          │  │          │ │         │ │         │
    │ Task 1   │  │ Task 2   │  │ Task 3   │ │ Task 4  │ │ Logging │
    │ Create   │  │ Create   │  │ Assign   │ │ Send    │ │ State   │
    │ Auth     │  │ Tenant   │  │ Admin    │ │ Email   │ │ Mgmt    │
    │ User     │  │ + Users  │  │ Role     │ │         │ │         │
    │          │  │          │  │          │ │         │ │         │
    │ Return:  │  │ Return:  │  │ Return:  │ │ Return: │ │         │
    │ user_id  │  │ tenant_id│  │ confirmed│ │ status  │ │         │
    └────┬─────┘  └────┬─────┘  └────┬─────┘ └────┬────┘ └────┬────┘
         │             │             │            │          │
         └─────────────┴─────────────┴────────────┴──────────┘
                       │
                  ┌────▼─────────┐
                  │  CHECKPOINTS  │
                  │ (Proof Array) │
                  ├───────────────┤
                  │ ✅ Auth user  │
                  │ ✅ Tenant     │
                  │ ✅ Role       │
                  │ ✅ Email      │
                  │ ✅ Workflow   │
                  └───────────────┘
```

### Core Components

#### 1. Conductor Class (T11.1)
```python
class OnboardingConductor:
    """
    Orchestrates customer onboarding as a Hermes Mission.
    
    Responsible for:
    - Creating mission
    - Dispatching tasks to swarm operators (parallel)
    - Collecting checkpoints (proof)
    - Tracking cost + progress
    - Managing mission state
    """
    
    async def conduct_customer_onboarding(
        self,
        invite_id: str,
        customer_email: str,
        plan: str
    ) -> Mission:
        """
        Main orchestration method.
        
        Returns Mission with:
        - Status: executing → completed
        - Tasks: 5 (auth, db, roles, comms, workflow)
        - Checkpoints: proof of each step
        - Cost: $0.017 (example)
        - Progress: 0% → 100%
        """
        # 1. Create mission
        mission = self.create_mission(
            type="customer_registration",
            customer_email=customer_email,
            objective=f"Register {customer_email} ({plan} plan)"
        )
        
        # 2. Dispatch 5 tasks to swarm (parallel execution)
        task1 = await self.dispatch_task(
            mission=mission,
            task_type="create_auth_user",
            operator="auth_operator",
            payload={...}
        )
        task2 = await self.dispatch_task(
            mission=mission,
            task_type="create_tenant",
            operator="db_operator",
            payload={...}
        )
        # ... tasks 3, 4, 5
        
        # 3. Wait for all tasks (asyncio.gather)
        results = await asyncio.gather(task1, task2, task3, task4, task5)
        
        # 4. Record checkpoints
        for task in results:
            mission.add_checkpoint(
                task_type=task.type,
                proof=task.result,
                status="✅" if task.success else "❌",
                duration_ms=task.duration_ms
            )
        
        # 5. Calculate cost
        mission.cost = sum(r.cost for r in results)
        mission.progress = 100
        mission.status = "completed"
        
        # 6. Return mission for Kanban + Dashboard
        return mission
```

#### 2-5. Swarm Operators (T11.2-T11.5)

Each operator is a **profile-like agent** that:
- Receives a Task
- Executes work
- Returns TaskResult with proof
- Publishes events to kanban board

```python
class AuthOperator(SwarmOperator):
    """Creates Supabase auth user"""
    
    async def execute(self, task: Task) -> TaskResult:
        # Do work
        user = await create_supabase_user(...)
        
        # Return proof
        return TaskResult(
            task_id=task.id,
            operator="auth_operator",
            success=True,
            proof={"user_id": str(user.id)},
            cost=0.001,
            duration_ms=150
        )

class DBOperator(SwarmOperator):
    """Creates tenant + user records"""
    # Similar pattern

class RolesOperator(SwarmOperator):
    """Assigns roles to users"""
    # Similar pattern

class CommsOperator(SwarmOperator):
    """Sends welcome emails"""
    # Similar pattern

class WorkflowTrackerOperator(SwarmOperator):
    """Logs workflow execution to audit trail"""
    # Similar pattern
```

#### 6. Mission Data Models (T11.6)

```python
class Mission:
    """Hermes-compatible mission"""
    id: str                        # mission-xxxxx
    type: str                      # customer_registration
    status: str                    # pending, executing, completed, failed
    objective: str
    
    tasks: List[Task]              # Dispatched tasks
    checkpoints: List[Checkpoint]  # Proof of completion
    cost: float                    # Total cost
    cost_breakdown: Dict[str, float]
    progress: float                # 0-100%
    
    created_at: datetime
    started_at: datetime
    completed_at: datetime
    duration_seconds: int
    
    final_result: Dict[str, Any]   # Combined results

class Checkpoint:
    """Proof of task completion"""
    timestamp: datetime
    task_type: str                 # create_auth_user, create_tenant
    status: str                    # ✅, ⏳, ❌
    proof: Dict[str, Any]          # The actual result
    operator_id: str
    duration_ms: int

class Task:
    """Work item"""
    id: str
    type: str
    operator: str
    payload: Dict[str, Any]
    status: str                    # assigned, queued, executing, completed
    created_at: datetime
    result: Optional[TaskResult]

class TaskResult:
    """Operator result"""
    task_id: str
    operator: str
    success: bool
    proof: Dict[str, Any]
    cost: float
    duration_ms: int
    error: Optional[str]
```

#### 7. Kanban Dashboard (T11.7)

```python
class KanbanDashboard:
    """React component for mission visualization"""
    
    # Columns
    ┌─────────────┬──────────────┬──────────────┬──────────────┐
    │  PENDING    │  EXECUTING   │  CHECKPOINTS │  COMPLETED   │
    ├─────────────┼──────────────┼──────────────┼──────────────┤
    │ Mission 3   │ Mission 1    │ Task 1 ✅    │ Mission 0    │
    │ (5 tasks)   │ Task A       │ Task 2 ✅    │ 5 tasks      │
    │             │ Task B       │ Task 3 ⏳    │ $0.047       │
    │ Mission 4   │ Task C       │ Task 4 ⏳    │ 14 min       │
    │ (2 tasks)   │             │ Task 5 ⏳    │              │
    │             │ Mission 2    │             │              │
    │             │ Task X ✅    │             │              │
    │             │ Task Y       │             │              │
    └─────────────┴──────────────┴──────────────┴──────────────┘
    
    // Metrics
    Total missions: 15
    Active (executing): 2
    Completed today: 8
    Total cost: $0.24
    Avg duration: 12 min
    Success rate: 95%
```

#### 8. Mission API (T11.8)

```python
# Mission endpoints
GET    /api/v1/missions
POST   /api/v1/missions/{id}/start
GET    /api/v1/missions/{id}
GET    /api/v1/missions/{id}/checkpoints
GET    /api/v1/missions/{id}/cost
GET    /api/v1/missions/{id}/progress

# Kanban endpoints
GET    /api/v1/kanban/dashboard
GET    /api/v1/kanban/boards
GET    /api/v1/kanban/tasks/{task_id}
POST   /api/v1/kanban/subscribe (WebSocket)
```

#### 9. Integration Tests (T11.9)

```python
# Test mission creation
# Test parallel task dispatching
# Test checkpoint collection
# Test cost calculation
# Test Kanban board state
# Test dashboard data
# Test error handling
# Test timeout handling
```

---

## 📊 HERMES INTEGRATION POINTS

### How T11 Fits into Hermes

```
Contexia Conductor (T11)
├─ Creates Mission (Hermes compatible)
├─ Dispatches Tasks (to swarm operators)
├─ Writes to Kanban DB (SQLite)
├─ Publishes Task Events (terminal states)
├─ Notifier watches for completion
└─ Users get notifications (via gateways)

Kanban Board (Existing Hermes System)
├─ Tracks task state (assigned → executing → terminal)
├─ Stores checkpoints (mission progress)
├─ Delivers notifications (notifier watcher)
├─ Multi-gateway support (dispatch owner)
└─ Subscription-based updates (WebSocket/polling)

Profiles (Multi-agent coordination)
├─ builder (one agent)
├─ centinela (another agent)
└─ [T11 could dispatch tasks to any profile]

Gateway (Existing infrastructure)
├─ Delivers notifications to Telegram
├─ Delivers notifications to Discord
├─ Single dispatcher owner (default profile)
└─ Notifier watcher (background loop)
```

### Kanban State Machine (Inherited)

```python
# Task state transitions
assigned → queued → executing → [terminal]

# Terminal states (notifier watches)
✅ completed    → Send notification
✅ archived     → Clean up
⏸️ blocked      → Notify blocker
❌ crashed      → Error notification
❌ gave_up      → Retry exhausted
❌ timed_out    → Timeout notification

# Notifier polls every 5 seconds for new terminal events
# Then sends message to user via gateway (Telegram, etc)
```

---

## 🚀 T11 EXECUTION PLAN (21 Hours)

### Phase 1: Core Orchestration (6 hours)
- **T11.1** (4h): Build Conductor class
  - Mission creation + lifecycle
  - Task dispatching (asyncio.gather)
  - Checkpoint collection
  - Cost tracking
  
- **T11.6** (2h): Build data models
  - Mission, Task, TaskResult, Checkpoint classes
  - CostTracker utility

### Phase 2: Swarm Operators (7 hours)
- **T11.2** (2h): Auth Operator
- **T11.3** (2h): DB Operator
- **T11.4** (1h): Roles Operator
- **T11.5** (2h): Comms + Workflow Tracker Operators

### Phase 3: Dashboard + API (5 hours)
- **T11.7** (3h): Kanban Dashboard (React)
- **T11.8** (2h): Mission API endpoints

### Phase 4: Testing (3 hours)
- **T11.9** (3h): Integration tests
  - Full mission execution
  - Parallel task verification
  - Kanban state validation
  - Error handling

---

## ✅ PHASE 3B FINAL TIMELINE (UPDATED)

```
✅ Jun 23: Phase 3A complete
✅ Jun 24-25: Core infrastructure complete
   ├─ Migrations (0010-0012)
   ├─ RBAC middleware
   ├─ Admin dashboard

⏳ Jun 26-27: T11 (Conductor + Swarms) — 21 hours
   ├─ T11.1-T11.6: Orchestration + Operators (13h)
   ├─ T11.7-T11.8: Dashboard + API (5h)
   └─ T11.9: Tests (3h)

⏳ Jun 27: T12 (RLS + role-based filtering) — 3 hours

⏳ Jun 27-28: T13-T15 (Email, tests, docs) — 6 hours

✅ Jun 30: PHASE 3B COMPLETE
   ├─ Conductor-based architecture
   ├─ Kanban integration
   ├─ Cost tracking
   ├─ Dashboard + API
   └─ Ready for Phase 2 (Jul 3)
```

---

## 💾 DEPLOYMENT TARGETS

**Frontend:**
- Kanban Dashboard (React component)
- Mission status view
- Cost breakdown display
- Real-time updates via WebSocket

**Backend:**
- Conductor class (apps/backend/operators/conductor.py)
- Swarm operators (apps/backend/operators/swarm/*.py)
- Mission API (apps/backend/presentation/mission_endpoints.py)
- Data models (apps/backend/models/mission.py)

**Database:**
- Kanban board integration (SQLite)
- Task event logging
- Checkpoint storage
- Cost tracking

---

## 🎯 SUCCESS CRITERIA

✅ Conductor orchestrates complete customer onboarding  
✅ 5 operators execute in parallel (asyncio)  
✅ Checkpoints recorded for each task  
✅ Cost tracked ($0.017 per mission)  
✅ Kanban dashboard shows real-time progress  
✅ Mission API provides RESTful access  
✅ Hermes integration validated (notifier + gateways)  
✅ All tests passing (integration + E2E)  

---

**This is the final T11 implementation plan, fully aligned with real Hermes architecture (Missions + Swarms + Kanban + Dispatcher). Ready to execute June 26-27.** ✅
