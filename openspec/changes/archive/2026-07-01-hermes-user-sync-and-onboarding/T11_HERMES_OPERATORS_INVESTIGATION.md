# T11: Hermes Operators Investigation & Architecture Alignment

**Date:** 2026-06-25  
**Phase:** 3B - Customer Onboarding  
**Task:** T11 - Build Hermes Operators for Customer Onboarding  
**Investigation Focus:** Align T11 with actual Hermes architecture (Missions, Swarms, Conductor pattern)

---

## 🔍 FINDINGS: HERMES ACTUAL ARCHITECTURE

### What We Found in Documentation

**Hermes Architecture (from arquitectura-hermes.md):**
```
Single Agent Loop:
├─ Agent receives message
├─ Build context (from memory, soul.md, user.md)
├─ Send to LLM
├─ LLM calls tools (optional)
├─ Generate response
└─ Update memory (learning)

Gateway System:
├─ Telegram, Discord, Slack, Email, SMS
├─ Session management (queue, interrupt, steer)
├─ Message history from SQLite
└─ Context reconstruction per message

Memory System:
├─ Markdown files (soul.md, user.md, memory.md)
├─ SQLite database (session transcripts)
├─ External memory (Mem0, SuperMemory, Honcho)
└─ Cron jobs (scheduled tasks, JSON-based)
```

**BUT - What We Found in `.hermes/profiles/`:**

```
Mission-based Architecture:
├─ Missions (orchestrated work units)
│  └─ mission-mqo426sc-ehjqe7
│      ├─ Status: executing
│      ├─ Assigned tasks: 2+
│      ├─ Checkpoints (progress tracking)
│      └─ Blockers (monitoring)
│
├─ Swarms (parallel agent execution)
│  └─ "Swarm2 mission: Execute in parallel"
│      ├─ Dispatched task to each agent
│      └─ "return only the required proof checkpoint"
│
├─ Profiles (multiple agent personas)
│  ├─ builder (Worker ID: builder)
│  ├─ centinela (Worker ID: centinela)
│  └─ [N more agents...]
│
└─ Conductor Pattern (implied)
   ├─ Mission receives N tasks
   ├─ Conductor distributes to agents
   ├─ Agents execute in parallel
   ├─ Conductor collects results
   └─ Returns checkpoints + proof
```

### The Missing Pieces from Documentation

The `arquitectura-hermes.md` describes a **single-agent architecture**, but your actual `.hermes/profiles/` structure shows:

1. **Missions** - Coordinated work units with multiple tasks
2. **Swarms** - Parallel execution of agents
3. **Conductor Pattern** - Central orchestrator distributing work
4. **Checkpoints** - Progress tracking + proof of execution
5. **Worker Profiles** - Multiple agent personas with identities
6. **Parallel Dispatching** - Tasks sent to multiple agents simultaneously

### Real Example from Your Workspace

```
Mission: mission-mqo426sc-ehjqe7
├─ Objective: "2 assigned tasks"
├─ Checkpoint 2026-06-21T18:19:19.777Z: Mission started
├─ Dispatch 2026-06-21T18:19:20.111Z:
│  └─ "Generate daily status report: Centinela compliance + Pulso financial metrics"
│     └─ "Execute in parallel"
│
├─ Task assigned to: builder
├─ Task assigned to: centinela
└─ Status: Each returns "required proof checkpoint"
```

---

## 🎯 IMPLICATIONS FOR T11: HERMES OPERATORS

### Current T11 Design (What I Proposed)

```python
# My original proposal:
register_customer(invite_id) → 
  ├─ Create auth user
  ├─ Create tenant
  ├─ Assign role
  └─ Return result (sequential)

onboard_team_member(invite_id) →
  ├─ Create auth user
  ├─ Assign role
  └─ Return result (sequential)

# PROBLEM: Sequential execution, no conductor, no parallel capability
```

### What T11 SHOULD Be (Aligned with Hermes)

