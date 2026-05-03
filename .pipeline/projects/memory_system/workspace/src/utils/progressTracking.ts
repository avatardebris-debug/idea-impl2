/**
 * Progress tracking utilities for memory palace sessions
 */

export interface RecallAttempt {
  id: string;
  palaceId: string;
  timestamp: string;
  items: string[];
  accuracy: number;
  duration: number;
  confidence: number;
  errors: Array<{
    errorType: 'omission' | 'substitution' | 'transposition' | 'insertion';
    positionExpected: number;
    positionRecalled: number | undefined;
    expected: string;
    recalled: string | undefined;
  }>;
}

export interface PalaceStats {
  sessionHistory: Array<{
    startTime: string;
    endTime?: string;
    accuracy: number;
    duration: number;
    totalItems: number;
    correctItems: number;
    confidence: number;
  }>;
  totalSessions: number;
  averageAccuracy: number;
  averageDuration: number;
  lastSessionDate: string | null;
}

/**
 * Generate a unique ID for a recall attempt
 */
export function generateAttemptId(): string {
  return `attempt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Calculate accuracy for a recall attempt
 */
export function calculateAccuracy(
  expectedItems: string[],
  recalledItems: string[],
  positionSensitive: boolean = true
): number {
  if (expectedItems.length === 0) {
    return 0;
  }

  let correctCount = 0;

  if (positionSensitive) {
    // Position-sensitive comparison
    for (let i = 0; i < expectedItems.length; i++) {
      if (i < recalledItems.length && recalledItems[i] === expectedItems[i]) {
        correctCount++;
      }
    }
  } else {
    // Position-insensitive comparison
    const recalledSet = new Set(recalledItems);
    for (const item of expectedItems) {
      if (recalledSet.has(item)) {
        correctCount++;
      }
    }
  }

  return correctCount / expectedItems.length;
}

/**
 * Detect errors in a recall attempt
 */
export function detectErrors(
  expectedItems: string[],
  recalledItems: string[]
): Array<{
  errorType: 'omission' | 'substitution' | 'transposition' | 'insertion';
  positionExpected: number;
  positionRecalled: number | undefined;
  expected: string;
  recalled: string | undefined;
}> {
  const errors: Array<{
    errorType: 'omission' | 'substitution' | 'transposition' | 'insertion';
    positionExpected: number;
    positionRecalled: number | undefined;
    expected: string;
    recalled: string | undefined;
  }> = [];

  const expectedSet = new Set(expectedItems);
  const recalledSet = new Set(recalledItems);

  // Check for omissions and substitutions
  for (let i = 0; i < expectedItems.length; i++) {
    const expectedItem = expectedItems[i];
    const recalledItem = recalledItems[i];

    if (!recalledItem) {
      // Omission
      errors.push({
        errorType: 'omission',
        positionExpected: i,
        positionRecalled: undefined,
        expected: expectedItem,
        recalled: undefined,
      });
    } else if (recalledItem !== expectedItem) {
      // Check if it's a substitution or transposition
      const expectedPositionInRecalled = recalledItems.indexOf(expectedItem);
      const recalledPositionInExpected = expectedItems.indexOf(recalledItem);

      if (expectedPositionInRecalled !== -1 && expectedPositionInRecalled !== i) {
        // Transposition - item was recalled but in wrong position
        errors.push({
          errorType: 'transposition',
          positionExpected: i,
          positionRecalled: expectedPositionInRecalled,
          expected: expectedItem,
          recalled: recalledItem,
        });
      } else {
        // Substitution - wrong item at this position
        errors.push({
          errorType: 'substitution',
          positionExpected: i,
          positionRecalled: i,
          expected: expectedItem,
          recalled: recalledItem,
        });
      }
    }
  }

  // Check for insertions (extra items recalled)
  for (let i = expectedItems.length; i < recalledItems.length; i++) {
    errors.push({
      errorType: 'insertion',
      positionExpected: undefined,
      positionRecalled: i,
      expected: undefined,
      recalled: recalledItems[i],
    });
  }

  return errors;
}

/**
 * Create a new recall attempt record
 */
export function createRecallAttempt(
  palaceId: string,
  items: string[],
  recalledItems: string[],
  duration: number,
  confidence: number
): RecallAttempt {
  const accuracy = calculateAccuracy(items, recalledItems);
  const errors = detectErrors(items, recalledItems);

  return {
    id: generateAttemptId(),
    palaceId,
    timestamp: new Date().toISOString(),
    items,
    recalledItems,
    accuracy,
    duration,
    confidence,
    errors,
  };
}

/**
 * Calculate palace statistics from session history
 */
export function calculatePalaceStats(
  sessionHistory: Array<{
    startTime: string;
    endTime?: string;
    accuracy: number;
    duration: number;
    totalItems: number;
    correctItems: number;
    confidence: number;
  }>
): PalaceStats {
  if (sessionHistory.length === 0) {
    return {
      sessionHistory: [],
      totalSessions: 0,
      averageAccuracy: 0,
      averageDuration: 0,
      lastSessionDate: null,
    };
  }

  const totalAccuracy = sessionHistory.reduce((sum, session) => sum + session.accuracy, 0);
  const totalDuration = sessionHistory.reduce((sum, session) => sum + session.duration, 0);
  const sortedHistory = [...sessionHistory].sort(
    (a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime()
  );

  return {
    sessionHistory: sortedHistory,
    totalSessions: sessionHistory.length,
    averageAccuracy: totalAccuracy / sessionHistory.length,
    averageDuration: totalDuration / sessionHistory.length,
    lastSessionDate: sortedHistory[0].startTime,
  };
}

/**
 * Get palace statistics from storage
 */
export function getPalaceStats(palaceId: string): PalaceStats | null {
  try {
    const stored = localStorage.getItem(`palace_stats_${palaceId}`);
    if (stored) {
      return JSON.parse(stored);
    }
    return null;
  } catch (error) {
    console.error('Error getting palace stats:', error);
    return null;
  }
}

/**
 * Save palace statistics to storage
 */
export function savePalaceStats(palaceId: string, stats: PalaceStats): void {
  try {
    localStorage.setItem(`palace_stats_${palaceId}`, JSON.stringify(stats));
  } catch (error) {
    console.error('Error saving palace stats:', error);
  }
}

/**
 * Add a new session to palace statistics
 */
export function addSessionToStats(
  palaceId: string,
  session: {
    startTime: string;
    endTime?: string;
    accuracy: number;
    duration: number;
    totalItems: number;
    correctItems: number;
    confidence: number;
  }
): PalaceStats {
  const currentStats = getPalaceStats(palaceId) || {
    sessionHistory: [],
    totalSessions: 0,
    averageAccuracy: 0,
    averageDuration: 0,
    lastSessionDate: null,
  };

  const updatedStats = {
    ...currentStats,
    sessionHistory: [...currentStats.sessionHistory, session],
    totalSessions: currentStats.totalSessions + 1,
    averageAccuracy:
      (currentStats.averageAccuracy * currentStats.totalSessions + session.accuracy) /
      (currentStats.totalSessions + 1),
    averageDuration:
      (currentStats.averageDuration * currentStats.totalSessions + session.duration) /
      (currentStats.totalSessions + 1),
    lastSessionDate: session.startTime,
  };

  savePalaceStats(palaceId, updatedStats);
  return updatedStats;
}

/**
 * Get recent sessions for a palace
 */
export function getRecentSessions(
  palaceId: string,
  limit: number = 10
): Array<{
  startTime: string;
  endTime?: string;
  accuracy: number;
  duration: number;
  totalItems: number;
  correctItems: number;
  confidence: number;
}> {
  const stats = getPalaceStats(palaceId);
  if (!stats) {
    return [];
  }

  return stats.sessionHistory.slice(0, limit);
}

/**
 * Get accuracy trend for a palace
 */
export function getAccuracyTrend(palaceId: string, windowSize: number = 5): {
  trend: 'improving' | 'declining' | 'stable';
  averageAccuracy: number;
} {
  const stats = getPalaceStats(palaceId);
  if (!stats || stats.sessionHistory.length < 2) {
    return { trend: 'stable', averageAccuracy: 0 };
  }

  const recentSessions = stats.sessionHistory.slice(-windowSize);
  const firstHalf = recentSessions.slice(0, Math.floor(recentSessions.length / 2));
  const secondHalf = recentSessions.slice(Math.floor(recentSessions.length / 2));

  const firstHalfAvg =
    firstHalf.reduce((sum, s) => sum + s.accuracy, 0) / firstHalf.length;
  const secondHalfAvg =
    secondHalf.reduce((sum, s) => sum + s.accuracy, 0) / secondHalf.length;

  const averageAccuracy = recentSessions.reduce((sum, s) => sum + s.accuracy, 0) /
    recentSessions.length;

  if (secondHalfAvg > firstHalfAvg + 0.1) {
    return { trend: 'improving', averageAccuracy };
  } else if (firstHalfAvg > secondHalfAvg + 0.1) {
    return { trend: 'declining', averageAccuracy };
  } else {
    return { trend: 'stable', averageAccuracy };
  }
}
