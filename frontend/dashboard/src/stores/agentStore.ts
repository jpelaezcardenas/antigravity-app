/**
 * Zustand Store for Agent Data Management
 * Persists to localStorage with automatic rehydration on app boot
 * Supports offline-first workflows with fresh data merging
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { Decimal } from 'decimal.js';

// Types from Phase 5
export interface AgentOutput {
  data: Record<string, any>;
  timestamp: number;
  status: 'success' | 'error';
}

export interface UserProfile {
  id: string;
  email: string;
  permissions: string[];
  workspace_id: string;
}

export interface DraftApproval {
  id: string;
  type: string;
  title: string;
  description: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  updated_at: string;
  agent?: string;
  content?: Record<string, any>;
}

export interface UserSettings {
  theme: 'light' | 'dark';
  notifications_enabled: boolean;
  language: string;
}

export interface AppError {
  message: string;
  code?: string;
  statusCode?: number;
  timestamp: number;
}

// Store State Interface
export interface AgentState {
  // Data sections (persisted)
  agents: Record<string, AgentOutput>;
  user: UserProfile | null;
  approvals: DraftApproval[];
  settings: UserSettings;

  // Metadata (not persisted)
  isLoading: boolean;
  error: AppError | null;
  lastSync: number;

  // Actions
  setAgentData: (agent: string, data: AgentOutput) => void;
  setUser: (user: UserProfile | null) => void;
  addApproval: (draft: DraftApproval) => void;
  updateApproval: (id: string, status: DraftApproval['status']) => void;
  removeApproval: (id: string) => void;
  setError: (error: AppError | null) => void;
  setLoading: (loading: boolean) => void;
  clearError: () => void;
  reset: () => void;

  // Selectors (derived)
  getApprovalById: (id: string) => DraftApproval | undefined;
  getAgentData: (agentName: string) => AgentOutput | undefined;
  getPendingApprovals: () => DraftApproval[];
}

const initialState = {
  agents: {},
  user: null,
  approvals: [],
  settings: {
    theme: 'light' as const,
    notifications_enabled: true,
    language: 'en',
  },
  isLoading: false,
  error: null,
  lastSync: 0,
};

/**
 * Zustand store with localStorage persistence
 * Schema version: 1
 */
export const useAgentStore = create<AgentState>(
  persist(
    (set, get) => ({
      ...initialState,

      // Actions
      setAgentData: (agent: string, data: AgentOutput) => {
        set((state) => ({
          agents: {
            ...state.agents,
            [agent]: {
              ...data,
              timestamp: Date.now(),
            },
          },
          lastSync: Date.now(),
        }));
      },

      setUser: (user: UserProfile | null) => {
        set({ user, lastSync: Date.now() });
      },

      addApproval: (draft: DraftApproval) => {
        set((state) => ({
          approvals: [...state.approvals, draft],
          lastSync: Date.now(),
        }));
      },

      updateApproval: (id: string, status: DraftApproval['status']) => {
        set((state) => ({
          approvals: state.approvals.map((approval) =>
            approval.id === id
              ? { ...approval, status, updated_at: new Date().toISOString() }
              : approval
          ),
          lastSync: Date.now(),
        }));
      },

      removeApproval: (id: string) => {
        set((state) => ({
          approvals: state.approvals.filter((approval) => approval.id !== id),
          lastSync: Date.now(),
        }));
      },

      setError: (error: AppError | null) => {
        set({ error });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      clearError: () => {
        set({ error: null });
      },

      reset: () => {
        set(initialState);
      },

      // Selectors
      getApprovalById: (id: string) => {
        return get().approvals.find((approval) => approval.id === id);
      },

      getAgentData: (agentName: string) => {
        return get().agents[agentName];
      },

      getPendingApprovals: () => {
        return get().approvals.filter((approval) => approval.status === 'pending');
      },
    }),

    {
      name: 'agent-store',
      version: 1,

      storage: createJSONStorage(() => localStorage),

      // Only persist data, not transient state
      partialize: (state) => ({
        agents: state.agents,
        user: state.user,
        approvals: state.approvals,
        settings: state.settings,
      }),

      // Migration handler
      migrate: (persistedState: any, version: number) => {
        if (version < 1) {
          console.warn('Clearing corrupted localStorage state');
          return initialState;
        }
        return persistedState;
      },
    }
  )
);

// Convenience hooks (selectors)
export const useAgents = () => useAgentStore((state) => state.agents);
export const useUser = () => useAgentStore((state) => state.user);
export const useApprovals = () => useAgentStore((state) => state.approvals);
export const useSettings = () => useAgentStore((state) => state.settings);
export const useError = () => useAgentStore((state) => state.error);
export const useIsLoading = () => useAgentStore((state) => state.isLoading);
export const usePendingApprovals = () =>
  useAgentStore((state) => state.approvals.filter((a) => a.status === 'pending'));

export const useAgentData = (agentName: string) =>
  useAgentStore((state) => state.agents[agentName]);
