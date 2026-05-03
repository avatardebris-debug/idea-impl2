/**
 * Utility for analyzing accuracy metrics and error patterns
 */

import { PalaceStats, RecallAttempt } from './progressTracking';

export interface CurrentMetrics {
  accuracy: number;
  recallSpeed: number;
  confidence: number;
}

export interface ErrorAnalysis {
  errorType: 'omission' | 'substitution' | 'transposition' | 'insertion';
  positionExpected: number;
  positionRecalled: number | undefined;
  expected: string;
  recalled: string | undefined;
}

export interface LearningPattern {
  label: string;
  value: string;
}

export interface LearningCurveData {
  sessionNumber: number;
  accuracy: number;
  timestamp: string;
}

export interface Recommendations {
  general: string[];
  errorSpecific: {
    errorType: string;
    suggestions: string[];
  }[];
}

/**
 * Calculate current metrics from recent recall attempts
 */
export function calculateCurrentMetrics(
  attempts: RecallAttempt[],
  windowSize: number = 5
): CurrentMetrics | null {
  if (attempts.length === 0) {
    return null;
  }

  const recentAttempts = attempts.slice(-windowSize);
  const totalAccuracy = recentAttempts.reduce((sum, attempt) => sum + attempt.accuracy, 0);
  const totalDuration = recentAttempts.reduce((sum, attempt) => sum + attempt.duration, 0);
  const totalConfidence = recentAttempts.reduce((sum, attempt) => sum + attempt.confidence, 0);

  return {
    accuracy: totalAccuracy / recentAttempts.length,
    recallSpeed: totalDuration / recentAttempts.length,
    confidence: totalConfidence / recentAttempts.length,
  };
}

/**
 * Analyze errors from recall attempts
 */
export function analyzeErrors(
  attempts: RecallAttempt[]
): {
  errorAnalysis: ErrorAnalysis[];
  errorCounts: Record<string, number>;
} {
  const errorAnalysis: ErrorAnalysis[] = [];
  const errorCounts: Record<string, number> = {};

  attempts.forEach((attempt) => {
    if (attempt.errors && attempt.errors.length > 0) {
      attempt.errors.forEach((error) => {
        errorAnalysis.push(error);
        errorCounts[error.errorType] = (errorCounts[error.errorType] || 0) + 1;
      });
    }
  });

  return { errorAnalysis, errorCounts };
}

/**
 * Build learning curve data from recall history
 */
export function buildLearningCurve(
  attempts: RecallAttempt[],
  maxSessions: number = 20
): LearningCurveData[] {
  const sortedAttempts = [...attempts].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  const recentAttempts = sortedAttempts.slice(-maxSessions);

  return recentAttempts.map((attempt, index) => ({
    sessionNumber: index + 1,
    accuracy: attempt.accuracy,
    timestamp: attempt.timestamp,
  }));
}

/**
 * Identify learning patterns from recall history
 */
export function identifyPatterns(
  attempts: RecallAttempt[],
  palaceStats: PalaceStats | null
): LearningPattern[] {
  const patterns: LearningPattern[] = [];

  // Analyze recall speed patterns
  if (attempts.length > 1) {
    const speeds = attempts.map((a) => a.duration / a.items.length);
    const avgSpeed = speeds.reduce((sum, s) => sum + s, 0) / speeds.length;
    const minSpeed = Math.min(...speeds);
    const maxSpeed = Math.max(...speeds);

    if (maxSpeed - minSpeed > 10) {
      patterns.push({
        label: 'Recall Speed Variability',
        value: `${minSpeed.toFixed(0)}-${maxSpeed.toFixed(0)}s/item (avg: ${avgSpeed.toFixed(1)}s)`,
      });
    }
  }

  // Analyze accuracy trends
  if (attempts.length > 2) {
    const accuracies = attempts.map((a) => a.accuracy);
    const firstHalfAvg = accuracies.slice(0, Math.floor(accuracies.length / 2)).reduce((a, b) => a + b, 0) / (accuracies.length / 2);
    const secondHalfAvg = accuracies.slice(Math.floor(accuracies.length / 2)).reduce((a, b) => a + b, 0) / (accuracies.length / 2);

    if (secondHalfAvg > firstHalfAvg + 0.1) {
      patterns.push({
        label: 'Accuracy Trend',
        value: 'Improving',
      });
    } else if (firstHalfAvg > secondHalfAvg + 0.1) {
      patterns.push({
        label: 'Accuracy Trend',
        value: 'Declining',
      });
    } else {
      patterns.push({
        label: 'Accuracy Trend',
        value: 'Stable',
      });
    }
  }

  // Analyze confidence patterns
  if (attempts.length > 1) {
    const confidences = attempts.map((a) => a.confidence);
    const avgConfidence = confidences.reduce((sum, c) => sum + c, 0) / confidences.length;

    patterns.push({
      label: 'Average Confidence',
      value: `${(avgConfidence * 100).toFixed(0)}%`,
    });
  }

  // Analyze error patterns
  const { errorCounts } = analyzeErrors(attempts);
  if (Object.keys(errorCounts).length > 0) {
    const mostCommonError = Object.entries(errorCounts).sort((a, b) => b[1] - a[1])[0];
    patterns.push({
      label: 'Most Common Error',
      value: mostCommonError[0].charAt(0).toUpperCase() + mostCommonError[0].slice(1),
    });
  }

  // Analyze session duration patterns
  if (palaceStats && palaceStats.sessionHistory.length > 0) {
    const durations = palaceStats.sessionHistory.map((s) => s.duration);
    const avgDuration = durations.reduce((sum, d) => sum + d, 0) / durations.length;
    const minDuration = Math.min(...durations);
    const maxDuration = Math.max(...durations);

    if (maxDuration - minDuration > 30) {
      patterns.push({
        label: 'Session Duration',
        value: `${minDuration}-${maxDuration}s (avg: ${avgDuration.toFixed(0)}s)`,
      });
    }
  }

  return patterns;
}

