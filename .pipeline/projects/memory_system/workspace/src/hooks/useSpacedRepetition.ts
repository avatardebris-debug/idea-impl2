import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  DifficultyConfig,
  SpacedRepetitionSchedule,
  SpacedRepetitionParams,
  RecallQuality,
  DifficultyAdaptationResult,
  ReviewQueueItem,
  SpacedRepetitionStats,
  SpacedRepetitionSessionResult,
} from '../types/spacedRepetition';
import {
  createInitialDifficultyConfig,
  updateDifficultyConfig,
  getDueItems,
  calculateSpacedRepetitionStats,
  createSessionResult,
  getItemsByStatus,
  getItemsDueInRange,
  estimateReviewTime,
} from '../utils/spacedRepetition';

/**
 * Hook for managing spaced repetition
 */
export function useSpacedRepetition(params?: SpacedRepetitionParams) {
  const [schedules, setSchedules] = useState<Record<string, SpacedRepetitionSchedule>>({});
  const [difficultyConfigs, setDifficultyConfigs] = useState<Record<string, DifficultyConfig>>({});
  const [sessionResults, setSessionResults] = useState<SpacedRepetitionSessionResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const loadedSchedules = localStorage.getItem('spacedRepetitionSchedules');
      const loadedConfigs = localStorage.getItem('spacedRepetitionConfigs');
      const loadedResults = localStorage.getItem('spacedRepetitionResults');

      if (loadedSchedules) {
        setSchedules(JSON.parse(loadedSchedules));
      }
      if (loadedConfigs) {
        setDifficultyConfigs(JSON.parse(loadedConfigs));
      }
      if (loadedResults) {
        setSessionResults(JSON.parse(loadedResults));
      }
    } catch (err) {
      setError('Failed to load spaced repetition data');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Save to localStorage on change
  useEffect(() => {
    if (!isLoading) {
      try {
        localStorage.setItem('spacedRepetitionSchedules', JSON.stringify(schedules));
        localStorage.setItem('spacedRepetitionConfigs', JSON.stringify(difficultyConfigs));
        localStorage.setItem('spacedRepetitionResults', JSON.stringify(sessionResults));
      } catch (err) {
        setError('Failed to save spaced repetition data');
        console.error(err);
      }
    }
  }, [schedules, difficultyConfigs, sessionResults, isLoading]);

  // Add a new item to review
  const addItem = useCallback((itemId: string, initialSchedule?: Partial<SpacedRepetitionSchedule>) => {
    setSchedules((prev) => ({
      ...prev,
      [itemId]: {
        itemId,
        scheduledDate: new Date().toISOString(),
        difficulty: 'medium',
        priority: 0,
        reason: initialSchedule?.reason || 'Initial item',
        ...initialSchedule,
      },
    }));

    setDifficultyConfigs((prev) => ({
      ...prev,
      [itemId]: createInitialDifficultyConfig(itemId),
    }));
  }, []);

  // Remove an item
  const removeItem = useCallback((itemId: string) => {
    setSchedules((prev) => {
      const { [itemId]: _, ...rest } = prev;
      return rest;
    });
    setDifficultyConfigs((prev) => {
      const { [itemId]: _, ...rest } = prev;
      return rest;
    });
  }, []);

  // Mark an item as reviewed with quality rating
  const reviewItem = useCallback(
    (itemId: string, quality: RecallQuality) => {
      const schedule = schedules[itemId];
      const config = difficultyConfigs[itemId];

      if (!schedule || !config) {
        setError(`Item ${itemId} not found`);
        return null;
      }

      const { config: updatedConfig, update } = updateDifficultyConfig(config, quality, params);

      setDifficultyConfigs((prev) => ({
        ...prev,
        [itemId]: updatedConfig,
      }));

      setSchedules((prev) => ({
        ...prev,
        [itemId]: {
          ...schedule,
          scheduledDate: update.nextReviewDate,
          difficulty: updatedConfig.level,
          priority: updatedConfig.status === 'mastered' ? 10 : updatedConfig.repetition,
        },
      }));

      return update;
    },
    [schedules, difficultyConfigs, params]
  );

  // Get items due for review
  const getDueItemsForReview = useCallback(
    (limit?: number): ReviewQueueItem[] => {
      const dueItems = getDueItems(schedules);
      return limit ? dueItems.slice(0, limit) : dueItems;
    },
    [schedules]
  );

  // Get statistics
  const stats = useMemo<SpacedRepetitionStats>(() => {
    return calculateSpacedRepetitionStats(schedules);
  }, [schedules]);

  // Get items by status
  const getItemsByStatus = useCallback(
    (status: DifficultyConfig['status']): string[] => {
      return getItemsByStatus(schedules, status);
    },
    [schedules]
  );

  // Get items due in a date range
  const getItemsDueInRange = useCallback(
    (startDate: Date, endDate: Date): ReviewQueueItem[] => {
      return getItemsDueInRange(schedules, startDate, endDate);
    },
    [schedules]
  );

  // Complete a review session
  const completeSession = useCallback(
    (itemsReviewed: number, itemsMastered: number, qualities: RecallQuality[], timeSpent: number) => {
      const result = createSessionResult(itemsReviewed, itemsMastered, qualities, timeSpent);
      setSessionResults((prev) => [result, ...prev]);
      return result;
    },
    []
  );

  // Adapt difficulty for an item
  const adaptDifficulty = useCallback(
    (itemId: string, accuracy: number): DifficultyAdaptationResult | null => {
      const config = difficultyConfigs[itemId];
      if (!config) {
        setError(`Item ${itemId} not found`);
        return null;
      }

      const result = {
        itemId,
        previousDifficulty: config.level,
        newDifficulty: config.level,
        reason: 'No change',
        confidence: 0.5,
      };

      // Simple adaptation logic
      if (accuracy >= 0.9 && config.level !== 'very_easy') {
        result.newDifficulty = 'very_easy';
        result.reason = 'High accuracy suggests easier difficulty';
        result.confidence = accuracy;
      } else if (accuracy <= 0.5 && config.level !== 'very_hard') {
        result.newDifficulty = 'very_hard';
        result.reason = 'Low accuracy suggests harder difficulty';
        result.confidence = 1 - accuracy;
      }

      setDifficultyConfigs((prev) => ({
        ...prev,
        [itemId]: {
          ...config,
          level: result.newDifficulty,
        },
      }));

      return result;
    },
    [difficultyConfigs]
  );

  // Reset an item to initial state
  const resetItem = useCallback((itemId: string) => {
    setSchedules((prev) => ({
      ...prev,
      [itemId]: {
        itemId,
        scheduledDate: new Date().toISOString(),
        difficulty: 'medium',
        priority: 0,
        reason: 'Reset',
      },
    }));

    setDifficultyConfigs((prev) => ({
      ...prev,
      [itemId]: createInitialDifficultyConfig(itemId),
    }));
  }, []);

  // Clear all data
  const clearAll = useCallback(() => {
    setSchedules({});
    setDifficultyConfigs({});
    setSessionResults([]);
    localStorage.removeItem('spacedRepetitionSchedules');
    localStorage.removeItem('spacedRepetitionConfigs');
    localStorage.removeItem('spacedRepetitionResults');
  }, []);

  return {
    schedules,
    difficultyConfigs,
    sessionResults,
    isLoading,
    error,
    stats,
    addItem,
    removeItem,
    reviewItem,
    getDueItemsForReview,
    getItemsByStatus,
    getItemsDueInRange,
    completeSession,
    adaptDifficulty,
    resetItem,
    clearAll,
  };
}

