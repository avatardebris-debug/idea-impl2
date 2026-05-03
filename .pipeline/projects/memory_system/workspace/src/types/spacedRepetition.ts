/**
 * Spaced repetition and difficulty adaptation types
 */

/**
 * Difficulty levels for memory exercises
 */
export type DifficultyLevel = 'very_easy' | 'easy' | 'medium' | 'hard' | 'very_hard';

/**
 * Difficulty configuration for a specific item
 */
export interface DifficultyConfig {
  level: DifficultyLevel;
  interval: number; // days until next review
  repetition: number; // current repetition count
  easeFactor: number; // SM-2 ease factor (2.5 is baseline)
  lastReviewDate: string | null;
  nextReviewDate: string | null;
  status: 'new' | 'learning' | 'review' | 'mastered';
}

/**
 * Spaced repetition schedule for an item
 */
export interface SpacedRepetitionSchedule {
  itemId: string;
  scheduledDate: string;
  difficulty: DifficultyLevel;
  priority: number; // higher = more urgent
  reason: string;
}

/**
 * Spaced repetition system state
 */
export interface SpacedRepetitionState {
  schedules: Record<string, SpacedRepetitionSchedule>;
  difficultyConfigs: Record<string, DifficultyConfig>;
  lastUpdated: string;
}

/**
 * Spaced repetition algorithm parameters
 */
export interface SpacedRepetitionParams {
  initialInterval: number; // initial interval in days
  minimumInterval: number; // minimum interval in days
  maximumInterval: number; // maximum interval in days
  easeFactorDecay: number; // how much ease factor decreases on failure
  easeFactorIncrease: number; // how much ease factor increases on success
  easeFactorMinimum: number; // minimum ease factor
  targetRetention: number; // target retention rate (0-1)
}

/**
 * Recall quality rating for spaced repetition
 */
export type RecallQuality = 'again' | 'hard' | 'good' | 'easy';

/**
 * Spaced repetition update result
 */
export interface SpacedRepetitionUpdate {
  itemId: string;
  quality: RecallQuality;
  newInterval: number;
  newEaseFactor: number;
  newStatus: DifficultyConfig['status'];
  nextReviewDate: string;
}

/**
 * Difficulty adaptation strategy
 */
export type DifficultyAdaptationStrategy = 'sm2' | 'supermemo2' | 'fsrs' | 'custom';

/**
 * Difficulty adaptation configuration
 */
export interface DifficultyAdaptationConfig {
  strategy: DifficultyAdaptationStrategy;
  params: SpacedRepetitionParams;
  autoAdjust: boolean;
  adjustmentThreshold: number; // minimum accuracy change to trigger adjustment
}

/**
 * Difficulty adaptation result
 */
export interface DifficultyAdaptationResult {
  itemId: string;
  previousDifficulty: DifficultyLevel;
  newDifficulty: DifficultyLevel;
  reason: string;
  confidence: number;
}

/**
 * Spaced repetition statistics
 */
export interface SpacedRepetitionStats {
  totalItems: number;
  newItems: number;
  learningItems: number;
  reviewItems: number;
  masteredItems: number;
  dueToday: number;
  upcomingThisWeek: number;
  averageRetention: number;
  averageInterval: number;
  totalReviews: number;
  averageQuality: RecallQuality;
}

/**
 * Review queue item
 */
export interface ReviewQueueItem {
  itemId: string;
  scheduledDate: string;
  difficulty: DifficultyLevel;
  priority: number;
  daysSinceLastReview: number;
  estimatedTime: number; // seconds
}

/**
 * Spaced repetition session result
 */
export interface SpacedRepetitionSessionResult {
  sessionId: string;
  timestamp: string;
  itemsReviewed: number;
  itemsMastered: number;
  averageQuality: RecallQuality;
  retentionRate: number;
  timeSpent: number;
  improvements: string[];
}
