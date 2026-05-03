import React, { useState, useEffect, useCallback } from 'react';
import {
  useAccuracyAnalytics,
  RecallAccuracyMetrics,
  RecallErrorAnalysis,
  LearningCurvePoint,
} from '../utils/accuracyAnalytics';
import { useExerciseProgress } from '../hooks/useExerciseProgress';
import { PalaceExerciseSession, PalaceStats, getPalaceStats } from '../utils/progressTracking';
import { RecallAttempt, Card, NumberCard } from '../types/memoryPalace';
import './AnalyticsDashboard.css';

interface AnalyticsDashboardProps {
  palaceId: string;
  palaceName: string;
  expectedItems: (string | Card | NumberCard)[];
  recallHistory: RecallAttempt[];
  enabled?: boolean;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  palaceId,
  palaceName,
  expectedItems,
  recallHistory,
  enabled = true,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'detailed' | 'learning' | 'recommendations'>('overview');
  const [showExport, setShowExport] = useState(false);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | 'pdf'>('json');

  // Use the analytics hook
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
  } = useAccuracyAnalytics({
    recallHistory,
    expectedItems,
    enabled,
  });

  // Get palace stats
  const stats = getPalaceStats(palaceId);
  const sessionHistory: PalaceExerciseSession[] = stats.sessionHistory || [];

  // Calculate summary metrics
  const summaryMetrics = React.useMemo(() => {
    if (sessionHistory.length === 0) {
      return {
        totalSessions: 0,
        averageAccuracy: 0,
        totalItemsRecalled: 0,
        averageDuration: 0,
        bestAccuracy: 0,
        recentTrend: 'stable',
      };
    }

    const accuracies = sessionHistory.map(s => s.accuracy);
    const durations = sessionHistory.map(s => s.duration);
    const totalItems = sessionHistory.reduce((sum, s) => sum + s.totalItems, 0);

    // Calculate recent trend
    const recentTrend = calculateTrend(accuracies);

    return {
      totalSessions: sessionHistory.length,
      averageAccuracy: accuracies.reduce((a, b) => a + b, 0) / accuracies.length,
      totalItemsRecalled: totalItems,
      averageDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
      bestAccuracy: Math.max(...accuracies),
      recentTrend,
    };
  }, [sessionHistory]);

  const calculateTrend = (accuracies: number[]): 'improving' | 'declining' | 'stable' => {
    if (accuracies.length < 3) return 'stable';
    const recent = accuracies.slice(-3).reduce((a, b) => a + b, 0) / 3;
    const older = accuracies.slice(0, 3).reduce((a, b) => a + b, 0) / 3;
    if (recent > older + 0.1) return 'improving';
    if (recent < older - 0.1) return 'declining';
    return 'stable';
  };

  const handleExport = useCallback(() => {
    const exportData = {
      palaceId,
      palaceName,
      exportedAt: new Date().toISOString(),
      summary: summaryMetrics,
      currentMetrics,
      errorAnalysis,
      learningCurve,
      patterns,
      recommendations,
      progress,
      sessionHistory,
    };

    if (exportFormat === 'json') {
      const jsonString = JSON.stringify(exportData, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `memory_palace_analytics_${palaceId}_${Date.now()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } else if (exportFormat === 'csv') {
      // Convert to CSV
      const headers = ['Date', 'Accuracy', 'Duration', 'Items Recalled', 'Items Total'];
      const rows = sessionHistory.map(s => [
        new Date(s.startTime).toISOString(),
        s.accuracy.toFixed(2),
        s.duration,
        s.correctItems,
        s.totalItems,
      ]);
      const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `memory_palace_analytics_${palaceId}_${Date.now()}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }

    setShowExport(false);
  }, [palaceId, palaceName, summaryMetrics, currentMetrics, errorAnalysis, learningCurve, patterns, recommendations, progress, sessionHistory, exportFormat]);

  if (!enabled) {
    return null;
  }

  return (
    <div className="analytics-dashboard">
      <div className="analytics-header">
        <div className="analytics-title">
          <h2>📊 Memory Palace Analytics: {palaceName}</h2>
          <p className="subtitle">Comprehensive performance tracking and insights</p>
        </div>
        <div className="analytics-actions">
          <button
            onClick={refresh}
            className="btn btn-secondary btn-sm"
            disabled={isLoading}
          >
            {isLoading ? 'Refreshing...' : '🔄 Refresh'}
          </button>
          <button
            onClick={() => setShowExport(true)}
            className="btn btn-primary btn-sm"
          >
            📥 Export Data
          </button>
        </div>
      </div>

      {/* Export Modal */}
      {showExport && (
        <div className="export-modal-overlay">
          <div className="export-modal">
            <div className="export-modal-header">
              <h3>Export Analytics Data</h3>
              <button onClick={() => setShowExport(false)} className="btn-close">✕</button>
            </div>
            <div className="export-modal-body">
              <div className="export-options">
                <label className="export-option">
                  <input
                    type="radio"
                    name="exportFormat"
                    value="json"
                    checked={exportFormat === 'json'}
                    onChange={() => setExportFormat('json')}
                  />
                  <span>JSON (Full data)</span>
                </label>
                <label className="export-option">
                  <input
                    type="radio"
                    name="exportFormat"
                    value="csv"
                    checked={exportFormat === 'csv'}
                    onChange={() => setExportFormat('csv')}
                  />
                  <span>CSV (Session history)</span>
                </label>
              </div>
              <div className="export-info">
                <p><strong>JSON:</strong> Complete analytics data including all metrics, errors, and recommendations</p>
                <p><strong>CSV:</strong> Simplified session history for spreadsheet import</p>
              </div>
            </div>
            <div className="export-modal-footer">
              <button onClick={() => setShowExport(false)} className="btn btn-secondary">Cancel</button>
              <button onClick={handleExport} className="btn btn-primary">Export</button>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="analytics-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'detailed' ? 'active' : ''}`}
          onClick={() => setActiveTab('detailed')}
        >
          Detailed Analysis
        </button>
        <button
          className={`tab ${activeTab === 'learning' ? 'active' : ''}`}
          onClick={() => setActiveTab('learning')}
        >
          Learning Curve
        </button>
        <button
          className={`tab ${activeTab === 'recommendations' ? 'active' : ''}`}
          onClick={() => setActiveTab('recommendations')}
        >
          Recommendations
        </button>
      </div>

      {/* Tab Content */}
      <div className="analytics-content">
        {activeTab === 'overview' && (
          <OverviewTab
            summaryMetrics={summaryMetrics}
            currentMetrics={currentMetrics}
            errorAnalysis={errorAnalysis}
            recommendations={recommendations}
            progress={progress}
            learningCurve={learningCurve}
            isLoading={isLoading}
            error={error}
          />
        )}

        {activeTab === 'detailed' && (
          <DetailedTab
            currentMetrics={currentMetrics}
            errorAnalysis={errorAnalysis}
            patterns={patterns}
            sessionHistory={sessionHistory}
            summaryMetrics={summaryMetrics}
            isLoading={isLoading}
            error={error}
          />
        )}

        {activeTab === 'learning' && (
          <LearningTab
            learningCurve={learningCurve}
            patterns={patterns}
            recommendations={recommendations}
            isLoading={isLoading}
            error={error}
          />
        )}

        {activeTab === 'recommendations' && (
          <RecommendationsTab
            recommendations={recommendations}
            errorAnalysis={errorAnalysis}
            patterns={patterns}
            currentMetrics={currentMetrics}
            isLoading={isLoading}
            error={error}
          />
        )}
      </div>
    </div>
  );
};

// Overview Tab
interface OverviewTabProps {
  summaryMetrics: any;
  currentMetrics: RecallAccuracyMetrics | null;
  errorAnalysis: RecallErrorAnalysis[];
  recommendations: string[];
  progress: any;
  learningCurve: LearningCurvePoint[];
  isLoading: boolean;
  error: string | null;
}

const OverviewTab: React.FC<OverviewTabProps> = ({
  summaryMetrics,
  currentMetrics,
  errorAnalysis,
  recommendations,
  progress,
  learningCurve,
  isLoading,
  error,
}) => {
  const getAccuracyColor = (accuracy: number): string => {
    if (accuracy >= 80) return '#28a745';
    if (accuracy >= 60) return '#ffc107';
    return '#dc3545';
  };

  const getTrendIcon = (trend: string): string => {
    switch (trend) {
      case 'improving': return '📈';
      case 'declining': return '📉';
      default: return '➡️';
    }
  };

  if (isLoading) {
    return <div className="loading">Loading overview...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="overview-tab">
      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="summary-icon">🎯</div>
          <div className="summary-content">
            <div className="summary-label">Average Accuracy</div>
            <div className="summary-value" style={{ color: getAccuracyColor(summaryMetrics.averageAccuracy) }}>
              {summaryMetrics.averageAccuracy.toFixed(1)}%
            </div>
            <div className="summary-trend">
              {getTrendIcon(summaryMetrics.recentTrend)} {summaryMetrics.recentTrend}
            </div>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">📅</div>
          <div className="summary-content">
            <div className="summary-label">Total Sessions</div>
            <div className="summary-value">{summaryMetrics.totalSessions}</div>
            <div className="summary-subtext">Practice sessions completed</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">⏱️</div>
          <div className="summary-content">
            <div className="summary-label">Avg Duration</div>
            <div className="summary-value">
              {Math.floor(summaryMetrics.averageDuration / 60)}m {summaryMetrics.averageDuration % 60}s
            </div>
            <div className="summary-subtext">Per session</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-icon">🏆</div>
          <div className="summary-content">
            <div className="summary-label">Best Accuracy</div>
            <div className="summary-value" style={{ color: getAccuracyColor(summaryMetrics.bestAccuracy) }}>
              {summaryMetrics.bestAccuracy.toFixed(1)}%
            </div>
            <div className="summary-subtext">Peak performance</div>
          </div>
        </div>
      </div>

      {/* Current Performance */}
      <div className="analytics-section">
        <h3>Current Performance</h3>
        {currentMetrics ? (
          <div className="performance-grid">
            <div className="performance-card">
              <div className="accuracy-gauge">
                <svg width="120" height="120" viewBox="0 0 120 120">
                  <circle
                    cx="60"
                    cy="60"
                    r="50"
                    fill="none"
                    stroke="#e0e0e0"
                    strokeWidth="12"
                  />
                  <circle
                    cx="60"
                    cy="60"
                    r="50"
                    fill="none"
                    stroke={getAccuracyColor(currentMetrics.accuracy)}
                    strokeWidth="12"
                    strokeDasharray={314}
                    strokeDashoffset={314 - (currentMetrics.accuracy * 314)}
                    transform="rotate(-90 60 60)"
                  />
                </svg>
                <div className="accuracy-value">
                  {(currentMetrics.accuracy * 100).toFixed(0)}%
                </div>
              </div>
              <div className="accuracy-details">
                <div className="accuracy-detail">
                  <span className="detail-label">Correctly Recalled:</span>
                  <span className="detail-value">{currentMetrics.correctlyRecalled}/{currentMetrics.totalItems}</span>
                </div>
                <div className="accuracy-detail">
                  <span className="detail-label">Partially Recalled:</span>
                  <span className="detail-value">{currentMetrics.partiallyRecalled}</span>
                </div>
                <div className="accuracy-detail">
                  <span className="detail-label">Missed:</span>
                  <span className="detail-value">{currentMetrics.missed}</span>
                </div>
              </div>
            </div>

            <div className="performance-stats">
              <div className="stat-row">
                <span className="stat-label">Order Accuracy:</span>
                <span className="stat-value">{(currentMetrics.orderAccuracy * 100).toFixed(0)}%</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Recall Speed:</span>
                <span className="stat-value">{currentMetrics.recallSpeed.toFixed(1)}s/item</span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Confidence:</span>
                <span className="stat-value">{(currentMetrics.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        ) : (
          <p className="no-data">No current data available</p>
        )}
      </div>

      {/* Error Summary */}
      <div className="analytics-section">
        <h3>Error Summary</h3>
        {errorAnalysis.length > 0 ? (
          <div className="error-summary">
            <div className="error-count">
              <span className="error-count-number">{errorAnalysis.length}</span>
              <span className="error-count-label">errors detected</span>
            </div>
            <div className="error-types">
              {Array.from(new Set(errorAnalysis.map(e => e.errorType))).map(errorType => {
                const count = errorAnalysis.filter(e => e.errorType === errorType).length;
                return (
                  <div key={errorType} className="error-type-badge">
                    <span className="error-type-name">{errorType}</span>
                    <span className="error-type-count">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="no-errors">
            <span className="error-icon">✅</span>
            <p>No errors detected - excellent recall!</p>
          </div>
        )}
      </div>

      {/* Learning Curve Preview */}
      <div className="analytics-section">
        <h3>Learning Curve Preview</h3>
        {learningCurve.length > 0 ? (
          <div className="learning-curve-preview">
            <svg width="100%" height="100" viewBox="0 0 100 100" preserveAspectRatio="none">
              <defs>
                <linearGradient id="curveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style={{ stopColor: '#28a745', stopOpacity: 1 }} />
                  <stop offset="100%" style={{ stopColor: '#28a745', stopOpacity: 0.3 }} />
                </linearGradient>
              </defs>
              <polygon
                points={`0,100 ${learningCurve.map((d, i) => {
                  const x = (i / (learningCurve.length - 1)) * 100;
                  const y = 100 - (d.accuracy / Math.max(...learningCurve.map(d => d.accuracy), 0.5)) * 100;
                  return `${x},${y}`;
                }).join(' ')} 100,100`}
                fill="url(#curveGradient)"
              />
              <polyline
                points={learningCurve.map((d, i) => {
                  const x = (i / (learningCurve.length - 1)) * 100;
                  const y = 100 - (d.accuracy / Math.max(...learningCurve.map(d => d.accuracy), 0.5)) * 100;
                  return `${x},${y}`;
                }).join(' ')}
                fill="none"
                stroke="#28a745"
                strokeWidth="2"
              />
            </svg>
            <div className="curve-labels">
              <span>Session 1</span>
              <span>Session {learningCurve.length}</span>
            </div>
          </div>
        ) : (
          <p className="no-data">Not enough data to show learning curve</p>
        )}
      </div>

      {/* Quick Recommendations */}
      {recommendations.length > 0 && (
        <div className="analytics-section">
          <h3>Quick Recommendations</h3>
          <ul className="quick-recommendations">
            {recommendations.slice(0, 3).map((rec, index) => (
              <li key={index} className="recommendation-item">
                <span className="rec-icon">💡</span>
                {rec}
              </li>
            ))}
            {recommendations.length > 3 && (
              <li className="rec-more">
                +{recommendations.length - 3} more recommendations
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

// Detailed Tab
interface DetailedTabProps {
  currentMetrics: RecallAccuracyMetrics | null;
  errorAnalysis: RecallErrorAnalysis[];
  patterns: any;
  sessionHistory: PalaceExerciseSession[];
  summaryMetrics: any;
  isLoading: boolean;
  error: string | null;
}

const DetailedTab: React.FC<DetailedTabProps> = ({
  currentMetrics,
  errorAnalysis,
  patterns,
  sessionHistory,
  summaryMetrics,
  isLoading,
  error,
}) => {
  if (isLoading) {
    return <div className="loading">Loading detailed analysis...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="detailed-tab">
      {/* Error Analysis */}
      <div className="analytics-section">
        <h3>Error Analysis</h3>
        {errorAnalysis.length > 0 ? (
          <div className="error-analysis-list">
            {errorAnalysis.slice(0, 10).map((error, index) => (
              <div key={index} className="error-item">
                <div className="error-header">
                  <span className="error-type-badge">{error.errorType}</span>
                  <span className="error-position">
                    Position {error.positionExpected} → {error.positionRecalled ?? 'missed'}
                  </span>
                </div>
                <div className="error-details">
                  <div className="error-detail-row">
                    <span className="detail-label">Expected:</span>
                    <span className="detail-value">{JSON.stringify(error.expected)}</span>
                  </div>
                  <div className="error-detail-row">
                    <span className="detail-label">Recalled:</span>
                    <span className="detail-value">
                      {error.recalled ? JSON.stringify(error.recalled) : 'Not recalled'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            {errorAnalysis.length > 10 && (
              <div className="error-more">
                +{errorAnalysis.length - 10} more errors
              </div>
            )}
          </div>
        ) : (
          <div className="no-errors">
            <span className="error-icon">✅</span>
            <p>No errors detected - excellent recall!</p>
          </div>
        )}
      </div>

      {/* Patterns */}
      {patterns && Object.keys(patterns).length > 0 && (
        <div className="analytics-section">
          <h3>Identified Patterns</h3>
          <div className="patterns-grid">
            {Object.entries(patterns).map(([key, value]) => (
              <div key={key} className="pattern-card">
                <div className="pattern-icon">🔍</div>
                <div className="pattern-content">
                  <div className="pattern-label">{key}</div>
                  <div className="pattern-value">{value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Session History */}
      <div className="analytics-section">
        <h3>Session History</h3>
        {sessionHistory.length > 0 ? (
          <div className="session-history-table">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Accuracy</th>
                  <th>Duration</th>
                  <th>Items</th>
                </tr>
              </thead>
              <tbody>
                {sessionHistory.slice(0, 20).reverse().map((session, index) => (
                  <tr key={index}>
                    <td>{new Date(session.startTime).toLocaleDateString()}</td>
                    <td>
                      <span className="accuracy-badge" style={{
                        backgroundColor: session.accuracy >= 0.8 ? '#28a745' :
                          session.accuracy >= 0.6 ? '#ffc107' : '#dc3545'
                      }}>
                        {(session.accuracy * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td>{Math.floor(session.duration / 60)}m {session.duration % 60}s</td>
                    <td>{session.correctItems}/{session.totalItems}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {sessionHistory.length > 20 && (
              <div className="more-sessions">
                And {sessionHistory.length - 20} more sessions
              </div>
            )}
          </div>
        ) : (
          <p className="no-data">No session history available</p>
        )}
      </div>
    </div>
  );
};

// Learning Tab
interface LearningTabProps {
  learningCurve: LearningCurvePoint[];
  patterns: any;
  recommendations: string[];
  isLoading: boolean;
  error: string | null;
}

const LearningTab: React.FC<LearningTabProps> = ({
  learningCurve,
  patterns,
  recommendations,
  isLoading,
  error,
}) => {
  if (isLoading) {
    return <div className="loading">Loading learning curve...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="learning-tab">
      {/* Learning Curve Chart */}
      <div className="analytics-section">
        <h3>Learning Curve</h3>
        {learningCurve.length > 0 ? (
          <div className="learning-curve-chart">
            <svg width="100%" height="300" viewBox="0 0 100 100" preserveAspectRatio="none">
              <defs>
                <linearGradient id="curveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style={{ stopColor: '#28a745', stopOpacity: 1 }} />
                  <stop offset="100%" style={{ stopColor: '#28a745', stopOpacity: 0.3 }} />
                </linearGradient>
              </defs>
              <polygon
                points={`0,100 ${learningCurve.map((d, i) => {
                  const x = (i / (learningCurve.length - 1)) * 100;
                  const y = 100 - (d.accuracy / Math.max(...learningCurve.map(d => d.accuracy), 0.5)) * 100;
                  return `${x},${y}`;
                }).join(' ')} 100,100`}
                fill="url(#curveGradient)"
              />
              <polyline
                points={learningCurve.map((d, i) => {
                  const x = (i / (learningCurve.length - 1)) * 100;
                  const y = 100 - (d.accuracy / Math.max(...learningCurve.map(d => d.accuracy), 0.5)) * 100;
                  return `${x},${y}`;
                }).join(' ')}
                fill="none"
                stroke="#28a745"
                strokeWidth="2"
              />
              {learningCurve.map((d, i) => {
                const x = (i / (learningCurve.length - 1)) * 100;
                const y = 100 - (d.accuracy / Math.max(...learningCurve.map(d => d.accuracy), 0.5)) * 100;
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
              <span>Session 1</span>
              <span>Session {learningCurve.length}</span>
            </div>
            <div className="chart-tooltip">
              <p>Shows improvement over time. Steeper curve = faster learning.</p>
            </div>
          </div>
        ) : (
          <div className="no-data">
            <p>Not enough data to show learning curve</p>
            <p>Complete at least 3 sessions to see your learning progress</p>
          </div>
        )}
      </div>

      {/* Learning Patterns */}
      {patterns && Object.keys(patterns).length > 0 && (
        <div className="analytics-section">
          <h3>Learning Patterns</h3>
          <div className="patterns-grid">
            {Object.entries(patterns).map(([key, value]) => (
              <div key={key} className="pattern-card">
                <div className="pattern-icon">🔍</div>
                <div className="pattern-content">
                  <div className="pattern-label">{key}</div>
                  <div className="pattern-value">{value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Learning Recommendations */}
      {recommendations.length > 0 && (
        <div className="analytics-section">
          <h3>Learning Recommendations</h3>
          <ul className="learning-recommendations">
            {recommendations.map((rec, index) => (
              <li key={index} className="recommendation-item">
                <span className="rec-icon">💡</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Recommendations Tab
interface RecommendationsTabProps {
  recommendations: string[];
  errorAnalysis: RecallErrorAnalysis[];
  patterns: any;
  currentMetrics: RecallAccuracyMetrics | null;
  isLoading: boolean;
  error: string | null;
}

const RecommendationsTab: React.FC<RecommendationsTabProps> = ({
  recommendations,
  errorAnalysis,
  patterns,
  currentMetrics,
  isLoading,
  error,
}) => {
  if (isLoading) {
    return <div className="loading">Loading recommendations...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="recommendations-tab">
      <div className="analytics-section">
        <h3>Personalized Recommendations</h3>
        {recommendations.length > 0 ? (
          <ul className="recommendation-list">
            {recommendations.map((rec, index) => (
              <li key={index} className="recommendation-item">
                <span className="rec-icon">💡</span>
                {rec}
              </li>
            ))}
          </ul>
        ) : (
          <div className="no-recommendations">
            <p>No specific recommendations at this time.</p>
            <p>Keep practicing to get personalized suggestions!</p>
          </div>
        )}
      </div>

      {/* Error-Based Recommendations */}
      {errorAnalysis.length > 0 && (
        <div className="analytics-section">
          <h3>Error-Based Suggestions</h3>
          <div className="error-suggestions">
            {Array.from(new Set(errorAnalysis.map(e => e.errorType))).map(errorType => {
              const errors = errorAnalysis.filter(e => e.errorType === errorType);
              const suggestions = getSuggestionsForErrorType(errorType);
              return (
                <div key={errorType} className="error-suggestion-card">
                  <div className="error-suggestion-header">
                    <span className="error-type-badge">{errorType}</span>
                    <span className="error-count">{errors.length} occurrences</span>
                  </div>
                  <div className="suggestion-content">
                    <p className="suggestion-text">{suggestions}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Pattern-Based Recommendations */}
      {patterns && Object.keys(patterns).length > 0 && (
        <div className="analytics-section">
          <h3>Pattern-Based Insights</h3>
          <div className="patterns-grid">
            {Object.entries(patterns).map(([key, value]) => (
              <div key={key} className="pattern-card">
                <div className="pattern-icon">🔍</div>
                <div className="pattern-content">
                  <div className="pattern-label">{key}</div>
                  <div className="pattern-value">{value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance-Based Recommendations */}
      {currentMetrics && (
        <div className="analytics-section">
          <h3>Performance Insights</h3>
          <div className="performance-insights">
            <div className="insight-item">
              <span className="insight-icon">🎯</span>
              <div className="insight-content">
                <div className="insight-label">Accuracy</div>
                <div className="insight-value">{(currentMetrics.accuracy * 100).toFixed(0)}%</div>
              </div>
            </div>
            <div className="insight-item">
              <span className="insight-icon">⏱️</span>
              <div className="insight-content">
                <div className="insight-label">Recall Speed</div>
                <div className="insight-value">{currentMetrics.recallSpeed.toFixed(1)}s/item</div>
              </div>
            </div>
            <div className="insight-item">
              <span className="insight-icon">🧠</span>
              <div className="insight-content">
                <div className="insight-label">Confidence</div>
                <div className="insight-value">{(currentMetrics.confidence * 100).toFixed(0)}%</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function to get suggestions for error types
const getSuggestionsForErrorType = (errorType: string): string => {
  const suggestions: Record<string, string> = {
    omission: 'Focus on remembering all items. Try using a checklist or counting method during recall.',
    substitution: 'Pay attention to details. Use vivid mental imagery to distinguish similar items.',
    transposition: 'Practice the order of items. Use spatial memory techniques to remember sequences.',
    distortion: 'Review the original information carefully. Create clear, distinct mental images.',
    hallucination: 'Be careful not to add information that wasn\'t there. Stick to what you actually memorized.',
  };
  return suggestions[errorType] || 'Practice more to improve recall accuracy.';
};

export default AnalyticsDashboard;
