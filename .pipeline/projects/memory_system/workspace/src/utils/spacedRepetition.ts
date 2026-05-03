import {
  DifficultyLevel,
  DifficultyConfig,
  SpacedRepetitionSchedule,
  SpacedRepetitionParams,
  RecallQuality,
  SpacedRepetitionUpdate,
  DifficultyAdaptationResult,
  SpacedRepetitionStats,
  ReviewQueueItem,
  SpacedRepetitionSessionResult,
  DifficultyAdaptationStrategy,
} from '../types/spacedRepetition';

/**
 * Default spaced repetition parameters (SM-2 inspired)
 */
export const DEFAULT_SPACED_REPETITION_PARAMS: SpacedRepetitionParams = {
  initialInterval: 1, // 1 day
  minimumInterval: 1,
  maximumInterval: 365, // 1 year
  easeFactorDecay: 0.3,
  easeFactorIncrease: 0.15,
  easeFactorMinimum: 1.3,
  targetRetention: 0.9,
};

/**
 * Default difficulty adaptation configuration
 */
export const DEFAULT_DIFFICULTY_ADAPTATION_CONFIG = {
  strategy: 'sm2' as DifficultyAdaptationStrategy,
  params: DEFAULT_SPACED_REPETITION_PARAMS,
  autoAdjust: true,
  adjustmentThreshold: 0.1,
};

/**
 * Map recall quality to SM-2 rating (0-5 scale)
 */
const recallQualityToRating: Record<RecallQuality, number> = {
  again: 0,
  hard: 2,
  good: 3,
  easy: 5,
};

/**
 * Map SM-2 rating to difficulty level
 */
const ratingToDifficulty: Record<number, DifficultyLevel> = {
  0: 'very_hard',
  1: 'hard',
  2: 'hard',
  3: 'medium',
  4: 'easy',
  5: 'very_easy',
};

/**
 * Map difficulty level to base interval multiplier
 */
const difficultyToIntervalMultiplier: Record<DifficultyLevel, number> = {
  very_easy: 2.5,
  easy: 2.0,
  medium: 1.5,
  hard: 1.0,
  very_hard: 0.5,
};

/**
 * Calculate next review interval using SM-2 algorithm
 * @param easeFactor - Current ease factor
 * @param quality - Recall quality rating (0-5)
 * @param currentInterval - Current interval in days
 * @param params - Spaced repetition parameters
 * @returns New interval in days
 */
export function calculateNextInterval(
  easeFactor: number,
  quality: RecallQuality,
  currentInterval: number,
  params: SpacedRepetitionParams = DEFAULT_SPACED_REPETITION_PARAMS
): number {
  const rating = recallQualityToRating[quality];

  if (rating === 0) {
    // Failed - reset to initial interval
    return params.initialInterval;
  }

  // SM-2 interval calculation
  let newInterval: number;

  if (currentInterval === 0) {
    // First successful recall
    newInterval = 1;
  } else if (currentInterval === 1) {
    // Second successful recall
    newInterval = 6;
  } else {
    // Subsequent recalls
    newInterval = Math.round(currentInterval * easeFactor);
  }

  // Apply difficulty multiplier
  const difficultyMultiplier = difficultyToIntervalMultiplier['medium']; // Use medium as base
  newInterval = Math.round(newInterval * difficultyMultiplier);

  // Clamp to min/max
  newInterval = Math.max(params.minimumInterval, Math.min(params.maximumInterval, newInterval));

  return newInterval;
}

/**
 * Update ease factor based on recall quality
 * @param currentEaseFactor - Current ease factor
 * @param quality - Recall quality
 * @param params - Spaced repetition parameters
 * @returns New ease factor
 */
export function updateEaseFactor(
  currentEaseFactor: number,
  quality: RecallQuality,
  params: SpacedRepetitionParams = DEFAULT_SPACED_REPETITION_PARAMS
): number {
  const rating = recallQualityToRating[quality];

  if (rating === 0) {
    // Failed - decrease ease factor
    return Math.max(
      params.easeFactorMinimum,
      currentEaseFactor - params.easeFactorDecay
    );
  }

  // Successful recall - increase ease factor
  return currentEaseFactor + params.easeFactorIncrease;
}