/**
 * Generate personalized recommendations based on analytics
 */
export function generateRecommendations(
  currentMetrics: CurrentMetrics | null,
  errorAnalysis: ErrorAnalysis[],
  patterns: LearningPattern[],
  attempts: RecallAttempt[]
): Recommendations {
  const generalRecommendations: string[] = [];
  const errorSpecificRecommendations: { errorType: string; suggestions: string[] }[] = [];

  // Accuracy-based recommendations
  if (currentMetrics && currentMetrics.accuracy < 0.7) {
    generalRecommendations.push('Focus on improving recall accuracy before increasing speed');
    generalRecommendations.push('Practice visualization techniques for difficult items');
  } else if (currentMetrics && currentMetrics.accuracy >= 0.9) {
    generalRecommendations.push('Consider increasing the complexity of items to maintain challenge');
  }

  // Speed-based recommendations
  if (currentMetrics && currentMetrics.recallSpeed > 60) {
    generalRecommendations.push('Your recall speed is slow - try reducing the number of items per session');
    generalRecommendations.push('Practice with simpler item sequences to build speed');
  } else if (currentMetrics && currentMetrics.recallSpeed < 30 && currentMetrics.accuracy < 0.8) {
    generalRecommendations.push('You recall quickly but with lower accuracy - slow down and focus on precision');
  }

  // Confidence-based recommendations
  if (currentMetrics && currentMetrics.confidence < 0.5) {
    generalRecommendations.push('Low confidence scores suggest you need more practice with this palace');
    generalRecommendations.push('Try recalling items multiple times before rating confidence');
  }

  // Error-specific recommendations
  const errorCounts: Record<string, number> = {};
  errorAnalysis.forEach((error) => {
    errorCounts[error.errorType] = (errorCounts[error.errorType] || 0) + 1;
  });

  if (errorCounts['omission'] && errorCounts['omission'] > 2) {
    errorSpecificRecommendations.push({
      errorType: 'Omission',
      suggestions: [
        'Focus on remembering all items, not just the most memorable ones',
        'Use a systematic approach to ensure you check all positions',
        'Practice with items that have similar characteristics to avoid overlooking them',
      ],
    });
  }

  if (errorCounts['substitution'] && errorCounts['substitution'] > 2) {
    errorSpecificRecommendations.push({
      errorType: 'Substitution',
      suggestions: [
        'Strengthen the associations between items and their positions',
        'Use more distinctive visualizations for each item',
        'Practice recalling items in sequence to maintain order',
      ],
    });
  }

  if (errorCounts['transposition'] && errorCounts['transposition'] > 2) {
    errorSpecificRecommendations.push({
      errorType: 'Transposition',
      suggestions: [
        'Focus on the order of items, not just their presence',
        'Use spatial cues to remember the sequence',
        'Practice recalling items in groups to reinforce order',
      ],
    });
  }

  // Pattern-based recommendations
  const accuracyTrend = patterns.find((p) => p.label === 'Accuracy Trend');
  if (accuracyTrend && accuracyTrend.value === 'Declining') {
    generalRecommendations.push('Your accuracy is declining - consider taking a break and returning with fresh mind');
    generalRecommendations.push('Review your visualization techniques and strengthen weak associations');
  }

  return {
    general: generalRecommendations,
    errorSpecific: errorSpecificRecommendations,
  };
}

/**
 * Main hook for accuracy analytics
 */
export function useAccuracyAnalytics(
  palaceId: string,
  attempts: RecallAttempt[],
  palaceStats: PalaceStats | null
) {
  const currentMetrics = calculateCurrentMetrics(attempts);
  const { errorAnalysis, errorCounts } = analyzeErrors(attempts);
  const learningCurve = buildLearningCurve(attempts);
  const patterns = identifyPatterns(attempts, palaceStats);
  const recommendations = generateRecommendations(currentMetrics, errorAnalysis, patterns, attempts);

  return {
    currentMetrics,
    errorAnalysis,
    errorCounts,
    learningCurve,
    patterns,
    recommendations,
    progress: {
      totalSessions: attempts.length,
      averageAccuracy: currentMetrics?.accuracy || 0,
      averageSpeed: currentMetrics?.recallSpeed || 0,
    },
    isLoading: false,
    error: null,
    refresh: () => {
      // In a real implementation, this would fetch fresh data
      return Promise.resolve();
    },
  };
}
