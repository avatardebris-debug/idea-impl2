# Analytics Dashboard

A comprehensive analytics dashboard for tracking and analyzing memory palace training progress.

## Overview

The Analytics Dashboard provides detailed insights into your memory palace performance, including:

- **Overview Tab**: Quick summary of current performance metrics
- **Error Analysis**: Detailed breakdown of recall errors
- **Learning Curve**: Visual representation of progress over time
- **Recommendations**: Personalized suggestions for improvement

## Features

### Real-time Analytics

- **Accuracy Tracking**: Monitor your recall accuracy over time
- **Speed Analysis**: Track how quickly you can recall items
- **Confidence Scoring**: Measure your confidence in recalled items
- **Error Detection**: Automatically identify and categorize errors

### Error Analysis

The system automatically categorizes errors into four types:

1. **Omission**: Items that were not recalled at all
2. **Substitution**: Items that were recalled incorrectly
3. **Transposition**: Items that were recalled in the wrong order
4. **Insertion**: Extra items that were not in the original list

### Learning Patterns

The system identifies patterns in your learning behavior:

- **Recall Speed Trends**: How your speed changes over time
- **Accuracy Trends**: How your accuracy improves or declines
- **Confidence Correlation**: Relationship between confidence and accuracy
- **Error Patterns**: Common types of errors you make

### Personalized Recommendations

Based on your performance, the system provides actionable recommendations:

- **General Recommendations**: Broad suggestions for improvement
- **Error-Specific Recommendations**: Targeted advice for specific error types

## Installation

```bash
npm install @memory-system/analytics-dashboard
```

## Usage

### Basic Usage

```tsx
import { AnalyticsDashboard } from '@memory-system/analytics-dashboard';

function MyMemoryPalace() {
  const palaceId = 'my-palace';
  const [attempts, setAttempts] = useState<RecallAttempt[]>([]);
  const [palaceStats, setPalaceStats] = useState<PalaceStats | null>(null);

  return (
    <AnalyticsDashboard
      palaceId={palaceId}
      attempts={attempts}
      palaceStats={palaceStats}
      enabled={true}
    />
  );
}
```

### With Custom Analytics Hook

```tsx
import { useAccuracyAnalytics } from '@memory-system/analytics-dashboard';

function MyMemoryPalace() {
  const palaceId = 'my-palace';
  const [attempts, setAttempts] = useState<RecallAttempt[]>([]);
  const [palaceStats, setPalaceStats] = useState<PalaceStats | null>(null);

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
  } = useAccuracyAnalytics(palaceId, attempts, palaceStats);

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
```

### Manual Analytics Calculation

```tsx
import {
  calculateCurrentMetrics,
  analyzeErrors,
  buildLearningCurve,
  identifyPatterns,
  generateRecommendations,
} from '@memory-system/analytics-dashboard';

function MyMemoryPalace() {
  const palaceId = 'my-palace';
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
    </div>
  );
}
```

## Props

### AnalyticsDashboard Component

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `palaceId` | `string` | Yes | Unique identifier for the memory palace |
| `attempts` | `RecallAttempt[]` | Yes | Array of recall attempts |
| `palaceStats` | `PalaceStats \| null` | Yes | Current palace statistics |
| `enabled` | `boolean` | Yes | Whether analytics are enabled |
| `onRecallComplete` | `function` | No | Callback when a recall session completes |
| `onError` | `function` | No | Callback when an error occurs |
| `onRecommendationClick` | `function` | No | Callback when a recommendation is clicked |

## Types

### RecallAttempt

```typescript
interface RecallAttempt {
  id: string;
  palaceId: string;
  timestamp: string;
  items: string[];
  recalledItems: string[];
  accuracy: number;
  duration: number;
  confidence: number;
  errors: ErrorAnalysis[];
}
```

### PalaceStats

```typescript
interface PalaceStats {
  sessionHistory: SessionData[];
  totalSessions: number;
  averageAccuracy: number;
  averageDuration: number;
  lastSessionDate: string | null;
}
```

### CurrentMetrics

```typescript
interface CurrentMetrics {
  accuracy: number;
  recallSpeed: number;
  confidence: number;
  totalItems: number;
  correctItems: number;
  errorRate: number;
}
```

### ErrorAnalysis

