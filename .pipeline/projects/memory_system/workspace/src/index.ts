// Core types
export type {
  DifficultyLevel,
  RecallQuality,
  SpacedRepetitionSchedule,
  SpacedRepetitionParams,
  DifficultyConfig,
  DifficultyAdaptationResult,
  ReviewQueueItem,
  SpacedRepetitionStats,
  SpacedRepetitionSessionResult,
} from './types/spacedRepetition';

// Utils
export {
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
} from './utils/spacedRepetition';

// Hooks
export { useSpacedRepetition, useReviewQueue, useReviewSession } from './hooks';

// Main entry point
export { useSpacedRepetition } from './hooks/useSpacedRepetition';
export { useReviewQueue } from './hooks/useReviewQueue';
export { useReviewSession } from './hooks/useReviewSession';