/**
 * Hook for getting due items with priority
 */
export function useReviewQueue(params?: SpacedRepetitionParams) {
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      const loadedSchedules = localStorage.getItem('spacedRepetitionSchedules');
      if (loadedSchedules) {
        const schedules = JSON.parse(loadedSchedules);
        const dueItems = getDueItems(schedules, new Date());
        setQueue(dueItems);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    queue,
    isLoading,
    totalDue: queue.length,
    estimatedTime: queue.reduce((sum, item) => sum + item.estimatedTime, 0),
  };
}

/**
 * Hook for tracking review sessions
 */
export function useReviewSession() {
  const [currentSession, setCurrentSession] = useState<{
    itemsReviewed: number;
    itemsMastered: number;
    qualities: RecallQuality[];
    startTime: number;
  } | null>(null);

  const startSession = useCallback(() => {
    setCurrentSession({
      itemsReviewed: 0,
      itemsMastered: 0,
      qualities: [],
      startTime: Date.now(),
    });
  }, []);

  const recordReview = useCallback((quality: RecallQuality, isMastered: boolean = false) => {
    setCurrentSession((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        itemsReviewed: prev.itemsReviewed + 1,
        itemsMastered: isMastered ? prev.itemsMastered + 1 : prev.itemsMastered,
        qualities: [...prev.qualities, quality],
      };
    });
  }, []);

  const endSession = useCallback(() => {
    return currentSession;
  }, [currentSession]);

  const resetSession = useCallback(() => {
    setCurrentSession(null);
  }, []);

  return {
    currentSession,
    startSession,
    recordReview,
    endSession,
    resetSession,
  };
}