```typescript
interface ErrorAnalysis {
  errorType: 'omission' | 'substitution' | 'transposition' | 'insertion';
  positionExpected: number;
  positionRecalled: number | undefined;
  expected: string;
  recalled: string | undefined;
}
```

### LearningPattern

```typescript
interface LearningPattern {
  label: string;
  value: string | number;
  trend: 'improving' | 'declining' | 'stable';
  significance: 'high' | 'medium' | 'low';
}
```

### Recommendations

```typescript
interface Recommendations {
  general: string[];
  errorSpecific: {
    errorType: string;
    suggestions: string[];
  }[];
}
```

## Hooks

### useAccuracyAnalytics

```typescript
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
} = useAccuracyAnalytics(palaceId, attempts, palaceStats);
```

**Returns:**

- `currentMetrics`: Current performance metrics
- `errorAnalysis`: Array of error analyses
- `learningCurve`: Learning curve data
- `patterns`: Identified learning patterns
- `recommendations`: Personalized recommendations
- `progress`: Overall progress percentage
- `isLoading`: Loading state
- `error`: Error state
- `refresh`: Function to refresh analytics

## Functions

### calculateCurrentMetrics

Calculates current performance metrics from recall attempts.

```typescript
const metrics = calculateCurrentMetrics(attempts, windowSize);
```

**Parameters:**

- `attempts`: Array of recall attempts
- `windowSize`: Number of recent attempts to consider (default: 5)

**Returns:** `CurrentMetrics`

### analyzeErrors

Analyzes errors from recall attempts.

```typescript
const { errorAnalysis, errorCounts } = analyzeErrors(attempts);
```

**Parameters:**

- `attempts`: Array of recall attempts

**Returns:**

- `errorAnalysis`: Array of error analyses
- `errorCounts`: Count of each error type

### buildLearningCurve

Builds a learning curve from recall attempts.

```typescript
const curve = buildLearningCurve(attempts, maxSessions);
```

**Parameters:**

- `attempts`: Array of recall attempts
- `maxSessions`: Maximum number of sessions to include (default: 20)

**Returns:** `LearningCurveData[]`

### identifyPatterns

Identifies learning patterns from recall attempts.

```typescript
const patterns = identifyPatterns(attempts, palaceStats);
```

**Parameters:**

- `attempts`: Array of recall attempts
- `palaceStats`: Current palace statistics

**Returns:** `LearningPattern[]`

### generateRecommendations

Generates personalized recommendations based on analytics.

```typescript
const recommendations = generateRecommendations(
  currentMetrics,
  errorAnalysis,
  patterns,
  attempts
);
```

**Parameters:**

- `currentMetrics`: Current performance metrics
- `errorAnalysis`: Array of error analyses
- `patterns`: Identified learning patterns
- `attempts`: Array of recall attempts

**Returns:** `Recommendations`

### getPalaceStats

Retrieves palace statistics from storage.

```typescript
const stats = getPalaceStats(palaceId);
```

**Parameters:**

- `palaceId`: Unique identifier for the memory palace

**Returns:** `PalaceStats | null`

### savePalaceStats

Saves palace statistics to storage.

```typescript
savePalaceStats(palaceId, stats);
```

**Parameters:**

- `palaceId`: Unique identifier for the memory palace
- `stats`: Palace statistics to save

### addSessionToStats

Adds a new session to palace statistics.

```typescript
const updatedStats = addSessionToStats(palaceId, sessionData);
```

**Parameters:**

- `palaceId`: Unique identifier for the memory palace
- `sessionData`: Session data to add

**Returns:** Updated `PalaceStats`

### getRecentSessions

Retrieves recent sessions from palace statistics.

```typescript
const sessions = getRecentSessions(palaceId, limit);
```

**Parameters:**

- `palaceId`: Unique identifier for the memory palace
- `limit`: Maximum number of sessions to retrieve (default: 10)

**Returns:** `SessionData[]`

### getAccuracyTrend

Analyzes the trend of accuracy over recent sessions.

```typescript
const trend = getAccuracyTrend(palaceId, windowSize);
```

**Parameters:**

- `palaceId`: Unique identifier for the memory palace
- `windowSize`: Number of recent sessions to consider (default: 5)

**Returns:** `AccuracyTrend`

### calculateAccuracy

Calculates accuracy for a recall attempt.

```typescript
const accuracy = calculateAccuracy(items, recalledItems);
```

**Parameters:**

- `items`: Original items
- `recalledItems`: Recalled items