/**
 * Determine new status based on repetition count and interval
 * @param repetition - Current repetition count
 * @param interval - Current interval in days
 * @returns New status
 */
export function determineStatus(repetition: number, interval: number): DifficultyConfig['status'] {
  if (repetition === 0) {
    return 'new';
  }

  if (repetition < 3) {
    return 'learning';
  }

  if (interval >= 21) { // 3 weeks
    return 'mastered';
  }

  return 'review';
}

/**
 * Create initial difficulty config for a new item
 * @param itemId - Unique item identifier
 * @returns Initial difficulty configuration
 */
export function createInitialDifficultyConfig(itemId: string): DifficultyConfig {
  return {
    level: 'medium',
    interval: 0,
    repetition: 0,
    easeFactor: 2.5,
    lastReviewDate: null,
    nextReviewDate: null,
    status: 'new',
  };
}

/**
 * Update difficulty config after a review session
 * @param config - Current difficulty config
 * @param quality - Recall quality
 * @param params - Spaced repetition parameters
 * @returns Updated difficulty config and update result
 */
export function updateDifficultyConfig(
  config: DifficultyConfig,
  quality: RecallQuality,
  params: SpacedRepetitionParams = DEFAULT_SPACED_REPETITION_PARAMS
): { config: DifficultyConfig; update: SpacedRepetitionUpdate } {
  const now = new Date();
  const newEaseFactor = updateEaseFactor(config.easeFactor, quality, params);
  const newInterval = calculateNextInterval(newEaseFactor, quality, config.interval, params);
  const newRepetition = config.repetition + 1;
  const newStatus = determineStatus(newRepetition, newInterval);

  const nextReviewDate = new Date(now);
  nextReviewDate.setDate(now.getDate() + newInterval);

  const update: SpacedRepetitionUpdate = {
    itemId: config.level ? config.level : 'unknown',
    quality,
    newInterval,
    newEaseFactor,
    newStatus,
    nextReviewDate: nextReviewDate.toISOString(),
  };

  const updatedConfig: DifficultyConfig = {
    ...config,
    level: ratingToDifficulty[recallQualityToRating[quality]],
    interval: newInterval,
    repetition: newRepetition,
    easeFactor: newEaseFactor,
    lastReviewDate: now.toISOString(),
    nextReviewDate: nextReviewDate.toISOString(),
    status: newStatus,
  };

  return { config: updatedConfig, update };
}

/**
 * Calculate difficulty adaptation based on performance
 * @param previousDifficulty - Previous difficulty level
 * @param accuracy - Current accuracy (0-1)
 * @param params - Spaced repetition parameters
 * @returns Difficulty adaptation result
 */
export function adaptDifficulty(
  previousDifficulty: DifficultyLevel,
  accuracy: number,
  params: SpacedRepetitionParams = DEFAULT_SPACED_REPETITION_PARAMS
): DifficultyAdaptationResult {
  const difficultyLevels: DifficultyLevel[] = ['very_easy', 'easy', 'medium', 'hard', 'very_hard'];
  const currentIndex = difficultyLevels.indexOf(previousDifficulty);

  let newDifficulty: DifficultyLevel = previousDifficulty;
  let reason = 'No change';
  let confidence = 0.5;

  if (accuracy >= 0.9) {
    // High accuracy - increase difficulty
    if (currentIndex < difficultyLevels.length - 1) {
      newDifficulty = difficultyLevels[currentIndex + 1];
      reason = 'High accuracy suggests item is easier than current difficulty';
      confidence = accuracy;
    }
  } else if (accuracy <= 0.5) {
    // Low accuracy - decrease difficulty
    if (currentIndex > 0) {
      newDifficulty = difficultyLevels[currentIndex - 1];
      reason = 'Low accuracy suggests item is harder than current difficulty';
      confidence = 1 - accuracy;
    }
  } else if (accuracy >= 0.7) {
    // Good accuracy - slight increase
    if (currentIndex < difficultyLevels.length - 1 && Math.random() > 0.7) {
      newDifficulty = difficultyLevels[currentIndex + 1];
      reason = 'Consistent good performance suggests slight difficulty increase';
      confidence = accuracy;
    }
  } else if (accuracy <= 0.8) {
    // Acceptable but not great - slight decrease
    if (currentIndex > 0 && Math.random() > 0.7) {
      newDifficulty = difficultyLevels[currentIndex - 1];
      reason = 'Inconsistent performance suggests slight difficulty decrease';
      confidence = 1 - accuracy;
    }
  }

  return {
    itemId: previousDifficulty,
    previousDifficulty,
    newDifficulty,
    reason,
    confidence,
  };
}

