import React from 'react';
import {
  RecallAccuracyMetrics,
  RecallErrorAnalysis,
  LearningCurvePoint,
} from '../utils/accuracyAnalytics';

interface MemoryPalaceAnalyticsProps {
  metrics: RecallAccuracyMetrics | null;
  errorAnalysis: RecallErrorAnalysis[];
  learningCurve: LearningCurvePoint[];
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
  recommendations: string[];
  progress: {
    currentAccuracy: number;
    improvementRate: number;
    masteryLevel: 'novice' | 'developing' | 'proficient' | 'expert';
    estimatedMasteryDate: string | null;
  };
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
}

const TrendIndicator: React.FC<{ trend: 'improving' | 'declining' | 'stable'; label: string }> = ({ trend, label }) => {
  const colors = {
    improving: '#28a745',
    declining: '#dc3545',
    stable: '#ffc107',
  };

  const icons = {
    improving: '📈',
    declining: '📉',
    stable: '➡️',
  };

  return (
    <div className="analytics-trend-item">
      <span className="trend-icon">{icons[trend]}</span>
      <span className="trend-label">{label}</span>
      <span
        className="trend-indicator"
        style={{ backgroundColor: colors[trend] }}
      >
        {trend}
      </span>
    </div>
  );
};

const AccuracyGauge: React.FC<{ accuracy: number }> = ({ accuracy }) => {
  const circumference = 2 * Math.PI * 40;
  const strokeDashoffset = circumference - accuracy * circumference;

  return (
    <div className="accuracy-gauge">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="#e0e0e0"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke={accuracy > 0.7 ? '#28a745' : accuracy > 0.5 ? '#ffc107' : '#dc3545'}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform="rotate(-90 50 50)"
        />
      </svg>
      <div className="accuracy-value">{(accuracy * 100).toFixed(0)}%</div>
    </div>
  );
};

const LearningCurveChart: React.FC<{ data: LearningCurvePoint[] }> = ({ data }) => {
  if (data.length === 0) {
    return (
      <div className="learning-curve-chart">
        <p className="chart-placeholder">No learning data available</p>
      </div>
    );
  }

  const maxAccuracy = Math.max(...data.map(d => d.accuracy), 0.5);
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 100 - (d.accuracy / maxAccuracy) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="learning-curve-chart">
      <svg width="100%" height="200" viewBox="0 0 100 100" preserveAspectRatio="none">
        <defs>
          <linearGradient id="curveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#28a745', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: '#28a745', stopOpacity: 0.3 }} />
          </linearGradient>
        </defs>
        <polygon
          points={`0,100 ${points} 100,100`}
          fill="url(#curveGradient)"
        />
        <polyline
          points={points}
          fill="none"
          stroke="#28a745"
          strokeWidth="2"
        />
        {data.map((d, i) => {
          const x = (i / (data.length - 1)) * 100;
          const y = 100 - (d.accuracy / maxAccuracy) * 100;
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r="2"
              fill="#28a745"
            />
          );
        })}
      </svg>
      <div className="chart-labels">
        <span>Attempt 1</span>
        <span>Attempt {data.length}</span>
      </div>
    </div>
  );
};

const ErrorAnalysisList: React.FC<{ errors: RecallErrorAnalysis[] }> = ({ errors }) => {
  if (errors.length === 0) {
    return (
      <div className="error-analysis">
        <h4>Error Analysis</h4>
        <p className="no-errors">No errors detected - excellent recall!</p>
      </div>
    );
  }

  const errorTypes = {
    omission: { label: 'Omission', color: '#dc3545' },
    substitution: { label: 'Substitution', color: '#fd7e14' },
    transposition: { label: 'Transposition', color: '#ffc107' },
    distortion: { label: 'Distortion', color: '#17a2b8' },
    hallucination: { label: 'Hallucination', color: '#6f42c1' },
  };

  return (
    <div className="error-analysis">
      <h4>Error Analysis ({errors.length} errors)</h4>
      <div className="error-list">
        {errors.slice(0, 10).map((error, index) => (
          <div key={index} className="error-item">
            <span
              className="error-type"
              style={{ backgroundColor: errorTypes[error.errorType].color }}
            >
              {errorTypes[error.errorType].label}
            </span>
            <div className="error-details">
              <div className="error-item-label">Expected:</div>
              <div className="error-item-value">{JSON.stringify(error.expected)}</div>
              <div className="error-item-label">Recalled:</div>
              <div className="error-item-value">
                {error.recalled ? JSON.stringify(error.recalled) : 'Not recalled'}
              </div>
              {error.positionExpected !== -1 && (
                <div className="error-item-label">
                  Position: {error.positionExpected} → {error.positionRecalled ?? 'missed'}
                </div>
              )}
            </div>
          </div>
        ))}
        {errors.length > 10 && (
          <div className="error-more">
            +{errors.length - 10} more errors
          </div>
        )}
      </div>
    </div>
  );
};

const RecommendationList: React.FC<{ recommendations: string[] }> = ({ recommendations }) => {
  if (recommendations.length === 0) {
    return (
      <div className="recommendations">
        <h4>Recommendations</h4>
        <p className="no-recommendations">No specific recommendations at this time.</p>
      </div>
    );
  }

  return (
    <div className="recommendations">
      <h4>Personalized Recommendations</h4>
      <ul className="recommendation-list">
        {recommendations.map((rec, index) => (
          <li key={index} className="recommendation-item">
            {rec}
          </li>
        ))}
      </ul>
    </div>
  );
};

