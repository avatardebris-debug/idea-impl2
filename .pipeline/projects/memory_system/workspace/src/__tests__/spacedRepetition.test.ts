import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import * as spacedRepetitionUtils from '../utils/spacedRepetition';
import {
  DEFAULT_SPACED_REPETITION_PARAMS,
  calculateNextInterval,
  updateEaseFactor,
  determineStatus,
  createInitialDifficultyConfig,
  updateDifficultyConfig,
  adaptDifficulty,
  getDueItems,
  calculateSpacedRepetitionStats,
  createSessionResult,
  getItemsByStatus,
  getItemsDueInRange,
  estimateReviewTime,
} from '../utils/spacedRepetition';
import {
  useSpacedRepetition,
  useReviewQueue,
  useReviewSession,
} from '../hooks/useSpacedRepetition';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('Spaced Repetition Utils', () => {
  describe('calculateNextInterval', () => {
    it('returns initial interval for first successful recall', () => {
      const result = calculateNextInterval(2.5, 'good', 0, DEFAULT_SPACED_REPETITION_PARAMS);
      expect(result).toBe(1);
    });

    it('returns 6 days for second successful recall', () => {
      const result = calculateNextInterval(2.5, 'good', 1, DEFAULT_SPACED_REPETITION_PARAMS);
      expect(result).toBe(6);
    });

    it('calculates interval based on ease factor for subsequent recalls', () => {
      const result = calculateNextInterval(2.5, 'good', 6, DEFAULT_SPACED_REPETITION_PARAMS);
      expect(result).toBeGreaterThan(6);
    });

    it('resets to initial interval on failure', () => {
      const result = calculateNextInterval(2.5, 'again', 10, DEFAULT_SPACED_REPETITION_PARAMS);
      expect(result).toBe(DEFAULT_SPACED_REPETITION_PARAMS.initialInterval);
    });

    it('clamps interval to minimum', () => {
      const result = calculateNextInterval(1.0, 'good', 0.5, {
        ...DEFAULT_SPACED_REPETITION_PARAMS,
        minimumInterval: 1,
      });
      expect(result).toBe(1);
    });

    it('clamps interval to maximum', () => {
      const result = calculateNextInterval(5.0, 'easy', 100, {
        ...DEFAULT_SPACED_REPETITION_PARAMS,
        maximumInterval: 365,
      });
      expect(result).toBe(365);
    });
  });

  describe('updateEaseFactor', () => {
    it('decreases ease factor on failure', () => {
      const result = updateEaseFactor(2.5, 'again', DEFAULT_SPACED_REPETITION_PARAMS);
      expect(result).toBeLessThan(2.5);
    });

    it('increases ease factor on success', () => {
      const result = updateEaseFactor(2.5, 'good', DEFAULT_SPACED_REPETITION_PARAMS);
      expect(result).toBeGreaterThan(2.5);
    });

    it('increases ease factor more on easy rating', () => {
      const result = updateEaseFactor(2.5, 'easy', DEFAULT_SPACED_REPETITION_PARAMS);
      expect(result).toBeGreaterThan(2.5);
    });

    it('clamps ease factor to minimum', () => {
      const result = updateEaseFactor(1.3, 'again', DEFAULT_SPACED_REPETITION_PARAMS);
      expect(result).toBeGreaterThanOrEqual(1.3);
    });

    it('clamps ease factor to maximum', () => {
      const result = updateEaseFactor(2.5, 'easy', {
        ...DEFAULT_SPACED_REPETITION_PARAMS,
        maximumEaseFactor: 2.5,
      });
      expect(result).toBeLessThanOrEqual(2.5);
    });
  });

  describe('determineStatus', () => {
    it('returns new for zero repetitions', () => {
      expect(determineStatus(0)).toBe('new');
    });

    it('returns learning for low repetitions', () => {
      expect(determineStatus(1)).toBe('learning');
      expect(determineStatus(2)).toBe('learning');
      expect(determineStatus(3)).toBe('learning');
    });

    it('returns review for moderate repetitions', () => {
      expect(determineStatus(4)).toBe('review');
      expect(determineStatus(5)).toBe('review');
      expect(determineStatus(10)).toBe('review');
    });

    it('returns mastered for high repetitions', () => {
      expect(determineStatus(20)).toBe('mastered');
      expect(determineStatus(50)).toBe('mastered');
    });
  });

  describe('createInitialDifficultyConfig', () => {
    it('creates initial config with correct defaults', () => {
      const config = createInitialDifficultyConfig('item-1');
      expect(config.level).toBe('medium');
      expect(config.interval).toBe(0);
      expect(config.repetition).toBe(0);
      expect(config.easeFactor).toBe(2.5);
      expect(config.status).toBe('new');
      expect(config.lastReviewDate).toBeNull();
      expect(config.nextReviewDate).toBeNull();
    });
  });

  describe('updateDifficultyConfig', () => {
    it('updates config after successful review', () => {
      const config = createInitialDifficultyConfig('item-1');
      const { config: updatedConfig, update } = updateDifficultyConfig(config, 'good');

      expect(updatedConfig.repetition).toBe(1);
      expect(updatedConfig.interval).toBeGreaterThan(0);
      expect(updatedConfig.easeFactor).toBeGreaterThan(2.5);
      expect(updatedConfig.lastReviewDate).toBeDefined();
      expect(updatedConfig.nextReviewDate).toBeDefined();
      expect(update.quality).toBe('good');
    });

    it('updates config after failed review', () => {
      const config = createInitialDifficultyConfig('item-1');
      const { config: updatedConfig, update } = updateDifficultyConfig(config, 'again');

      expect(updatedConfig.repetition).toBe(1);
      expect(updatedConfig.easeFactor).toBeLessThan(2.5);
      expect(update.quality).toBe('again');
    });
  });

  describe('adaptDifficulty', () => {
    it('increases difficulty for high accuracy', () => {
      const result = adaptDifficulty('medium', 0.95);
      expect(result.newDifficulty).not.toBe('medium');
      expect(result.confidence).toBeGreaterThan(0.9);
    });

    it('decreases difficulty for low accuracy', () => {
      const result = adaptDifficulty('medium', 0.4);
      expect(result.newDifficulty).not.toBe('medium');
      expect(result.confidence).toBeGreaterThan(0.5);
    });

    it('keeps difficulty same for moderate accuracy', () => {
      const result = adaptDifficulty('medium', 0.7);
      expect(result.newDifficulty).toBe('medium');
      expect(result.reason).toBe('No change');
    });
  });

  describe('getDueItems', () => {
    it('returns items scheduled for today or past', () => {
      const schedules = {
        'item-1': {
          itemId: 'item-1',
          scheduledDate: new Date(Date.now() - 86400000).toISOString(), // yesterday
          difficulty: 'medium',
          priority: 3,
          reason: 'Test',
        },
        'item-2': {
          itemId: 'item-2',
          scheduledDate: new Date().toISOString(), // today
          difficulty: 'hard',
          priority: 5,
          reason: 'Test',
        },
        'item-3': {
          itemId: 'item-3',
          scheduledDate: new Date(Date.now() + 86400000).toISOString(), // tomorrow
          difficulty: 'easy',
          priority: 1,
          reason: 'Test',
        },
      };

      const dueItems = getDueItems(schedules);
      expect(dueItems).toHaveLength(2);
      expect(dueItems.map((item) => item.itemId)).toContain('item-1');
      expect(dueItems.map((item) => item.itemId)).toContain('item-2');
    });

    it('sorts by priority (highest first)', () => {
      const schedules = {
        'item-1': {
          itemId: 'item-1',
          scheduledDate: new Date().toISOString(),
          difficulty: 'medium',
          priority: 3,
          reason: 'Test',
        },
        'item-2': {
          itemId: 'item-2',
          scheduledDate: new Date().toISOString(),
          difficulty: 'hard',
          priority: 5,
          reason: 'Test',
        },
      };

      const dueItems = getDueItems(schedules);
      expect(dueItems[0].itemId).toBe('item-2');
      expect(dueItems[1].itemId).toBe('item-1');
    });

    it('returns empty array for no due items', () => {
      const schedules = {
        'item-1': {
          itemId: 'item-1',
          scheduledDate: new Date(Date.now() + 86400000).toISOString(), // tomorrow
          difficulty: 'medium',
          priority: 3,
          reason: 'Test',
        },
      };

      const dueItems = getDueItems(schedules);
      expect(dueItems).toHaveLength(0);
    });
  });

  describe('estimateReviewTime', () => {
    it('returns correct time for very_easy', () => {
      expect(estimateReviewTime('very_easy')).toBe(10);
    });

    it('returns correct time for easy', () => {
      expect(estimateReviewTime('easy')).toBe(15);
    });

    it('returns correct time for medium', () => {
      expect(estimateReviewTime('medium')).toBe(20);
    });

    it('returns correct time for hard', () => {
      expect(estimateReviewTime('hard')).toBe(30);
    });

    it('returns correct time for very_hard', () => {
      expect(estimateReviewTime('very_hard')).toBe(45);
    });
  });

  describe('calculateSpacedRepetitionStats', () => {
    it('calculates correct total items', () => {
      const schedules = {
        'item-1': {
          itemId: 'item-1',
          scheduledDate: new Date().toISOString(),
          difficulty: 'medium',
          priority: 3,
          reason: 'Test',
        },
        'item-2': {
          itemId: 'item-2',
          scheduledDate: new Date().toISOString(),
          difficulty: 'hard',
          priority: 5,
          reason: 'Test',
        },
      };

      const stats = calculateSpacedRepetitionStats(schedules);
      expect(stats.totalItems).toBe(2);
    });

    it('counts due today correctly', () => {
      const schedules = {
        'item-1': {
          itemId: 'item-1',
          scheduledDate: new Date().toISOString(),
          difficulty: 'medium',
          priority: 3,
          reason: 'Test',
        },
      };

      const stats = calculateSpacedRepetitionStats(schedules);
      expect(stats.dueToday).toBe(1);
    });

    it('returns zero stats for empty schedules', () => {
      const stats = calculateSpacedRepetitionStats({});
      expect(stats.totalItems).toBe(0);
      expect(stats.dueToday).toBe(0);
      expect(stats.averageRetention).toBe(0);
    });
  });

  describe('createSessionResult', () => {
    it('creates correct session result', () => {
      const result = createSessionResult(10, 8, ['good', 'good', 'easy', 'good'], 180);

      expect(result.itemsReviewed).toBe(10);
      expect(result.itemsMastered).toBe(8);
      expect(result.retentionRate).toBe(0.8);
      expect(result.timeSpent).toBe(180);
      expect(result.sessionId).toBeDefined();
      expect(result.timestamp).toBeDefined();
    });

    it('calculates average quality correctly', () => {
      const result = createSessionResult(10, 5, ['easy', 'easy', 'good', 'good'], 120);
      expect(result.averageQuality).toBe('easy');
    });

    it('generates improvements', () => {
      const result = createSessionResult(10, 10, ['easy', 'easy', 'easy'], 300);
      expect(result.improvements).toContainEqual(
        expect.stringContaining('Consider increasing difficulty')
      );
    });
  });

  describe('getItemsByStatus', () => {
    it('returns items by status', () => {
      const schedules = {
        'item-1': {
          itemId: 'item-1',
          scheduledDate: new Date().toISOString(),
          difficulty: 'medium',
          priority: 0,
          reason: 'Test',
        },
        'item-2': {
          itemId: 'item-2',
          scheduledDate: new Date().toISOString(),
          difficulty: 'hard',
          priority: 2,
          reason: 'Test',
        },
        'item-3': {
          itemId: 'item-3',
          scheduledDate: new Date().toISOString(),
          difficulty: 'easy',
          priority: 5,
          reason: 'Test',
        },
      };

      const newItems = getItemsByStatus(schedules, 'new');
      expect(newItems).toContain('item-1');

      const reviewItems = getItemsByStatus(schedules, 'review');
      expect(reviewItems).toContain('item-3');
    });
  });

  describe('getItemsDueInRange', () => {
    it('returns items due within date range', () => {
      const schedules = {
        'item-1': {
          itemId: 'item-1',
          scheduledDate: new Date().toISOString(),
          difficulty: 'medium',
          priority: 3,
          reason: 'Test',
        },
        'item-2': {
          itemId: 'item-2',
          scheduledDate: new Date(Date.now() + 86400000).toISOString(), // tomorrow
          difficulty: 'hard',
          priority: 5,
          reason: 'Test',
        },
      };

      const startDate = new Date();
      const endDate = new Date(Date.now() + 172800000); // 2 days from now

      const dueItems = getItemsDueInRange(schedules, startDate, endDate);
      expect(dueItems).toHaveLength(2);
    });

    it('returns empty array for no items in range', () => {
      const schedules = {
        'item-1': {
          itemId: 'item-1',
          scheduledDate: new Date(Date.now() + 864000000).toISOString(), // 10 days from now
          difficulty: 'medium',
          priority: 3,
          reason: 'Test',
        },
      };

      const startDate = new Date();
      const endDate = new Date(Date.now() + 86400000); // 1 day from now

      const dueItems = getItemsDueInRange(schedules, startDate, endDate);
      expect(dueItems).toHaveLength(0);
    });
  });
});