**Returns:** `number` (0-1)

### detectErrors

Detects errors in a recall attempt.

```typescript
const errors = detectErrors(items, recalledItems);
```

**Parameters:**

- `items`: Original items
- `recalledItems`: Recalled items

**Returns:** `ErrorAnalysis[]`

### createRecallAttempt

Creates a new recall attempt.

```typescript
const attempt = createRecallAttempt(palaceId, items, recalledItems, duration, confidence);
```

**Parameters:**

- `palaceId`: Unique identifier for the memory palace
- `items`: Original items
- `recalledItems`: Recalled items
- `duration`: Duration in seconds
- `confidence`: Confidence score (0-1)

**Returns:** `RecallAttempt`

### generateAttemptId

Generates a unique ID for a recall attempt.

```typescript
const id = generateAttemptId();
```

**Returns:** `string`

## Error Types

The system automatically categorizes errors into four types:

1. **Omission**: Items that were not recalled at all
2. **Substitution**: Items that were recalled incorrectly
3. **Transposition**: Items that were recalled in the wrong order
4. **Insertion**: Extra items that were not in the original list

## Recommendations

### General Recommendations

- **High Accuracy (>90%)**: "Your performance is excellent. Consider increasing the difficulty."
- **Good Accuracy (70-90%)**: "Good progress! Focus on consistency."
- **Moderate Accuracy (50-70%)**: "Keep practicing. Focus on visualization techniques."
- **Low Accuracy (<50%)**: "Consider taking a break and reviewing your techniques."

### Error-Specific Recommendations

#### Omission Errors
- Strengthen your visualization of the item
- Create a more memorable association
- Practice recalling items in smaller groups

#### Substitution Errors
- Focus on the unique characteristics of each item
- Create distinct visual markers for each item
- Practice distinguishing between similar items

#### Transposition Errors
- Strengthen the sequence of locations
- Create a clear path through your palace
- Practice recalling items in order

#### Insertion Errors
- Be more careful about what you visualize
- Review your original list before recalling
- Practice focusing on only the target items

## Styling

The Analytics Dashboard uses CSS modules for styling. You can customize the appearance by overriding the CSS variables:

```css
:root {
  --analytics-bg-color: #ffffff;
  --analytics-text-color: #333333;
  --analytics-primary-color: #007bff;
  --analytics-success-color: #28a745;
  --analytics-warning-color: #ffc107;
  --analytics-danger-color: #dc3545;
  --analytics-border-color: #dee2e6;
  --analytics-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

## Performance

The Analytics Dashboard is optimized for performance:

- **Memoization**: Uses React.memo and useMemo to prevent unnecessary re-renders
- **Lazy Loading**: Loads analytics data on demand
- **Debouncing**: Debounces rapid updates to prevent excessive calculations
- **Efficient Algorithms**: Uses efficient algorithms for error detection and pattern recognition

## Accessibility

The Analytics Dashboard is designed with accessibility in mind:

- **Keyboard Navigation**: Full keyboard navigation support
- **Screen Reader Support**: ARIA labels and roles for screen readers
- **Color Contrast**: Meets WCAG 2.1 AA contrast requirements
- **Focus Management**: Proper focus management for interactive elements

## Troubleshooting

### Analytics Not Updating

If analytics are not updating, check:

1. That `palaceId` is consistent across all components
2. That `attempts` array is being updated correctly
3. That `palaceStats` is being passed to the component
4. That the `enabled` prop is set to `true`

### Recommendations Not Appearing

If recommendations are not appearing, check:

1. That you have enough recall attempts (at least 3)
2. That `currentMetrics`, `errorAnalysis`, and `patterns` are being calculated correctly
3. That the `generateRecommendations` function is being called with the correct parameters

### Error Analysis Not Showing

If error analysis is not showing, check:

1. That recall attempts have errors detected
2. That the `analyzeErrors` function is being called correctly
3. That the error data is being passed to the component

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting a pull request.

## License

MIT License - feel free to use this in your projects!

## Support

For support, please open an issue on the GitHub repository.

## Examples

See the [examples directory](./src/examples/) for complete examples of how to use the Analytics Dashboard.

## Changelog

### 1.0.0
- Initial release
- Basic analytics dashboard
- Error analysis
- Learning curve visualization
- Personalized recommendations
- Real-time analytics hook
- Export functionality
- Trend analysis