const MasteryBadge: React.FC<{ level: string }> = ({ level }) => {
  const colors = {
    novice: '#6c757d',
    developing: '#17a2b8',
    proficient: '#28a745',
    expert: '#ffc107',
  };

  return (
    <div className="mastery-badge" style={{ backgroundColor: colors[level as keyof typeof colors] }}>
      {level.charAt(0).toUpperCase() + level.slice(1)}
    </div>
  );
};

export const MemoryPalaceAnalytics: React.FC<MemoryPalaceAnalyticsProps> = ({
  metrics,
  errorAnalysis,
  learningCurve,
  trends,
  weakPoints,
  strongPoints,
  recommendations,
  progress,
  isLoading,
  error,
  onRefresh,
}) => {
  if (isLoading) {
    return (
      <div className="memory-palace-analytics">
        <div className="loading">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="memory-palace-analytics">
        <div className="error">Error: {error}</div>
        <button onClick={onRefresh} className="retry-button">Retry</button>
      </div>
    );
  }

  return (
    <div className="memory-palace-analytics">
      <div className="analytics-header">
        <h2>Memory Palace Analytics</h2>
        <button onClick={onRefresh} className="refresh-button">
          🔄 Refresh
        </button>
      </div>

      <div className="analytics-grid">
        {/* Current Performance */}
        <div className="analytics-card">
          <h3>Current Performance</h3>
          {metrics ? (
            <div className="performance-metrics">
              <AccuracyGauge accuracy={metrics.accuracy} />
              <div className="metrics-details">
                <div className="metric-item">
                  <span className="metric-label">Correctly Recalled:</span>
                  <span className="metric-value">{metrics.correctlyRecalled}/{metrics.totalItems}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Partially Recalled:</span>
                  <span className="metric-value">{metrics.partiallyRecalled}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Missed:</span>
                  <span className="metric-value">{metrics.missed}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Order Accuracy:</span>
                  <span className="metric-value">{(metrics.orderAccuracy * 100).toFixed(0)}%</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Recall Speed:</span>
                  <span className="metric-value">{metrics.recallSpeed.toFixed(1)}s/item</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Confidence:</span>
                  <span className="metric-value">{(metrics.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          ) : (
            <p>No data available</p>
          )}
        </div>

        {/* Trends */}
        <div className="analytics-card">
          <h3>Performance Trends</h3>
          <div className="trends-container">
            <TrendIndicator
              trend={trends.accuracyTrend}
              label="Accuracy"
            />
            <TrendIndicator
              trend={trends.speedTrend}
              label="Speed"
            />
            <TrendIndicator
              trend={trends.confidenceTrend}
              label="Confidence"
            />
          </div>
        </div>

        {/* Mastery Level */}
        <div className="analytics-card">
          <h3>Mastery Level</h3>
          <div className="mastery-container">
            <MasteryBadge level={progress.masteryLevel} />
            <div className="mastery-details">
              <div className="mastery-stat">
                <span className="stat-label">Current Accuracy:</span>
                <span className="stat-value">{(progress.currentAccuracy * 100).toFixed(0)}%</span>
              </div>
              <div className="mastery-stat">
                <span className="stat-label">Improvement Rate:</span>
                <span className="stat-value">
                  {(progress.improvementRate * 100).toFixed(2)}% per attempt
                </span>
              </div>
              {progress.estimatedMasteryDate && (
                <div className="mastery-stat">
                  <span className="stat-label">Est. Mastery:</span>
                  <span className="stat-value">
                    {new Date(progress.estimatedMasteryDate).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Learning Curve */}
        <div className="analytics-card full-width">
          <h3>Learning Curve</h3>
          <LearningCurveChart data={learningCurve} />
        </div>

        {/* Error Analysis */}
        <div className="analytics-card">
          <ErrorAnalysisList errors={errorAnalysis} />
        </div>

        {/* Weak & Strong Points */}
        <div className="analytics-card">
          <h3>Position Analysis</h3>
          <div className="position-analysis">
            {weakPoints.length > 0 && (
              <div className="position-section">
                <h4>Weak Positions</h4>
                <ul className="position-list">
                  {weakPoints.slice(0, 5).map((point, index) => (
                    <li key={index} className="position-item">
                      <span className="position-number">Position {point.position}</span>
                      <span className="position-accuracy">
                        {(point.averageAccuracy * 100).toFixed(0)}% accuracy
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {strongPoints.length > 0 && (
              <div className="position-section">
                <h4>Strong Positions</h4>
                <ul className="position-list">
                  {strongPoints.slice(0, 5).map((point, index) => (
                    <li key={index} className="position-item">
                      <span className="position-number">Position {point.position}</span>
                      <span className="position-accuracy">
                        {(point.averageAccuracy * 100).toFixed(0)}% accuracy
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {weakPoints.length === 0 && strongPoints.length === 0 && (
              <p className="no-positions">No position data available yet</p>
            )}
          </div>
        </div>

        {/* Recommendations */}
        <div className="analytics-card full-width">
          <RecommendationList recommendations={recommendations} />
        </div>
      </div>
    </div>
  );
};

export default MemoryPalaceAnalytics;