/**
 * Get items due for review
 * @param schedules - All schedules
 * @param now - Current date (default: now)
 * @returns Review queue items
 */
export function getDueItems(
  schedules: Record<string, SpacedRepetitionSchedule>,
  now: Date = new Date()
): ReviewQueueItem[] {
  const dueItems: ReviewQueueItem[] = [];
  const nowISO = now.toISOString();

  Object.entries(schedules).forEach(([itemId, schedule]) => {
    const scheduledDate = new Date(schedule.scheduledDate);
    const daysSinceLastReview = Math.floor(
      (now.getTime() - new Date(schedule.scheduledDate).getTime()) / (1000 * 60 * 60 * 24)
    );

    if (scheduledDate <= now) {
      dueItems.push({
        itemId,
        scheduledDate: schedule.scheduledDate,
        difficulty: schedule.difficulty,
        priority: schedule.priority,
        daysSinceLastReview,
        estimatedTime: estimateReviewTime(schedule.difficulty),
      });
    }
  });

  // Sort by priority (highest first)
  return dueItems.sort((a, b) => b.priority - a.priority);
}

/**
 * Estimate review time based on difficulty
 * @param difficulty - Difficulty level
 * @returns Estimated time in seconds
 */
export function estimateReviewTime(difficulty: DifficultyLevel): number {
  const timeMap: Record<DifficultyLevel, number> = {
    very_easy: 10,
    easy: 15,
    medium: 20,
    hard: 30,
    very_hard: 45,
  };
  return timeMap[difficulty];
}

/**
 * Calculate spaced repetition statistics
 * @param schedules - All schedules
 * @param now - Current date (default: now)
 * @returns Spaced repetition statistics
 */
export function calculateSpacedRepetitionStats(
  schedules: Record<string, SpacedRepetitionSchedule>,
  now: Date = new Date()
): SpacedRepetitionStats {
  const nowISO = now.toISOString();
  const weekFromNow = new Date(now);
  weekFromNow.setDate(now.getDate() + 7);

  let newItems = 0;
  let learningItems = 0;
  let reviewItems = 0;
  let masteredItems = 0;
  let dueToday = 0;
  let upcomingThisWeek = 0;
  let totalRetention = 0;
  let totalInterval = 0;
  let totalReviews = 0;
  let qualityCount: Record<RecallQuality, number> = { again: 0, hard: 0, good: 0, easy: 0 };

  Object.values(schedules).forEach((schedule) => {
    const scheduledDate = new Date(schedule.scheduledDate);

    // Count by status
    if (schedule.priority === 0) newItems++;
    else if (schedule.priority < 3) learningItems++;
    else if (schedule.priority >= 3) reviewItems++;
    else masteredItems++;

    // Count due today
    if (scheduledDate <= now) {
      dueToday++;
    }

    // Count upcoming this week
    if (scheduledDate <= weekFromNow) {
      upcomingThisWeek++;
    }

    // Calculate averages
    totalRetention += schedule.priority; // Simplified
    totalInterval += schedule.priority;
    totalReviews++;

    // Track quality (simplified)
    if (schedule.priority > 3) qualityCount.easy++;
    else if (schedule.priority > 2) qualityCount.good++;
    else if (schedule.priority > 1) qualityCount.hard++;
    else qualityCount.again++;
  });

  const averageRetention = totalReviews > 0 ? totalRetention / totalReviews : 0;
  const averageInterval = totalReviews > 0 ? totalInterval / totalReviews : 0;

  // Calculate average quality
  let averageQuality: RecallQuality = 'good';
  if (qualityCount.again > qualityCount.good + qualityCount.easy) {
    averageQuality = 'again';
  } else if (qualityCount.hard > qualityCount.good + qualityCount.easy) {
    averageQuality = 'hard';
  } else if (qualityCount.easy > qualityCount.good) {
    averageQuality = 'easy';
  }

  return {
    totalItems: Object.keys(schedules).length,
    newItems,
    learningItems,
    reviewItems,
    masteredItems,
    dueToday,
    upcomingThisWeek,
    averageRetention,
    averageInterval,
    totalReviews,
    averageQuality,
  };
}

