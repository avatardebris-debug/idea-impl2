import {
  calculateRecallAccuracy,
  analyzeRecallErrors,
  calculateLearningCurve,
  identifyRecallPatterns,
  generateImprovementRecommendations,
  calculateLearningProgress,
} from '../utils/accuracyAnalytics';
import { RecallAttempt, Card, NumberCard } from '../types/memoryPalace';

describe('Accuracy Analytics', () => {
  const mockExpectedItems: (string | Card | NumberCard)[] = [
    'Apple',
    { id: '1', type: 'card', name: 'King of Hearts', value: 1 },
    { id: '2', type: 'number', value: 42 },
    'Banana',
    { id: '3', type: 'card', name: 'Queen of Spades', value: 12 },
  ];

  describe('calculateRecallAccuracy', () => {
    it('should calculate accuracy for perfect recall', () => {
      const attempt: RecallAttempt = {
        id: 'test-1',
        timestamp: '2024-01-01T00:00:00Z',
        expectedItems: mockExpectedItems,
        recalledItems: [
          { item: 'Apple', confidence: 1.0 },
          { item: { id: '1', type: 'card', name: 'King of Hearts', value: 1 }, confidence: 1.0 },
          { item: { id: '2', type: 'number', value: 42 }, confidence: 1.0 },
          { item: 'Banana', confidence: 1.0 },
          { item: { id: '3', type: 'card', name: 'Queen of Spades', value: 12 }, confidence: 1.0 },
        ],
        duration: 10,
      };

      const metrics = calculateRecallAccuracy(attempt, mockExpectedItems);

      expect(metrics.totalItems).toBe(5);
      expect(metrics.correctlyRecalled).toBe(5);
      expect(metrics.partiallyRecalled).toBe(0);
      expect(metrics.missed).toBe(0);
      expect(metrics.accuracy).toBe(1.0);
      expect(metrics.orderAccuracy).toBe(1.0);
      expect(metrics.positionAccuracy).toBe(1.0);
      expect(metrics.recallSpeed).toBe(2);
      expect(metrics.confidence).toBe(1.0);
    });

    it('should calculate accuracy for partial recall', () => {
      const attempt: RecallAttempt = {
        id: 'test-2',
        timestamp: '2024-01-01T00:00:00Z',
        expectedItems: mockExpectedItems,
        recalledItems: [
          { item: 'Apple', confidence: 0.9 },
          { item: 'Banana', confidence: 0.8 },
          { item: { id: '2', type: 'number', value: 42 }, confidence: 0.7 },
        ],
        duration: 8,
      };

      const metrics = calculateRecallAccuracy(attempt, mockExpectedItems);

      expect(metrics.totalItems).toBe(5);
      expect(metrics.correctlyRecalled).toBe(1); // Apple in correct position
      expect(metrics.partiallyRecalled).toBe(2); // Banana and 42
      expect(metrics.missed).toBe(2); // King of Hearts and Queen of Spades
      expect(metrics.accuracy).toBeGreaterThan(0.5);
      expect(metrics.accuracy).toBeLessThan(0.8);
    });

    it('should handle empty recall', () => {
      const attempt: RecallAttempt = {
        id: 'test-3',
        timestamp: '2024-01-01T00:00:00Z',
        expectedItems: mockExpectedItems,
        recalledItems: [],
        duration: 0,
      };

      const metrics = calculateRecallAccuracy(attempt, mockExpectedItems);

      expect(metrics.totalItems).toBe(5);
      expect(metrics.correctlyRecalled).toBe(0);
      expect(metrics.missed).toBe(5);
      expect(metrics.accuracy).toBe(0);
    });

    it('should handle hallucinated items', () => {
      const attempt: RecallAttempt = {
        id: 'test-4',
        timestamp: '2024-01-01T00:00:00Z',
        expectedItems: mockExpectedItems,
        recalledItems: [
          { item: 'Apple', confidence: 0.9 },
          { item: 'Orange', confidence: 0.8 }, // Not in expected list
        ],
        duration: 5,
      };

      const metrics = calculateRecallAccuracy(attempt, mockExpectedItems);

      expect(metrics.totalItems).toBe(5);
      expect(metrics.correctlyRecalled).toBe(1);
      expect(metrics.partiallyRecalled).toBe(1); // Orange counts as partial
      expect(metrics.missed).toBe(4);
    });
  });

  describe('analyzeRecallErrors', () => {
    it('should identify transposition errors', () => {
      const attempt: RecallAttempt = {
        id: 'test-5',
        timestamp: '2024-01-01T00:00:00Z',
        expectedItems: mockExpectedItems,
        recalledItems: [
          { item: 'Apple', confidence: 0.9 },
          { item: 'Banana', confidence: 0.8 }, // Should be position 3
          { item: { id: '2', type: 'number', value: 42 }, confidence: 0.7 },
          { item: { id: '1', type: 'card', name: 'King of Hearts', value: 1 }, confidence: 0.6 }, // Should be position 1
          { item: { id: '3', type: 'card', name: 'Queen of Spades', value: 12 }, confidence: 0.5 },
        ],
        duration: 10,
      };

      const errors = analyzeRecallErrors(attempt, mockExpectedItems);

      const transpositionErrors = errors.filter(e => e.errorType === 'transposition');
      expect(transpositionErrors.length).toBeGreaterThan(0);
    });

    it('should identify omission errors', () => {
      const attempt: RecallAttempt = {
        id: 'test-6',
        timestamp: '2024-01-01T00:00:00Z',
        expectedItems: mockExpectedItems,
        recalledItems: [
          { item: 'Apple', confidence: 0.9 },
        ],
        duration: 3,
      };

      const errors = analyzeRecallErrors(attempt, mockExpectedItems);

      const omissionErrors = errors.filter(e => e.errorType === 'omission');
      expect(omissionErrors.length).toBe(4);
    });

    it('should identify hallucination errors', () => {
      const attempt: RecallAttempt = {
        id: 'test-7',
        timestamp: '2024-01-01T00:00:00Z',
        expectedItems: mockExpectedItems,
        recalledItems: [
          { item: 'Apple', confidence: 0.9 },
          { item: 'Orange', confidence: 0.8 },
        ],
        duration: 5,
      };

      const errors = analyzeRecallErrors(attempt, mockExpectedItems);

      const hallucinationErrors = errors.filter(e => e.errorType === 'hallucination');
      expect(hallucinationErrors.length).toBe(1);
    });

    it('should identify substitution errors', () => {
      const attempt: RecallAttempt = {
        id: 'test-8',
        timestamp: '2024-01-01T00:00:00Z',
        expectedItems: mockExpectedItems,
        recalledItems: [
          { item: 'Apple', confidence: 0.9 },
          { item: 'Orange', confidence: 0.8 }, // Substitution for King of Hearts
          { item: { id: '2', type: 'number', value: 42 }, confidence: 0.7 },
          { item: 'Banana', confidence: 0.6 },
          { item: { id: '3', type: 'card', name: 'Queen of Spades', value: 12 }, confidence: 0.5 },
        ],
        duration: 10,
      };

      const errors = analyzeRecallErrors(attempt, mockExpectedItems);

      const substitutionErrors = errors.filter(e => e.errorType === 'substitution');
      expect(substitutionErrors.length).toBeGreaterThan(0);
    });
  });

  describe('calculateLearningCurve', () => {
    it('should calculate learning curve from multiple attempts', () => {
      const attempts: RecallAttempt[] = [
        {
          id: 'attempt-1',
          timestamp: '2024-01-01T00:00:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Apple', confidence: 0.3 },
          ],
          duration: 15,
        },
        {
          id: 'attempt-2',
          timestamp: '2024-01-01T00:01:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Apple', confidence: 0.6 },
            { item: 'Banana', confidence: 0.4 },
          ],
          duration: 12,
        },
        {
          id: 'attempt-3',
          timestamp: '2024-01-01T00:02:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Apple', confidence: 0.9 },
            { item: 'Banana', confidence: 0.8 },
            { item: { id: '2', type: 'number', value: 42 }, confidence: 0.7 },
          ],
          duration: 10,
        },
      ];

      const curve = calculateLearningCurve(attempts, mockExpectedItems);

      expect(curve.length).toBe(3);
      expect(curve[0].accuracy).toBeLessThan(curve[2].accuracy);
      expect(curve[0].averageConfidence).toBeLessThan(curve[2].averageConfidence);
      expect(curve[0].averageSpeed).toBeGreaterThan(curve[2].averageSpeed);
    });

    it('should handle single attempt', () => {
      const attempts: RecallAttempt[] = [
        {
          id: 'attempt-1',
          timestamp: '2024-01-01T00:00:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Apple', confidence: 0.5 },
          ],
          duration: 10,
        },
      ];

      const curve = calculateLearningCurve(attempts, mockExpectedItems);

      expect(curve.length).toBe(1);
    });
  });

  describe('identifyRecallPatterns', () => {
    it('should identify position-based patterns', () => {
      const attempts: RecallAttempt[] = [
        {
          id: 'attempt-1',
          timestamp: '2024-01-01T00:00:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Apple', confidence: 0.9 },
            { item: 'Banana', confidence: 0.3 },
          ],
          duration: 10,
        },
        {
          id: 'attempt-2',
          timestamp: '2024-01-01T00:01:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Apple', confidence: 0.95 },
            { item: 'Banana', confidence: 0.4 },
          ],
          duration: 10,
        },
      ];

      const patterns = identifyRecallPatterns(attempts, mockExpectedItems);

      expect(patterns.weakPoints.length).toBeGreaterThan(0);
      expect(patterns.strongPoints.length).toBeGreaterThan(0);
    });

    it('should identify time-based patterns', () => {
      const attempts: RecallAttempt[] = [
        {
          id: 'attempt-1',
          timestamp: '2024-01-01T00:00:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Apple', confidence: 0.9 },
          ],
          duration: 10,
        },
        {
          id: 'attempt-2',
          timestamp: '2024-01-01T00:01:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Apple', confidence: 0.8 },
          ],
          duration: 15,
        },
      ];

      const patterns = identifyRecallPatterns(attempts, mockExpectedItems);

      expect(patterns.trends.accuracyTrend).toBeDefined();
      expect(patterns.trends.speedTrend).toBeDefined();
    });
  });

  describe('generateImprovementRecommendations', () => {
    it('should generate recommendations for low accuracy', () => {
      const metrics = calculateRecallAccuracy(
        {
          id: 'test',
          timestamp: '2024-01-01T00:00:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [],
          duration: 0,
        },
        mockExpectedItems
      );

      const recommendations = generateImprovementRecommendations(metrics, []);

      expect(recommendations.length).toBeGreaterThan(0);
      expect(recommendations[0]).toContain('accuracy');
    });

    it('should generate recommendations for slow recall', () => {
      const metrics = calculateRecallAccuracy(
        {
          id: 'test',
          timestamp: '2024-01-01T00:00:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Apple', confidence: 0.9 },
          ],
          duration: 60,
        },
        mockExpectedItems
      );

      const recommendations = generateImprovementRecommendations(metrics, []);

      expect(recommendations.some(r => r.toLowerCase().includes('speed'))).toBe(true);
    });

    it('should generate recommendations for low confidence', () => {
      const metrics = calculateRecallAccuracy(
        {
          id: 'test',
          timestamp: '2024-01-01T00:00:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Apple', confidence: 0.3 },
          ],
          duration: 5,
        },
        mockExpectedItems
      );

      const recommendations = generateImprovementRecommendations(metrics, []);

      expect(recommendations.some(r => r.toLowerCase().includes('confidence'))).toBe(true);
    });

    it('should generate recommendations for transposition errors', () => {
      const errors = [
        {
          errorType: 'transposition',
          expected: 'Apple',
          recalled: 'Banana',
          positionExpected: 0,
          positionRecalled: 1,
        },
      ];

      const metrics = calculateRecallAccuracy(
        {
          id: 'test',
          timestamp: '2024-01-01T00:00:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Banana', confidence: 0.8 },
            { item: 'Apple', confidence: 0.8 },
          ],
          duration: 5,
        },
        mockExpectedItems
      );

      const recommendations = generateImprovementRecommendations(metrics, errors);

      expect(recommendations.some(r => r.toLowerCase().includes('order') || r.toLowerCase().includes('sequence'))).toBe(true);
    });

    it('should generate recommendations for hallucination errors', () => {
      const errors = [
        {
          errorType: 'hallucination',
          expected: null,
          recalled: 'Orange',
          positionExpected: -1,
          positionRecalled: 0,
        },
      ];

      const metrics = calculateRecallAccuracy(
        {
          id: 'test',
          timestamp: '2024-01-01T00:00:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: [
            { item: 'Orange', confidence: 0.8 },
          ],
          duration: 5,
        },
        mockExpectedItems
      );

      const recommendations = generateImprovementRecommendations(metrics, errors);

      expect(recommendations.some(r => r.toLowerCase().includes('hallucination') || r.toLowerCase().includes('fabrication'))).toBe(true);
    });

    it('should return empty array for perfect recall', () => {
      const metrics = calculateRecallAccuracy(
        {
          id: 'test',
          timestamp: '2024-01-01T00:00:00Z',
          expectedItems: mockExpectedItems,
          recalledItems: mockExpectedItems.map(item => ({ item, confidence: 1.0 })),
          duration: 10,
        },
        mockExpectedItems
      );

      const recommendations = generateImprovementRecommendations(metrics, []);

      expect(recommendations.length).toBe(0);
    });
  });

  describe('calculateLearningProgress', () => {
    it('should calculate progress from learning curve', () => {
      const learningCurve: { accuracy: number; averageConfidence: number; averageSpeed: number }[] = [
        { accuracy: 0.2, averageConfidence: 0.3, averageSpeed: 15 },
        { accuracy: 0.5, averageConfidence: 0.6, averageSpeed: 12 },
        { accuracy: 0.8, averageConfidence: 0.85, averageSpeed: 10 },
      ];

      const progress = calculateLearningProgress(learningCurve);

      expect(progress.currentAccuracy).toBe(0.8);
      expect(progress.improvementRate).toBeGreaterThan(0);
      expect(progress.masteryLevel).toBe('developing');
    });

    it('should classify mastery levels correctly', () => {
      const lowAccuracyCurve = [
        { accuracy: 0.3, averageConfidence: 0.4, averageSpeed: 20 },
      ];

      const progress = calculateLearningProgress(lowAccuracyCurve);
      expect(progress.masteryLevel).toBe('novice');

      const mediumAccuracyCurve = [
        { accuracy: 0.6, averageConfidence: 0.65, averageSpeed: 12 },
      ];

      const progress2 = calculateLearningProgress(mediumAccuracyCurve);
      expect(progress2.masteryLevel).toBe('developing');

      const highAccuracyCurve = [
        { accuracy: 0.85, averageConfidence: 0.9, averageSpeed: 8 },
      ];

      const progress3 = calculateLearningProgress(highAccuracyCurve);
      expect(progress3.masteryLevel).toBe('proficient');

      const expertCurve = [
        { accuracy: 0.95, averageConfidence: 0.98, averageSpeed: 5 },
      ];

      const progress4 = calculateLearningProgress(expertCurve);
      expect(progress4.masteryLevel).toBe('expert');
    });

    it('should estimate mastery date', () => {
      const learningCurve: { accuracy: number; averageConfidence: number; averageSpeed: number }[] = [
        { accuracy: 0.3, averageConfidence: 0.4, averageSpeed: 20 },
        { accuracy: 0.5, averageConfidence: 0.6, averageSpeed: 15 },
        { accuracy: 0.7, averageConfidence: 0.75, averageSpeed: 12 },
      ];

      const progress = calculateLearningProgress(learningCurve);

      expect(progress.estimatedMasteryDate).toBeDefined();
      expect(new Date(progress.estimatedMasteryDate!).getTime()).toBeGreaterThan(Date.now());
    });
  });
});