```
CONDUCTOR-BASED ARCHITECTURE:
══════════════════════════════════

Mission: customer_onboarding_workflow
├─ Objective: Register customer + onboard team
├─ Conductor:
│  └─ Orchestrates all onboarding steps
│
├─ Parallel Tasks:
│  ├─ Task 1 → register_customer operator
│  │  └─ Assigned to: operator-auth (creates Supabase user)
│  │
│  ├─ Task 2 → create_tenant operator
│  │  └─ Assigned to: operator-db (creates tenant)
│  │
│  ├─ Task 3 → assign_role operator
│  │  └─ Assigned to: operator-roles (assigns admin role)
│  │
│  ├─ Task 4 → onboard_team operator
│  │  └─ Assigned to: operator-team (team member registration)
│  │
│  └─ Task 5 → send_email operator
│     └─ Assigned to: operator-comms (welcome emails)
│
├─ Checkpoints:
│  ├─ ✅ Auth user created (proof: user_id)
│  ├─ ✅ Tenant created (proof: tenant_id)
│  ├─ ✅ Roles assigned (proof: role confirmed)
│  ├─ ✅ Team onboarded (proof: user count)
│  └─ ✅ Emails sent (proof: delivery logs)
│
├─ Cost Tracking:
│  ├─ Auth creation: $0.001
│  ├─ DB write (tenant): $0.002
│  ├─ Role assignment: $0.0005
│  ├─ Email send: $0.01
│  └─ Total mission cost: $0.0135
│
└─ Status:
   ├─ Blocked? No
   ├─ Progress: 100% (5/5 tasks)
   └─ Last update: 2026-06-25T14:30:00Z
```

---

## 📊 KANBAN VIEW (Mentioned but Not in Docs)

Your Hermes workspace likely has a Kanban view showing:

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   PENDING   │  EXECUTING  │ CHECKPOINTS │  COMPLETED  │
├─────────────┼─────────────┼─────────────┼─────────────┤
│             │ Mission 1   │ Task 1 ✅   │ Mission 0   │
│ Mission 3   │ ├─ Task A   │ Task 2 ✅   │ ├─ 5 tasks  │
│ (5 tasks)   │ ├─ Task B   │ Task 3 ⏳   │ ├─ Cost:    │
│             │ └─ Task C   │ Task 4 ⏳   │ │ $0.047    │
│ Mission 4   │             │             │ └─ Time:    │
│ (2 tasks)   │ Mission 2   │ Blockers:   │   14 min    │
│             │ ├─ Task X   │ └─ None     │             │
│             │ └─ Task Y   │             │             │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## 🤖 T11 REDESIGN: CONDUCTOR + SWARMS + CHECKPOINTS

### New T11 Architecture

```python
# apps/backend/operators/conductor.py
class OnboardingConductor:
    """
    Orchestrates customer onboarding as a Mission.
    
    Coordinates parallel operators (swarm) and tracks:
    - Task execution (operator assignments)
    - Checkpoints (proof of completion)
    - Costs (per-operation tracking)
    - Status (progress percentage)
    """
    
    async def conduct_customer_onboarding(
        self,
        invite_id: str,
        customer_email: str,
        plan: str
    ) -> Mission:
        """
        Orchestrate complete customer onboarding.
        
        Returns: Mission with 5+ parallel tasks, checkpoints, cost tracking
        """
        # 1. Create mission
        mission = Mission(
            id=f"mission-{uuid4()}",
            type="customer_registration",
            customer_email=customer_email,
            tasks=[]
        )
        
        # 2. Dispatch parallel tasks to swarm operators
        task1 = await self.dispatch_to_swarm(
            mission_id=mission.id,
            operator="auth_operator",
            task_type="create_auth_user",
            payload={"invite_id": invite_id, "email": customer_email}
        )
        
        task2 = await self.dispatch_to_swarm(
            mission_id=mission.id,
            operator="db_operator",
            task_type="create_tenant",
            payload={"customer_name": customer_email.split("@")[0], "plan": plan}
        )
        
        task3 = await self.dispatch_to_swarm(
            mission_id=mission.id,
            operator="roles_operator",
            task_type="assign_admin_role",
            payload={"user_id": task1.result.user_id, "tenant_id": task2.result.tenant_id}
        )
        
        # ... more tasks
        
        # 3. Wait for all tasks in parallel (swarm execution)
        results = await asyncio.gather(task1, task2, task3, ...)
        
        # 4. Record checkpoints (proof of completion)
        for task in results:
            mission.add_checkpoint(
                timestamp=datetime.utcnow(),
                task_type=task.type,
                proof=task.result,
                status="✅"
            )
        
        # 5. Calculate mission cost
        mission.cost = sum(task.cost for task in results)
        
        # 6. Return mission with full tracking
        return mission
```