/**
 * Create a spaced repetition session result
 * @param itemsReviewed - Number of items reviewed
 * @param itemsMastered - Number of items mastered
 * @param qualities - Array of recall qualities
 * @param timeSpent - Time spent in seconds
 * @returns Session result
 */
export function createSessionResult(
  itemsReviewed: number,
  itemsMastered: number,
  qualities: RecallQuality[],
  timeSpent: number
): SpacedRepetitionSessionResult {
  // Calculate average quality
  let averageQuality: RecallQuality = 'good';
  const qualityCount: Record<RecallQuality, number> = { again: 0, hard: 0, good: 0, easy: 0 };

  qualities.forEach((quality) => {
    qualityCount[quality]++;
  });

  if (qualityCount.again > qualityCount.good + qualityCount.easy) {
    averageQuality = 'again';
  } else if (qualityCount.hard > qualityCount.good + qualityCount.easy) {
    averageQuality = 'hard';
  } else if (qualityCount.easy > qualityCount.good) {
    averageQuality = 'easy';
  }

  // Calculate retention rate
  const retentionRate = itemsMastered / itemsReviewed;

  // Generate improvements
  const improvements: string[] = [];
  if (averageQuality === 'easy') {
    improvements.push('Consider increasing difficulty for mastered items');
  } else if (averageQuality === 'again') {
    improvements.push('Focus on items rated "again" in next session');
  } else if (timeSpent > itemsReviewed * 30) {
    improvements.push('Review sessions are taking longer than expected');
  }

  return {
    sessionId: `session-${Date.now()}`,
    timestamp: new Date().toISOString(),
    itemsReviewed,
    itemsMastered,
    averageQuality,
    retentionRate,
    timeSpent,
    improvements,
  };
}

/**
 * Get items by status
 * @param schedules - All schedules
 * @param status - Status to filter by
 * @returns Items matching the status
 */
export function getItemsByStatus(
  schedules: Record<string, SpacedRepetitionSchedule>,
  status: DifficultyConfig['status']
): string[] {
  return Object.entries(schedules)
    .filter(([_, schedule]) => {
      // Map priority to status
      if (status === 'new' && schedule.priority === 0) return true;
      if (status === 'learning' && schedule.priority > 0 && schedule.priority < 3) return true;
      if (status === 'review' && schedule.priority >= 3) return true;
      if (status === 'mastered' && schedule.priority > 5) return true;
      return false;
    })
    .map(([itemId, _]) => itemId);
}

/**
 * Get items due within a time range
 * @param schedules - All schedules
 * @param startDate - Start date
 * @param endDate - End date
 * @returns Items due within the range
 */
export function getItemsDueInRange(
  schedules: Record<string, SpacedRepetitionSchedule>,
  startDate: Date,
  endDate: Date
): ReviewQueueItem[] {
  const dueItems: ReviewQueueItem[] = [];

  Object.entries(schedules).forEach(([itemId, schedule]) => {
    const scheduledDate = new Date(schedule.scheduledDate);
    if (scheduledDate >= startDate && scheduledDate <= endDate) {
      dueItems.push({
        itemId,
        scheduledDate: schedule.scheduledDate,
        difficulty: schedule.difficulty,
        priority: schedule.priority,
        daysSinceLastReview: Math.floor(
          (new Date().getTime() - scheduledDate.getTime()) / (1000 * 60 * 60 * 24)
        ),
        estimatedTime: estimateReviewTime(schedule.difficulty),
      });
    }
  });

  return dueItems.sort((a, b) => a.scheduledDate.localeCompare(b.scheduledDate));
}
