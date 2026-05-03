import { AnalyticsDashboard } from '../src/components/AnalyticsDashboard';
import {
  useAccuracyAnalytics,
  calculateCurrentMetrics,
  analyzeErrors,
  buildLearningCurve,
  identifyPatterns,
  generateRecommendations,
  getPalaceStats,
  savePalaceStats,
  addSessionToStats,
  getRecentSessions,
  getAccuracyTrend,
  calculateAccuracy,
  detectErrors,
  createRecallAttempt,
  generateAttemptId,
  type RecallAttempt,
  type PalaceStats,
  type CurrentMetrics,
  type ErrorAnalysis,
  type LearningPattern,
  type LearningCurveData,
  type Recommendations,
} from '../src';

/**
 * Example: Complete Analytics Dashboard Integration
 * 
 * This example demonstrates how to integrate the Analytics Dashboard
 * into a memory palace application with full functionality.
 */

// Example 1: Basic Setup
function BasicAnalyticsExample() {
  const palaceId = 'my-memory-palace';
  
  // Mock data - in production, this would come from your state management
  const recallAttempts: RecallAttempt[] = [
    {
      id: generateAttemptId(),
      palaceId,
      timestamp: new Date('2024-01-01').toISOString(),
      items: ['apple', 'banana', 'cherry'],
      accuracy: 1.0,
      duration: 60,
      confidence: 0.9,
      errors: [],
    },
    {
      id: generateAttemptId(),
      palaceId,
      timestamp: new Date('2024-01-02').toISOString(),
      items: ['apple', 'banana', 'cherry'],
      accuracy: 0.67,
      duration: 45,
      confidence: 0.7,
      errors: [
        {
          errorType: 'omission',
          positionExpected: 2,
          positionRecalled: undefined,
          expected: 'cherry',
          recalled: undefined,
        },
      ],
    },
  ];

  const palaceStats: PalaceStats = {
    sessionHistory: recallAttempts.map((attempt) => ({
      startTime: attempt.timestamp,
      accuracy: attempt.accuracy,
      duration: attempt.duration,
      totalItems: attempt.items.length,
      correctItems: Math.round(attempt.items.length * attempt.accuracy),
      confidence: attempt.confidence,
    })),
    totalSessions: recallAttempts.length,
    averageAccuracy: 0.835,
    averageDuration: 52.5,
    lastSessionDate: recallAttempts[recallAttempts.length - 1].timestamp,
  };

  return (
    <AnalyticsDashboard
      palaceId={palaceId}
      attempts={recallAttempts}
      palaceStats={palaceStats}
      enabled={true}
    />
  );
}