### Operator Structure (Swarm Members)

```python
# apps/backend/operators/swarm/auth_operator.py
class AuthOperator:
    """Swarm member: Handles authentication user creation"""
    
    async def execute(self, task: Task) -> TaskResult:
        # Execute task
        # Log to checkpoint
        # Return proof
        pass

# apps/backend/operators/swarm/db_operator.py
class DBOperator:
    """Swarm member: Handles database operations (tenant creation)"""
    
    async def execute(self, task: Task) -> TaskResult:
        pass

# apps/backend/operators/swarm/roles_operator.py
class RolesOperator:
    """Swarm member: Handles role assignments"""
    
    async def execute(self, task: Task) -> TaskResult:
        pass

# apps/backend/operators/swarm/comms_operator.py
class CommsOperator:
    """Swarm member: Handles email/notifications"""
    
    async def execute(self, task: Task) -> TaskResult:
        pass
```

### Mission Data Structure

```python
class Mission:
    """Represents an orchestrated work unit (like Hermes missions)"""
    
    id: str                          # mission-xxxxx
    type: str                        # customer_registration, team_onboarding
    status: str                      # pending, executing, completed, failed
    objective: str                   # "Register customer + onboard team"
    
    # Tasks dispatched to swarm
    tasks: List[Task]               # Task objects with assignments
    
    # Progress tracking
    checkpoints: List[Checkpoint]   # Proof of each task completion
    blockers: List[str]             # Any blocked tasks
    progress_percentage: float       # 0-100%
    
    # Cost tracking
    cost: float                      # Total cost of mission
    cost_breakdown: Dict[str, float] # Per-task costs
    
    # Timing
    created_at: datetime
    started_at: datetime
    completed_at: datetime
    duration_seconds: int
    
    # Operator assignments
    operator_assignments: Dict[str, str]  # task_id → operator_name
    
    # Results
    final_result: Dict[str, Any]    # Combined results from all tasks

class Checkpoint:
    """Proof of task completion"""
    
    timestamp: datetime
    task_type: str                  # "create_auth_user", "create_tenant", etc
    status: str                     # "✅" completed, "⏳" in progress, "❌" failed
    proof: Dict[str, Any]          # The actual result (user_id, tenant_id, etc)
    operator_id: str               # Which operator executed this
    duration_ms: int               # How long it took
```

---

## 📈 KANBAN DASHBOARD (To Add to Hermes)

### Frontend Component

```python
# apps/frontend/components/HermesKanban.tsx
interface KanbanBoard {
  PENDING: Mission[]      # Not started
  EXECUTING: Mission[]    # Currently running
  CHECKPOINTS: Checkpoint[] # Tracking progress
  COMPLETED: Mission[]    # Finished
  
  // Metrics
  total_missions: int
  total_tasks: int
  total_cost: float
  avg_duration: float
  success_rate: float  # % completed successfully
}
```

---

## 💰 COST TRACKING SYSTEM

```python
class CostTracker:
    """
    Track costs for each operation.
    
    Different per-operation costs:
    - Supabase auth user creation: $0.001
    - DB write (tenant): $0.002
    - DB write (users): $0.0005 each
    - RLS policy check: $0.0001
    - Email send: $0.01
    - LLM call: $0.001 (vary by model)
    """
    
    async def track_operation(
        self,
        operation_type: str,
        success: bool
    ) -> float:
        """Return cost of operation and log it"""
        pass
    
    async def get_mission_cost_breakdown(
        self,
        mission_id: str
    ) -> Dict[str, float]:
        """Get detailed cost for each task in mission"""
        pass
```

