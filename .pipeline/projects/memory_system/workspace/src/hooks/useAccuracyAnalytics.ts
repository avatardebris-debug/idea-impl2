import { useState, useCallback, useEffect, useMemo } from 'react';
import {
  calculateRecallAccuracy,
  analyzeRecallErrors,
  calculateLearningCurve,
  identifyRecallPatterns,
  generateImprovementRecommendations,
  calculateLearningProgress,
  RecallAccuracyMetrics,
  RecallErrorAnalysis,
  LearningCurvePoint,
} from '../utils/accuracyAnalytics';
import { RecallAttempt, Card, NumberCard } from '../types/memoryPalace';

interface UseAccuracyAnalyticsProps {
  recallHistory: RecallAttempt[];
  expectedItems: (string | Card | NumberCard)[];
  enabled?: boolean;
}

interface AccuracyAnalytics {
  currentMetrics: RecallAccuracyMetrics | null;
  errorAnalysis: RecallErrorAnalysis[];
  learningCurve: LearningCurvePoint[];
  patterns: {
    trends: {
      accuracyTrend: 'improving' | 'declining' | 'stable';
      speedTrend: 'improving' | 'declining' | 'stable';
      confidenceTrend: 'improving' | 'declining' | 'stable';
    };
    weakPoints: {
      position: number;
      averageAccuracy: number;
      averageConfidence: number;
    }[];
    strongPoints: {
      position: number;
      averageAccuracy: number;
      averageConfidence: number;
    }[];
  };
  recommendations: string[];
  progress: {
    currentAccuracy: number;
    improvementRate: number;
    masteryLevel: 'novice' | 'developing' | 'proficient' | 'expert';
    estimatedMasteryDate: string | null;
  };
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export const useAccuracyAnalytics = ({
  recallHistory,
  expectedItems,
  enabled = true,
}: UseAccuracyAnalyticsProps): AccuracyAnalytics => {
  const [currentMetrics, setCurrentMetrics] = useState<RecallAccuracyMetrics | null>(null);
  const [errorAnalysis, setErrorAnalysis] = useState<RecallErrorAnalysis[]>([]);
  const [learningCurve, setLearningCurve] = useState<LearningCurvePoint[]>([]);
  const [patterns, setPatterns] = useState<{
    trends: {
      accuracyTrend: 'improving' | 'declining' | 'stable';
      speedTrend: 'improving' | 'declining' | 'stable';
      confidenceTrend: 'improving' | 'declining' | 'stable';
    };
    weakPoints: {
      position: number;
      averageAccuracy: number;
      averageConfidence: number;
    }[];
    strongPoints: {
      position: number;
      averageAccuracy: number;
      averageConfidence: number;
    }[];
  } | null>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [progress, setProgress] = useState<{
    currentAccuracy: number;
    improvementRate: number;
    masteryLevel: 'novice' | 'developing' | 'proficient' | 'expert';
    estimatedMasteryDate: string | null;
  }>({
    currentAccuracy: 0,
    improvementRate: 0,
    masteryLevel: 'novice',
    estimatedMasteryDate: null,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performAnalysis = useCallback(() => {
    if (!enabled || recallHistory.length === 0) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Simulate async operation
      setTimeout(() => {
        // Get most recent attempt metrics
        const latestAttempt = recallHistory[recallHistory.length - 1];
        const metrics = calculateRecallAccuracy(latestAttempt, expectedItems);
        setCurrentMetrics(metrics);

        // Analyze errors
        const errors = analyzeRecallErrors(latestAttempt, expectedItems);
        setErrorAnalysis(errors);

        // Calculate learning curve
        const curve = calculateLearningCurve(recallHistory);
        setLearningCurve(curve);

        // Identify patterns
        const accuracyHistory = recallHistory.map(attempt =>
          calculateRecallAccuracy(attempt, expectedItems)
        );
        const identifiedPatterns = identifyRecallPatterns(accuracyHistory);
        setPatterns(identifiedPatterns);

        // Generate recommendations
        const recs = generateImprovementRecommendations(metrics, errors, identifiedPatterns);
        setRecommendations(recs);

        // Calculate progress
        const prog = calculateLearningProgress(curve);
        setProgress(prog);

        setIsLoading(false);
      }, 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze accuracy');
      setIsLoading(false);
    }
  }, [recallHistory, expectedItems, enabled]);

  useEffect(() => {
    if (enabled) {
      performAnalysis();
    }
  }, [recallHistory, expectedItems, enabled, performAnalysis]);

  const refresh = useCallback(() => {
    performAnalysis();
  }, [performAnalysis]);

  return {
    currentMetrics,
    errorAnalysis,
    learningCurve,
    patterns,
    recommendations,
    progress,
    isLoading,
    error,
    refresh,
  };
};

export default useAccuracyAnalytics;
