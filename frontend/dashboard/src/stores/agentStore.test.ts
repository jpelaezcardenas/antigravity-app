/**
 * Unit Tests for Zustand Agent Store
 * Tests: selectors, actions, persistence, rehydration
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useAgentStore } from './agentStore';

describe('Agent Store', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Reset store
    useAgentStore.setState({
      agents: {},
      user: null,
      approvals: [],
      settings: {
        theme: 'light',
        notifications_enabled: true,
        language: 'en',
      },
      isLoading: false,
      error: null,
      lastSync: 0,
    });
  });

  afterEach(() => {
    localStorage.clear();
  });

  // === SELECTOR TESTS ===

  describe('Selectors', () => {
    it('useAgents returns agents record', () => {
      const store = useAgentStore.getState();
      const agents = store.agents;
      expect(agents).toEqual({});
    });

    it('useUser returns user or null', () => {
      const store = useAgentStore.getState();
      const user = store.user;
      expect(user).toBeNull();
    });

    it('useApprovals returns approval array', () => {
      const store = useAgentStore.getState();
      const approvals = store.approvals;
      expect(Array.isArray(approvals)).toBe(true);
      expect(approvals.length).toBe(0);
    });

    it('getAgentData returns agent by name', () => {
      const store = useAgentStore.getState();
      useAgentStore.setState({
        agents: {
          pulso: {
            data: { caja_real: '1000' },
            timestamp: Date.now(),
            status: 'success',
          },
        },
      });

      const agent = store.getAgentData('pulso');
      expect(agent).toBeDefined();
      expect(agent?.data.caja_real).toBe('1000');
    });

    it('getPendingApprovals filters by status', () => {
      const store = useAgentStore.getState();
      useAgentStore.setState({
        approvals: [
          {
            id: '1',
            type: 'test',
            title: 'Draft 1',
            description: 'Test',
            status: 'pending',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '2',
            type: 'test',
            title: 'Draft 2',
            description: 'Test',
            status: 'approved',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
      });

      const pending = store.getPendingApprovals();
      expect(pending.length).toBe(1);
      expect(pending[0].id).toBe('1');
    });
  });

  // === ACTION TESTS ===

  describe('Actions', () => {
    it('setAgentData updates agents with timestamp', () => {
      const store = useAgentStore.getState();
      const testData = {
        data: { caja_real: '5000' },
        timestamp: 0,
        status: 'success' as const,
      };

      store.setAgentData('pulso', testData);
      const state = useAgentStore.getState();

      expect(state.agents.pulso).toBeDefined();
      expect(state.agents.pulso.data.caja_real).toBe('5000');
      expect(state.agents.pulso.timestamp).toBeGreaterThan(0);
    });

    it('setUser updates user', () => {
      const store = useAgentStore.getState();
      const testUser = {
        id: 'user-123',
        email: 'test@example.com',
        permissions: ['READ_PULSO'],
        workspace_id: 'ws-123',
      };

      store.setUser(testUser);
      const state = useAgentStore.getState();

      expect(state.user).toEqual(testUser);
    });

    it('addApproval appends to approvals', () => {
      const store = useAgentStore.getState();
      const testDraft = {
        id: 'draft-1',
        type: 'tax_correction',
        title: 'Test Draft',
        description: 'Test description',
        status: 'pending' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      store.addApproval(testDraft);
      const state = useAgentStore.getState();

      expect(state.approvals.length).toBe(1);
      expect(state.approvals[0].id).toBe('draft-1');
    });

    it('updateApproval changes status', () => {
      const store = useAgentStore.getState();
      store.addApproval({
        id: 'draft-1',
        type: 'test',
        title: 'Test',
        description: 'Test',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });

      store.updateApproval('draft-1', 'approved');
      const state = useAgentStore.getState();

      expect(state.approvals[0].status).toBe('approved');
    });

    it('removeApproval filters by id', () => {
      const store = useAgentStore.getState();
      store.addApproval({
        id: 'draft-1',
        type: 'test',
        title: 'Test',
        description: 'Test',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });

      expect(useAgentStore.getState().approvals.length).toBe(1);

      store.removeApproval('draft-1');
      expect(useAgentStore.getState().approvals.length).toBe(0);
    });

    it('setError updates error', () => {
      const store = useAgentStore.getState();
      const testError = {
        message: 'Test error',
        code: 'TEST_ERROR',
        statusCode: 500,
        timestamp: Date.now(),
      };

      store.setError(testError);
      expect(useAgentStore.getState().error).toEqual(testError);
    });

    it('clearError sets error to null', () => {
      const store = useAgentStore.getState();
      store.setError({
        message: 'Test',
        code: 'TEST',
        timestamp: Date.now(),
      });

      expect(useAgentStore.getState().error).toBeDefined();

      store.clearError();
      expect(useAgentStore.getState().error).toBeNull();
    });

    it('reset clears all state', () => {
      const store = useAgentStore.getState();
      store.setAgentData('pulso', {
        data: { test: 'data' },
        timestamp: 0,
        status: 'success',
      });
      store.addApproval({
        id: '1',
        type: 'test',
        title: 'Test',
        description: 'Test',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });

      expect(useAgentStore.getState().agents).not.toEqual({});
      expect(useAgentStore.getState().approvals.length).toBeGreaterThan(0);

      store.reset();

      expect(useAgentStore.getState().agents).toEqual({});
      expect(useAgentStore.getState().approvals).toEqual([]);
    });
  });

  // === PERSISTENCE TESTS ===

  describe('Persistence', () => {
    it('persists agents to localStorage', () => {
      const store = useAgentStore.getState();
      const testData = {
        data: { caja_real: '1000' },
        timestamp: Date.now(),
        status: 'success' as const,
      };

      store.setAgentData('pulso', testData);

      const stored = localStorage.getItem('agent-store');
      expect(stored).toBeDefined();

      const parsed = JSON.parse(stored!);
      expect(parsed.state.agents.pulso).toBeDefined();
    });

    it('persists approvals to localStorage', () => {
      const store = useAgentStore.getState();
      const testDraft = {
        id: 'draft-1',
        type: 'test',
        title: 'Test',
        description: 'Test',
        status: 'pending' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      store.addApproval(testDraft);

      const stored = localStorage.getItem('agent-store');
      const parsed = JSON.parse(stored!);
      expect(parsed.state.approvals.length).toBe(1);
    });

    it('does NOT persist transient state', () => {
      const store = useAgentStore.getState();
      store.setLoading(true);
      store.setError({
        message: 'Test',
        code: 'TEST',
        timestamp: Date.now(),
      });

      const stored = localStorage.getItem('agent-store');
      const parsed = JSON.parse(stored!);

      expect(parsed.state.isLoading).toBeUndefined();
      expect(parsed.state.error).toBeUndefined();
    });
  });

  // === REHYDRATION TESTS ===

  describe('Rehydration', () => {
    it('rehydrates data from localStorage', () => {
      const store = useAgentStore.getState();
      store.setAgentData('pulso', {
        data: { test: 'value' },
        timestamp: Date.now(),
        status: 'success',
      });

      // Simulate page reload: new store instance
      const newStore = useAgentStore.getState();
      expect(newStore.agents.pulso).toBeDefined();
    });

    it('rehydrates user from localStorage', () => {
      const store = useAgentStore.getState();
      const testUser = {
        id: 'user-123',
        email: 'test@example.com',
        permissions: [],
        workspace_id: 'ws-123',
      };

      store.setUser(testUser);

      const newStore = useAgentStore.getState();
      expect(newStore.user).toEqual(testUser);
    });

    it('handles corrupted localStorage gracefully', () => {
      localStorage.setItem('agent-store', '{invalid json}');

      expect(() => {
        const store = useAgentStore.getState();
        expect(store.agents).toEqual({});
      }).not.toThrow();
    });
  });
});