describe('useSpacedRepetition Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useSpacedRepetition());

    expect(result.current.schedules).toEqual({});
    expect(result.current.difficultyConfigs).toEqual({});
    expect(result.current.isLoading).toBe(false);
  });

  it('loads data from localStorage', () => {
    localStorageMock.getItem
      .mockReturnValueOnce(JSON.stringify({ 'item-1': { scheduledDate: new Date().toISOString() } }))
      .mockReturnValueOnce(JSON.stringify({ 'item-1': { level: 'medium' } }))
      .mockReturnValueOnce('[]');

    const { result } = renderHook(() => useSpacedRepetition());

    expect(result.current.schedules).toEqual({ 'item-1': { scheduledDate: expect.any(String) } });
  });

  it('saves data to localStorage on change', () => {
    const { result } = renderHook(() => useSpacedRepetition());

    result.current.addItem('item-1');

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'spacedRepetitionSchedules',
      expect.any(String)
    );
  });

  it('adds a new item', () => {
    const { result } = renderHook(() => useSpacedRepetition());

    result.current.addItem('item-1');

    expect(result.current.schedules['item-1']).toBeDefined();
    expect(result.current.difficultyConfigs['item-1']).toBeDefined();
  });

  it('removes an item', () => {
    const { result } = renderHook(() => useSpacedRepetition());

    result.current.addItem('item-1');
    result.current.removeItem('item-1');

    expect(result.current.schedules['item-1']).toBeUndefined();
  });

  it('reviews an item', () => {
    const { result } = renderHook(() => useSpacedRepetition());

    result.current.addItem('item-1');
    result.current.reviewItem('item-1', 'good');

    expect(result.current.schedules['item-1'].scheduledDate).not.toBe(
      result.current.schedules['item-1'].scheduledDate
    );
  });

  it('gets due items', () => {
    const { result } = renderHook(() => useSpacedRepetition());

    result.current.addItem('item-1', { scheduledDate: new Date().toISOString() });

    const dueItems = result.current.getDueItemsForReview();
    expect(dueItems).toHaveLength(1);
  });

  it('completes a session', () => {
    const { result } = renderHook(() => useSpacedRepetition());

    result.current.completeSession(10, 8, ['good', 'good', 'easy'], 180);

    expect(result.current.sessionResults).toHaveLength(1);
    expect(result.current.sessionResults[0].itemsReviewed).toBe(10);
  });

  it('adapts difficulty', () => {
    const { result } = renderHook(() => useSpacedRepetition());

    result.current.addItem('item-1');
    const adaptation = result.current.adaptDifficulty('item-1', 0.95);

    expect(adaptation).toBeDefined();
    expect(adaptation?.newDifficulty).not.toBe('medium');
  });

  it('resets an item', () => {
    const { result } = renderHook(() => useSpacedRepetition());

    result.current.addItem('item-1');
    result.current.reviewItem('item-1', 'good');
    result.current.resetItem('item-1');

    expect(result.current.schedules['item-1'].priority).toBe(0);
  });

  it('clears all data', () => {
    const { result } = renderHook(() => useSpacedRepetition());

    result.current.addItem('item-1');
    result.current.clearAll();

    expect(result.current.schedules).toEqual({});
    expect(result.current.difficultyConfigs).toEqual({});
  });
});

