/**
 * Hook: Store Rehydration
 * Loads cached data from localStorage on app boot
 * Fetches fresh data in background and merges intelligently
 * No loading spinner needed - cache loads immediately
 */

import { useEffect, useRef } from 'react';
import { useAgentStore } from '../stores/agentStore';

interface RehydrationOptions {
  onRehydrateComplete?: () => void;
  onError?: (error: Error) => void;
  fetchFreshData?: boolean; // default: true
}

/**
 * Hook: Rehydrate store from localStorage and fetch fresh data
 * Call this once on app boot (e.g., in root layout component)
 *
 * Usage:
 *   useStoreRehydration({
 *     onRehydrateComplete: () => console.log('Store ready'),
 *     fetchFreshData: true
 *   });
 */
export const useStoreRehydration = (options: RehydrationOptions = {}) => {
  const { onRehydrateComplete, onError, fetchFreshData = true } = options;
  const hasRehydratedRef = useRef(false);

  useEffect(() => {
    // Prevent double rehydration in StrictMode
    if (hasRehydratedRef.current) return;
    hasRehydratedRef.current = true;

    const rehydrate = async () => {
      try {
        // Step 1: Load from localStorage (synchronous, instant)
        const stored = localStorage.getItem('agent-store');
        if (stored) {
          const parsed = JSON.parse(stored);
          const cachedState = parsed.state;

          // Restore cached state to store
          useAgentStore.setState({
            agents: cachedState.agents || {},
            user: cachedState.user || null,
            approvals: cachedState.approvals || [],
            settings: cachedState.settings || {
              theme: 'light',
              notifications_enabled: true,
              language: 'en',
            },
          });

          console.log('[Rehydration] Loaded cached data from localStorage');
        }

        // Step 2: Fetch fresh data in background (async, non-blocking)
        if (fetchFreshData) {
          fetchFreshDataInBackground();
        }

        // Notify that rehydration is complete
        onRehydrateComplete?.();
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        console.error('[Rehydration] Error loading from localStorage:', err);

        // Clear corrupted localStorage
        localStorage.removeItem('agent-store');

        // Notify error
        onError?.(err);
      }
    };

    rehydrate();
  }, [onRehydrateComplete, onError, fetchFreshData]);
};

/**
 * Internal: Fetch fresh data from backend in background
 * Merges with cached data intelligently (fresh data wins)
 * Task 2.6: Error handling with logging (toast not available in background context)
 */
const fetchFreshDataInBackground = async () => {
  try {
    // Fetch fresh user data
    const userResponse = await fetch('/api/v1/auth/me');
    if (userResponse.ok) {
      const userData = await userResponse.json();
      useAgentStore.setState({
        user: userData,
      });
      console.log('[Rehydration] Fetched fresh user data');
    } else {
      console.warn('[Rehydration] Failed to fetch user data:', userResponse.status);
    }

    // Fetch fresh agent data (all agents in parallel)
    const agents = [
      'pulso',
      'centinela',
      'radar',
      'taty',
      'social-ops',
      'audit',
      'approval',
      'maestro',
    ];

    const agentRequests = agents.map((agent) =>
      fetch(`/api/v1/agents/${agent}/stream`)
        .then((res) => {
          if (!res.ok) {
            console.warn(`[Rehydration] Failed to fetch ${agent}:`, res.status);
            return null;
          }
          return res.json();
        })
        .catch((err) => {
          console.error(`[Rehydration] Error fetching ${agent}:`, err);
          return null;
        })
    );

    const agentResults = await Promise.all(agentRequests);

    const freshAgents: Record<string, any> = {};
    agentResults.forEach((result, index) => {
      if (result) {
        freshAgents[agents[index]] = {
          data: result.data,
          timestamp: Date.now(),
          status: 'success',
        };
      }
    });

    if (Object.keys(freshAgents).length > 0) {
      // Merge: fresh data wins over cached
      const currentAgents = useAgentStore.getState().agents;
      useAgentStore.setState({
        agents: {
          ...currentAgents,
          ...freshAgents,
        },
      });
      console.log('[Rehydration] Merged fresh agent data');
    } else {
      console.warn('[Rehydration] No agent data fetched successfully');
    }
  } catch (error) {
    console.error('[Rehydration] Error fetching fresh data:', error);
    // Don't throw - if background fetch fails, use cached data
  }
};

/**
 * Hook: Force refresh of specific agent data
 * Useful for "refresh now" buttons in UI
 */
export const useRefreshAgent = () => {
  return async (agentName: string) => {
    try {
      useAgentStore.setState({ isLoading: true });

      const response = await fetch(`/api/v1/agents/${agentName}/stream`);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${agentName} data`);
      }

      const data = await response.json();
      useAgentStore.getState().setAgentData(agentName, {
        data: data.data,
        timestamp: Date.now(),
        status: 'success',
      });

      useAgentStore.setState({ isLoading: false });
      console.log(`[Refresh] Updated ${agentName} data`);
    } catch (error) {
      useAgentStore.setState({
        isLoading: false,
        error: {
          message: error instanceof Error ? error.message : 'Unknown error',
          code: 'FETCH_ERROR',
          timestamp: Date.now(),
        },
      });
    }
  };
};

/**
 * Hook: Clear all cached data and reset store
 * Useful for logout
 */
export const useClearCache = () => {
  return () => {
    localStorage.removeItem('agent-store');
    useAgentStore.getState().reset();
    console.log('[Cache] Cleared all cached data');
  };
};