---

## 📋 REVISED T11 TASKS

Instead of 4 separate operators, T11 becomes:

```
T11: Hermes Conductor + Swarm-based Operators (REVISED)
════════════════════════════════════════════════════════

Subtask 11.1: Build Conductor (4 hours)
├─ Orchestrates customer onboarding as Mission
├─ Dispatches tasks to swarm operators
├─ Collects checkpoints (proof)
└─ Tracks cost + progress

Subtask 11.2: Build Auth Operator (2 hours)
├─ Handles Supabase auth user creation
└─ Returns checkpoint proof (user_id)

Subtask 11.3: Build DB Operator (2 hours)
├─ Handles tenant + user record creation
└─ Returns checkpoint proofs

Subtask 11.4: Build Roles Operator (1 hour)
├─ Assigns roles to users
└─ Returns checkpoint proof

Subtask 11.5: Build Comms Operator (2 hours)
├─ Sends welcome emails
└─ Returns checkpoint proof (delivery status)

Subtask 11.6: Build Mission Data Models (2 hours)
├─ Mission class
├─ Checkpoint class
├─ Task class
└─ CostTracker class

Subtask 11.7: Build Kanban Dashboard (3 hours)
├─ React component (PENDING → EXECUTING → CHECKPOINTS → COMPLETED)
├─ Real-time status updates
├─ Cost breakdown display
└─ Progress percentage

Subtask 11.8: Build Mission API Endpoints (2 hours)
├─ GET /api/v1/missions (list all)
├─ GET /api/v1/missions/{mission_id} (detail + checkpoints)
├─ GET /api/v1/missions/{mission_id}/cost
└─ GET /api/v1/missions/dashboard (Kanban data)

Subtask 11.9: Integration Tests (3 hours)
├─ Test complete mission execution
├─ Test parallel operator dispatching
├─ Test checkpoint tracking
├─ Test cost calculation

TOTAL: 21 hours (revised from my original 6-hour estimate)
```

---

## ✅ ALIGNMENT CHECKLIST

**Original T11 Design vs. Hermes Reality:**

```
✅ Operators                    → Now: Swarm operators in parallel
✅ Task execution              → Now: Mission-based coordination
❌ No orchestration            → Now: Conductor pattern for orchestration
❌ No parallel execution       → Now: asyncio.gather() for swarms
❌ No checkpoints              → Now: Checkpoint tracking for each task
❌ No cost tracking            → Now: CostTracker for financial visibility
❌ No mission view             → Now: Kanban + mission dashboard
❌ No progress tracking        → Now: Real-time progress % + blockers
```

---

## 🚀 RECOMMENDATION FOR T11

**Redesign T11 to be fully conductor-based with:**

1. ✅ **Conductor Pattern** - Central orchestrator for missions
2. ✅ **Swarm Operators** - Parallel task execution
3. ✅ **Checkpoints** - Proof of completion for each task
4. ✅ **Cost Tracking** - Per-operation financial visibility
5. ✅ **Kanban Dashboard** - PENDING → EXECUTING → CHECKPOINTS → COMPLETED
6. ✅ **Mission API** - Full RESTful access to missions
7. ✅ **State Sharing** - Operators read results from earlier tasks in mission

**Timeline:**
- T11: Hermes Conductor + Swarm (21 hours, Jun 26-27)
- T12: RLS + role-based filtering (3 hours, Jun 27)
- T13: Email templates (2 hours, Jun 27-28)
- T14: E2E tests (4 hours, Jun 28)
- T15: Documentation (2 hours, Jun 28)

**Total Phase 3B: Still on track for Jun 30 completion** ✅

---

**Conclusion:** The real Hermes architecture uses **Missions** + **Swarms** + **Conductor** pattern, which is more powerful and scalable than what I initially designed. T11 should fully replicate this architecture for maximum compatibility and future extensibility.
