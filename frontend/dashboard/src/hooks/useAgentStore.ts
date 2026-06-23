/**
 * Convenience hooks for Agent Store selectors
 * Use these instead of directly calling useAgentStore for cleaner component code
 */

import { useAgentStore } from '../stores/agentStore';

/**
 * Hook: Get all agents data
 * @returns Record<string, AgentOutput>
 */
export const useAgents = () => {
  return useAgentStore((state) => state.agents);
};

/**
 * Hook: Get current user profile
 * @returns UserProfile | null
 */
export const useUser = () => {
  return useAgentStore((state) => state.user);
};

/**
 * Hook: Get all approvals
 * @returns DraftApproval[]
 */
export const useApprovals = () => {
  return useAgentStore((state) => state.approvals);
};

/**
 * Hook: Get user settings
 * @returns UserSettings
 */
export const useSettings = () => {
  return useAgentStore((state) => state.settings);
};

/**
 * Hook: Get current error (if any)
 * @returns AppError | null
 */
export const useError = () => {
  return useAgentStore((state) => state.error);
};

/**
 * Hook: Get loading state
 * @returns boolean
 */
export const useIsLoading = () => {
  return useAgentStore((state) => state.isLoading);
};

/**
 * Hook: Get single agent data by name
 * @param agentName - Name of agent (pulso, centinela, radar, etc.)
 * @returns AgentOutput | undefined
 */
export const useAgentData = (agentName: string) => {
  return useAgentStore((state) => state.agents[agentName]);
};

/**
 * Hook: Get pending approvals (filtered by status='pending')
 * @returns DraftApproval[]
 */
export const usePendingApprovals = () => {
  return useAgentStore((state) =>
    state.approvals.filter((approval) => approval.status === 'pending')
  );
};

/**
 * Hook: Get approved approvals
 * @returns DraftApproval[]
 */
export const useApprovedApprovals = () => {
  return useAgentStore((state) =>
    state.approvals.filter((approval) => approval.status === 'approved')
  );
};

/**
 * Hook: Get rejected approvals
 * @returns DraftApproval[]
 */
export const useRejectedApprovals = () => {
  return useAgentStore((state) =>
    state.approvals.filter((approval) => approval.status === 'rejected')
  );
};

/**
 * Hook: Get all store actions
 * Returns object with all setters: setAgentData, setUser, addApproval, etc.
 */
export const useStoreActions = () => {
  return useAgentStore((state) => ({
    setAgentData: state.setAgentData,
    setUser: state.setUser,
    addApproval: state.addApproval,
    updateApproval: state.updateApproval,
    removeApproval: state.removeApproval,
    setError: state.setError,
    setLoading: state.setLoading,
    clearError: state.clearError,
    reset: state.reset,
  }));
};

/**
 * Hook: Get approval by ID
 * @param id - Approval ID
 * @returns DraftApproval | undefined
 */
export const useApprovalById = (id: string) => {
  return useAgentStore((state) => state.getApprovalById(id));
};

/**
 * Hook: Get user permissions
 * @returns string[]
 */
export const usePermissions = () => {
  return useAgentStore((state) => state.user?.permissions ?? []);
};

/**
 * Hook: Check if user has specific permission
 * @param permission - Permission to check
 * @returns boolean
 */
export const useHasPermission = (permission: string) => {
  return useAgentStore((state) =>
    state.user?.permissions.includes(permission) ?? false
  );
};

/**
 * Hook: Get user email
 * @returns string | undefined
 */
export const useUserEmail = () => {
  return useAgentStore((state) => state.user?.email);
};

/**
 * Hook: Get user ID
 * @returns string | undefined
 */
export const useUserId = () => {
  return useAgentStore((state) => state.user?.id);
};

/**
 * Hook: Get workspace ID
 * @returns string | undefined
 */
export const useWorkspaceId = () => {
  return useAgentStore((state) => state.user?.workspace_id);
};

/**
 * Hook: Get last sync timestamp
 * @returns number (milliseconds)
 */
export const useLastSync = () => {
  return useAgentStore((state) => state.lastSync);
};

/**
 * Hook: Check if store has unsaved changes
 * @returns boolean
 */
export const useHasUnsavedChanges = () => {
  return useAgentStore((state) => {
    // Has unsaved changes if:
    // 1. Any agents have been updated but not yet synced
    // 2. Any approvals are pending
    // 3. Error is present
    const hasAgents = Object.keys(state.agents).length > 0;
    const hasPending = state.approvals.some((a) => a.status === 'pending');
    const hasError = state.error !== null;

    return hasAgents || hasPending || hasError;
  });
};
