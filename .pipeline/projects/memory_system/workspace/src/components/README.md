# Analytics Dashboard

A comprehensive analytics dashboard for tracking and analyzing memory palace training progress.

## Overview

The Analytics Dashboard provides detailed insights into your memory palace performance, including:

- **Overview Tab**: Quick summary of current metrics, error analysis, and learning patterns
- **Detailed Analysis Tab**: In-depth error analysis and session history
- **Learning Curve Tab**: Visual representation of accuracy improvement over time
- **Recommendations Tab**: Personalized suggestions for improvement

## Features

### Current Metrics
- **Accuracy**: Average recall accuracy across recent sessions
- **Recall Speed**: Average time per item
- **Confidence**: Average self-reported confidence level

### Error Analysis
- **Omission**: Items that were forgotten
- **Substitution**: Wrong items recalled at specific positions
- **Transposition**: Items recalled in wrong order
- **Insertion**: Extra items added that weren't in the original sequence

### Learning Patterns
- **Recall Speed Variability**: Consistency of recall speed
- **Accuracy Trend**: Whether accuracy is improving, declining, or stable
- **Average Confidence**: Typical confidence level during recalls
- **Most Common Error**: Primary error type to focus on

### Personalized Recommendations
- Accuracy-based suggestions
- Speed optimization tips
- Confidence building strategies
- Error-specific improvement techniques

## Installation

```bash
npm install
```

## Usage

### Basic Usage

```tsx
import { AnalyticsDashboard } from './components/AnalyticsDashboard';

function MyComponent() {
  const palaceId = 'test-palace';
  const attempts = useRecallAttempts(palaceId);
  const palaceStats = getPalaceStats(palaceId);

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

### With Custom Props

```tsx
<AnalyticsDashboard
  palaceId="my-palace"
  attempts={recallAttempts}
  palaceStats={palaceStats}
  enabled={true}
  onRefresh={handleRefresh}
  onExport={handleExport}
  onRecommendationClick={handleRecommendationClick}
  showExportButton={true}
  showSessionHistory={true}
  maxRecentSessions={10}
  accuracyWindow={5}
  learningCurveMaxSessions={20}
  className="custom-class"
/>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `palaceId` | `string` | required | Unique identifier for the memory palace |
| `attempts` | `RecallAttempt[]` | `[]` | Array of recall attempt records |
| `palaceStats` | `PalaceStats \| null` | `null` | Current palace statistics |
| `enabled` | `boolean` | `true` | Whether the dashboard is enabled |
| `onRefresh` | `() => void` | `undefined` | Callback when refresh is triggered |
| `onExport` | `() => void` | `undefined` | Callback when export is triggered |
| `onRecommendationClick` | `(rec: string) => void` | `undefined` | Callback when recommendation is clicked |
| `showExportButton` | `boolean` | `true` | Whether to show export button |
| `showSessionHistory` | `boolean` | `true` | Whether to show session history |
| `maxRecentSessions` | `number` | `10` | Maximum recent sessions to display |
| `accuracyWindow` | `number` | `5` | Number of recent attempts for metrics |
| `learningCurveMaxSessions` | `number` | `20` | Maximum sessions for learning curve |
| `className` | `string` | `undefined` | Additional CSS classes |

## Data Models

### RecallAttempt

```typescript
interface RecallAttempt {
  id: string;
  palaceId: string;
  timestamp: string;
  items: string[];
  accuracy: number;
  duration: number;
  confidence: number;
  errors: Array<{
    errorType: 'omission' | 'substitution' | 'transposition' | 'insertion';
    positionExpected: number;
    positionRecalled: number | undefined;
    expected: string;
    recalled: string | undefined;
  }>;
}
```

### PalaceStats

```typescript
interface PalaceStats {
  sessionHistory: Array<{
    startTime: string;
    endTime?: string;
    accuracy: number;
    duration: number;
    totalItems: number;
    correctItems: number;
    confidence: number;
  }>;
  totalSessions: number;
  averageAccuracy: number;
  averageDuration: number;
  lastSessionDate: string | null;
}
```

## Utility Functions

### calculateCurrentMetrics

Calculates current performance metrics from recent recall attempts.

```typescript
const metrics = calculateCurrentMetrics(attempts, 5);
// Returns: { accuracy: number, recallSpeed: number, confidence: number } | null
```

### analyzeErrors

Analyzes errors from recall attempts.

```typescript
const { errorAnalysis, errorCounts } = analyzeErrors(attempts);
// Returns: { errorAnalysis: ErrorAnalysis[], errorCounts: Record<string, number> }
```

### buildLearningCurve

Builds learning curve data from recall history.

```typescript
const curve = buildLearningCurve(attempts, 20);
// Returns: LearningCurveData[]
```

### identifyPatterns

Identifies learning patterns from recall history.

```typescript
const patterns = identifyPatterns(attempts, palaceStats);
// Returns: LearningPattern[]
```

### generateRecommendations

Generates personalized recommendations based on analytics.

```typescript
const recommendations = generateRecommendations(currentMetrics, errorAnalysis, patterns, attempts);
// Returns: { general: string[], errorSpecific: { errorType: string, suggestions: string[] }[] }
```

### useAccuracyAnalytics

Main hook for accuracy analytics.

```typescript
const analytics = useAccuracyAnalytics(palaceId, attempts, palaceStats);
// Returns: {
//   currentMetrics: CurrentMetrics | null,
//   errorAnalysis: ErrorAnalysis[],
//   errorCounts: Record<string, number>,
//   learningCurve: LearningCurveData[],
//   patterns: LearningPattern[],
//   recommendations: Recommendations,
//   progress: Progress,
//   isLoading: boolean,
//   error: string | null,
//   refresh: () => Promise<void>
// }
```

## Styling

The component uses Tailwind CSS for styling. You can customize the appearance by:

1. Passing custom CSS classes via the `className` prop
2. Overriding Tailwind classes in your global styles
3. Using Tailwind's arbitrary values for inline customization

## Testing

Run the test suite:

```bash
npm test
```

The component includes comprehensive tests covering:
- Tab switching functionality
- Metrics display
- Error analysis display
- Learning recommendations
- Loading and error states
- Export functionality
- Session history
- Edge cases (empty data, null values, disabled state)

## Best Practices

1. **Regular Updates**: Call `refresh()` periodically to update analytics with new data
2. **Error Handling**: Always check for errors before displaying analytics
3. **Performance**: Limit the number of sessions displayed in learning curves for large datasets
4. **Accessibility**: The component includes ARIA labels and keyboard navigation support
5. **Responsive Design**: The component adapts to different screen sizes automatically

## Troubleshooting

### Analytics not updating
- Ensure `refresh()` is called after new recall attempts
- Check that `palaceId` is consistent across components
- Verify that localStorage is accessible

### Empty data display
- Ensure recall attempts are being recorded
- Check that palace stats are being saved
- Verify that the `palaceId` matches between components

### Performance issues with large datasets
- Reduce `accuracyWindow` and `learningCurveMaxSessions` props
- Consider implementing pagination for session history
- Use virtualization for long lists

## License

MIT License - feel free to use and modify as needed.