// Example 2: Real-time Analytics with Hook
function RealtimeAnalyticsExample() {
  const palaceId = 'realtime-palace';
  
  // Use the analytics hook for automatic updates
  const {
    currentMetrics,
    errorAnalysis,
    learningCurve,
    patterns,
    recommendations,
    progress,
    isLoading,
    error,
    refresh,
  } = useAccuracyAnalytics(palaceId, recallAttempts, palaceStats);

  if (isLoading) {
    return <div>Loading analytics...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Memory Palace Analytics</h1>
      
      {/* Current Metrics */}
      {currentMetrics && (
        <div>
          <h2>Current Performance</h2>
          <p>Accuracy: {(currentMetrics.accuracy * 100).toFixed(0)}%</p>
          <p>Recall Speed: {currentMetrics.recallSpeed.toFixed(1)}s/item</p>
          <p>Confidence: {(currentMetrics.confidence * 100).toFixed(0)}%</p>
        </div>
      )}

      {/* Error Analysis */}
      {errorAnalysis.length > 0 && (
        <div>
          <h2>Error Analysis</h2>
          {errorAnalysis.map((error, index) => (
            <div key={index}>
              <p>
                {error.errorType}: Expected '{error.expected}', 
                {error.recalled ? ` recalled '${error.recalled}'` : ' missed'}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Learning Patterns */}
      {patterns.length > 0 && (
        <div>
          <h2>Learning Patterns</h2>
          {patterns.map((pattern, index) => (
            <div key={index}>
              <strong>{pattern.label}:</strong> {pattern.value}
            </div>
          ))}
        </div>
      )}

      {/* Recommendations */}
      {recommendations.general.length > 0 && (
        <div>
          <h2>Recommendations</h2>
          <ul>
            {recommendations.general.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      <button onClick={refresh}>Refresh Analytics</button>
    </div>
  );
}

// Example 3: Custom Analytics Dashboard with Manual Calculations
function CustomAnalyticsExample() {
  const palaceId = 'custom-palace';
  const [attempts, setAttempts] = useState<RecallAttempt[]>([]);

  // Manual calculation of metrics
  const currentMetrics = calculateCurrentMetrics(attempts, 5);
  const { errorAnalysis, errorCounts } = analyzeErrors(attempts);
  const learningCurve = buildLearningCurve(attempts, 20);
  const patterns = identifyPatterns(attempts, null);
  const recommendations = generateRecommendations(
    currentMetrics,
    errorAnalysis,
    patterns,
    attempts
  );

  const handleRecallComplete = (
    items: string[],
    recalledItems: string[],
    duration: number,
    confidence: number
  ) => {
    const newAttempt = createRecallAttempt(
      palaceId,
      items,
      recalledItems,
      duration,
      confidence
    );

    setAttempts((prev) => [...prev, newAttempt]);

    // Update palace stats
    const stats = getPalaceStats(palaceId);
    const updatedStats = addSessionToStats(palaceId, {
      startTime: newAttempt.timestamp,
      accuracy: newAttempt.accuracy,
      duration: newAttempt.duration,
      totalItems: newAttempt.items.length,
      correctItems: Math.round(newAttempt.items.length * newAttempt.accuracy),
      confidence: newAttempt.confidence,
    });

    savePalaceStats(palaceId, updatedStats);
  };

  return (
    <div>
      <h1>Custom Analytics Dashboard</h1>
      
      {/* Metrics Display */}
      {currentMetrics && (
        <div className="metrics-display">
          <h2>Performance Metrics</h2>
          <div className="metric">
            <span>Accuracy:</span>
            <span>{(currentMetrics.accuracy * 100).toFixed(0)}%</span>
          </div>
          <div className="metric">
            <span>Recall Speed:</span>
            <span>{currentMetrics.recallSpeed.toFixed(1)}s/item</span>
          </div>
          <div className="metric">
            <span>Confidence:</span>
            <span>{(currentMetrics.confidence * 100).toFixed(0)}%</span>
          </div>
        </div>
      )}

      {/* Error Analysis */}
      <div className="error-analysis">
        <h2>Error Analysis</h2>
        {errorAnalysis.length === 0 ? (
          <p>No errors detected</p>
        ) : (
          <div className="error-summary">
            {Object.entries(errorCounts).map(([type, count]) => (
              <div key={type}>
                <span>{type}:</span>
                <span>{count}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Learning Curve */}
      <div className="learning-curve">
        <h2>Learning Curve</h2>
        {learningCurve.length === 0 ? (
          <p>No learning data yet</p>
        ) : (
          <div className="curve-data">
            {learningCurve.map((data, index) => (
              <div key={index}>
                <span>Session {data.sessionNumber}:</span>
                <span>{(data.accuracy * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Patterns */}
      <div className="patterns">
        <h2>Learning Patterns</h2>
        {patterns.length === 0 ? (
          <p>No patterns identified yet</p>
        ) : (
          <div className="pattern-list">
            {patterns.map((pattern, index) => (
              <div key={index}>
                <strong>{pattern.label}:</strong> {pattern.value}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recommendations */}
      <div className="recommendations">
        <h2>Recommendations</h2>
        {recommendations.general.length === 0 &&
        recommendations.errorSpecific.length === 0 ? (
          <p>No specific recommendations at this time</p>
        ) : (
          <ul>
            {recommendations.general.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
            {recommendations.errorSpecific.map((rec, index) => (
              <li key={`error-${index}`}>
                <strong>{rec.errorType}:</strong>
                <ul>
                  {rec.suggestions.map((suggestion, sIndex) => (
                    <li key={sIndex}>{suggestion}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Manual Recall Button */}
      <button onClick={() => handleRecallComplete(['item1', 'item2'], ['item1'], 30, 0.8)}>
        Simulate Recall
      </button>
    </div>
  );
}

// Example 4: Export Analytics Data
function ExportAnalyticsExample() {
  const palaceId = 'export-palace';
  const [attempts, setAttempts] = useState<RecallAttempt[]>([]);

  const exportAnalytics = () => {
    const palaceStats = getPalaceStats(palaceId);
    const currentMetrics = calculateCurrentMetrics(attempts);
    const { errorAnalysis, errorCounts } = analyzeErrors(attempts);
    const learningCurve = buildLearningCurve(attempts);
    const patterns = identifyPatterns(attempts, palaceStats);
    const recommendations = generateRecommendations(
      currentMetrics,
      errorAnalysis,
      patterns,
      attempts
    );

    const exportData = {
      palaceId,
      exportedAt: new Date().toISOString(),
      metrics: currentMetrics,
      errorAnalysis,
      errorCounts,
      learningCurve,
      patterns,
      recommendations,
      palaceStats,
      rawAttempts: attempts,
    };

    // Download as JSON
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analytics-${palaceId}-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <h1>Export Analytics</h1>
      <button onClick={exportAnalytics}>Export Analytics Data</button>
    </div>
  );
}

// Example 5: Trend Analysis
function TrendAnalysisExample() {
  const palaceId = 'trend-palace';

  const accuracyTrend = getAccuracyTrend(palaceId, 5);

  return (
    <div>
      <h1>Accuracy Trend Analysis</h1>
      
      <div className="trend-display">
        <h2>Recent Performance Trend</h2>
        <p>
          Trend: <strong>{accuracyTrend.trend.toUpperCase()}</strong>
        </p>
        <p>
          Average Accuracy: <strong>{(accuracyTrend.averageAccuracy * 100).toFixed(0)}%</strong>
        </p>
      </div>

      {accuracyTrend.trend === 'improving' && (
        <div className="positive-feedback">
          <p>Great progress! Your accuracy is improving over recent sessions.</p>
        </div>
      )}

      {accuracyTrend.trend === 'declining' && (
        <div className="warning-feedback">
          <p>
            Your accuracy has been declining. Consider taking a break or reviewing
            your visualization techniques.
          </p>
        </div>
      )}

      {accuracyTrend.trend === 'stable' && (
        <div className="neutral-feedback">
          <p>
            Your performance is stable. Consider increasing the difficulty to
            continue improving.
          </p>
        </div>
      )}
    </div>
  );
}

// Example 6: Error-Specific Recommendations
function ErrorSpecificRecommendationsExample() {
  const palaceId = 'error-palace';
  const [attempts, setAttempts] = useState<RecallAttempt[]>([]);

  const { errorAnalysis } = analyzeErrors(attempts);

  // Group errors by type
  const errorGroups = useMemo(() => {
    const groups: Record<string, ErrorAnalysis[]> = {};
    errorAnalysis.forEach((error) => {
      if (!groups[error.errorType]) {
        groups[error.errorType] = [];
      }
      groups[error.errorType].push(error);
    });
    return groups;
  }, [errorAnalysis]);

  const getRecommendationsForError = (errorType: string): string[] => {
    switch (errorType) {
      case 'omission':
        return [
          'Strengthen your visualization of the item',
          'Create a more memorable association',
          'Practice recalling items in smaller groups',
        ];
      case 'substitution':
        return [
          'Focus on the unique characteristics of each item',
          'Create distinct visual markers for each item',
          'Practice distinguishing between similar items',
        ];
      case 'transposition':
        return [
          'Strengthen the sequence of locations',
          'Create a clear path through your palace',
          'Practice recalling items in order',
        ];
      case 'insertion':
        return [
          'Be more careful about what you visualize',
          'Review your original list before recalling',
          'Practice focusing on only the target items',
        ];
      default:
        return ['Review your visualization techniques'];
    }
  };

  return (
    <div>
      <h1>Error-Specific Recommendations</h1>
      
      {Object.keys(errorGroups).length === 0 ? (
        <p>No errors detected yet</p>
      ) : (
        <div className="error-recommendations">
          {Object.entries(errorGroups).map(([errorType, errors]) => (
            <div key={errorType} className="error-section">
              <h3>{errorType} Errors ({errors.length})</h3>
              <ul>
                {errors.slice(0, 3).map((error, index) => (
                  <li key={index}>
                    Expected: <strong>{error.expected}</strong>
                    {error.recalled ? `, Recalled: <strong>{error.recalled}</strong>` : ''}
                  </li>
                ))}
              </ul>
              <div className="recommendations">
                <h4>Recommendations:</h4>
                <ul>
                  {getRecommendationsForError(errorType).map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Example 7: Session History Analysis
function SessionHistoryExample() {
  const palaceId = 'history-palace';
  const palaceStats = getPalaceStats(palaceId);

  const recentSessions = getRecentSessions(palaceId, 10);

  return (
    <div>
      <h1>Session History</h1>
      
      {palaceStats ? (
        <div className="stats-summary">
          <h2>Overall Statistics</h2>
          <p>Total Sessions: {palaceStats.totalSessions}</p>
          <p>Average Accuracy: {(palaceStats.averageAccuracy * 100).toFixed(1)}%</p>
          <p>Average Duration: {palaceStats.averageDuration.toFixed(1)}s</p>
          <p>Last Session: {new Date(palaceStats.lastSessionDate!).toLocaleDateString()}</p>
        </div>
      ) : (
        <p>No session history found</p>
      )}

      <h2>Recent Sessions</h2>
      {recentSessions.length === 0 ? (
        <p>No recent sessions</p>
      ) : (
        <div className="session-list">
          {recentSessions.map((session, index) => (
            <div key={index} className="session-item">
              <div className="session-header">
                <span>
                  {new Date(session.startTime).toLocaleString()}
                </span>
                <span className="accuracy-badge">
                  {(session.accuracy * 100).toFixed(0)}%
                </span>
              </div>
              <div className="session-details">
                <span>Duration: {session.duration}s</span>
                <span>Confidence: {(session.confidence * 100).toFixed(0)}%</span>
                <span>Items: {session.totalItems}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Example 8: Complete Memory Palace Analytics Application
function CompleteAnalyticsApplication() {
  const palaceId = 'complete-palace';
  const [attempts, setAttempts] = useState<RecallAttempt[]>([]);
  const [palaceStats, setPalaceStats] = useState<PalaceStats | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'analysis' | 'curve' | 'recommendations'>('overview');

  // Load initial data
  useEffect(() => {
    const stats = getPalaceStats(palaceId);
    if (stats) {
      setPalaceStats(stats);
    }
  }, [palaceId]);

  // Calculate analytics
  const currentMetrics = calculateCurrentMetrics(attempts, 5);
  const { errorAnalysis, errorCounts } = analyzeErrors(attempts);
  const learningCurve = buildLearningCurve(attempts, 20);
  const patterns = identifyPatterns(attempts, palaceStats);
  const recommendations = generateRecommendations(
    currentMetrics,
    errorAnalysis,
    patterns,
    attempts
  );

  const handleRecallComplete = (
    items: string[],
    recalledItems: string[],
    duration: number,
    confidence: number
  ) => {
    const newAttempt = createRecallAttempt(
      palaceId,
      items,
      recalledItems,
      duration,
      confidence
    );

    setAttempts((prev) => [...prev, newAttempt]);

    const stats = getPalaceStats(palaceId);
    const updatedStats = addSessionToStats(palaceId, {
      startTime: newAttempt.timestamp,
      accuracy: newAttempt.accuracy,
      duration: newAttempt.duration,
      totalItems: newAttempt.items.length,
      correctItems: Math.round(newAttempt.items.length * newAttempt.accuracy),
      confidence: newAttempt.confidence,
    });

    setPalaceStats(updatedStats);
  };

  return (
    <div className="complete-analytics-app">
      <h1>Memory Palace Analytics Dashboard</h1>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'analysis' ? 'active' : ''}
          onClick={() => setActiveTab('analysis')}
        >
          Error Analysis
        </button>
        <button
          className={activeTab === 'curve' ? 'active' : ''}
          onClick={() => setActiveTab('curve')}
        >
          Learning Curve
        </button>
        <button
          className={activeTab === 'recommendations' ? 'active' : ''}
          onClick={() => setActiveTab('recommendations')}
        >
          Recommendations
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <AnalyticsDashboard
              palaceId={palaceId}
              attempts={attempts}
              palaceStats={palaceStats}
              enabled={true}
            />
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="analysis-tab">
            <h2>Error Analysis</h2>
            {errorAnalysis.length === 0 ? (
              <p>No errors detected</p>
            ) : (
              <div className="error-list">
                {errorAnalysis.map((error, index) => (
                  <div key={index} className="error-item">
                    <span className="error-type">{error.errorType}</span>
                    <span>
                      Expected: <strong>{error.expected}</strong>
                    </span>
                    {error.recalled ? (
                      <span>
                        Recalled: <strong>{error.recalled}</strong>
                      </span>
                    ) : (
                      <span>Missed</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'curve' && (
          <div className="curve-tab">
            <h2>Learning Curve</h2>
            {learningCurve.length === 0 ? (
              <p>No learning data yet</p>
            ) : (
              <div className="curve-display">
                {learningCurve.map((data, index) => (
                  <div key={index} className="curve-point">
                    <span>Session {data.sessionNumber}</span>
                    <span>{(data.accuracy * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="recommendations-tab">
            <h2>Personalized Recommendations</h2>
            {recommendations.general.length === 0 &&
            recommendations.errorSpecific.length === 0 ? (
              <p>No specific recommendations at this time</p>
            ) : (
              <div className="recommendations-list">
                {recommendations.general.map((rec, index) => (
                  <div key={index} className="general-rec">
                    <span>{rec}</span>
                  </div>
                ))}
                {recommendations.errorSpecific.map((rec, index) => (
                  <div key={`error-${index}`} className="error-rec">
                    <strong>{rec.errorType}:</strong>
                    <ul>
                      {rec.suggestions.map((suggestion, sIndex) => (
                        <li key={sIndex}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Simulate Recall */}
      <div className="simulate-recall">
        <h3>Simulate Recall</h3>
        <button
          onClick={() =>
            handleRecallComplete(
              ['apple', 'banana', 'cherry'],
              ['apple', 'banana'],
              45,
              0.8
            )
          }
        >
          Simulate Recall
        </button>
      </div>
    </div>
  );
}

// Export all examples
export {
  BasicAnalyticsExample,
  RealtimeAnalyticsExample,
  CustomAnalyticsExample,
  ExportAnalyticsExample,
  TrendAnalysisExample,
  ErrorSpecificRecommendationsExample,
  SessionHistoryExample,
  CompleteAnalyticsApplication,
};