describe('useReviewQueue Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  it('initializes with empty queue', () => {
    const { result } = renderHook(() => useReviewQueue());

    expect(result.current.queue).toEqual([]);
    expect(result.current.totalDue).toBe(0);
  });

  it('loads due items from localStorage', () => {
    localStorageMock.getItem.mockReturnValueOnce(
      JSON.stringify({
        'item-1': {
          itemId: 'item-1',
          scheduledDate: new Date().toISOString(),
          difficulty: 'medium',
          priority: 3,
          reason: 'Test',
        },
      })
    );

    const { result } = renderHook(() => useReviewQueue());

    expect(result.current.queue).toHaveLength(1);
  });

  it('calculates estimated time', () => {
    localStorageMock.getItem.mockReturnValueOnce(
      JSON.stringify({
        'item-1': {
          itemId: 'item-1',
          scheduledDate: new Date().toISOString(),
          difficulty: 'medium',
          priority: 3,
          reason: 'Test',
        },
      })
    );

    const { result } = renderHook(() => useReviewQueue());

    expect(result.current.estimatedTime).toBeGreaterThan(0);
  });
});

describe('useReviewSession Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with no session', () => {
    const { result } = renderHook(() => useReviewSession());

    expect(result.current.currentSession).toBeNull();
  });

  it('starts a session', () => {
    const { result } = renderHook(() => useReviewSession());

    result.current.startSession();

    expect(result.current.currentSession).toBeDefined();
    expect(result.current.currentSession?.itemsReviewed).toBe(0);
  });

  it('records a review', () => {
    const { result } = renderHook(() => useReviewSession());

    result.current.startSession();
    result.current.recordReview('good');

    expect(result.current.currentSession?.itemsReviewed).toBe(1);
    expect(result.current.currentSession?.qualities).toEqual(['good']);
  });

  it('ends a session', () => {
    const { result } = renderHook(() => useReviewSession());

    result.current.startSession();
    result.current.recordReview('good');
    const session = result.current.endSession();

    expect(session?.itemsReviewed).toBe(1);
  });

  it('resets a session', () => {
    const { result } = renderHook(() => useReviewSession());

    result.current.startSession();
    result.current.recordReview('good');
    result.current.resetSession();

    expect(result.current.currentSession).toBeNull();
  });
});
