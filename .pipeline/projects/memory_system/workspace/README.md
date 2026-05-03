# Memory System

A comprehensive memory and spaced repetition system built with TypeScript and React.

## Overview

This project implements a sophisticated spaced repetition algorithm inspired by SM-2 (SuperMemo 2) with additional features for difficulty adaptation and intelligent scheduling. The system is designed to optimize long-term retention through scientifically-backed review scheduling.

## Features

- **SM-2 Inspired Algorithm**: Uses proven spaced repetition principles with configurable parameters
- **Difficulty Adaptation**: Automatically adjusts difficulty based on performance
- **Priority-Based Scheduling**: Items are prioritized based on urgency and importance
- **Status Tracking**: Tracks new, learning, review, and mastered items
- **Session Analytics**: Comprehensive statistics and session tracking
- **React Hooks**: Easy-to-use hooks for integration with React applications
- **Persistent Storage**: Automatic saving to localStorage
- **Type-Safe**: Full TypeScript support with comprehensive type definitions

## Installation

```bash
npm install
npm run dev
```

## Quick Start

### Basic Usage

```typescript
import { useSpacedRepetition } from './hooks/useSpacedRepetition';

function MemoryApp() {
  const {
    addItem,
    reviewItem,
    getDueItemsForReview,
    stats,
  } = useSpacedRepetition();

  // Add a new item
  addItem('item-1', {
    reason: 'First vocabulary word',
  });

  // Get items due for review
  const dueItems = getDueItemsForReview(10);

  // Review an item
  reviewItem('item-1', 'good');

  // Get statistics
  console.log(stats);
}
```

### Advanced Usage with Custom Parameters

```typescript
import { useSpacedRepetition } from './hooks/useSpacedRepetition';
import { SpacedRepetitionParams } from './types/spacedRepetition';

const customParams: SpacedRepetitionParams = {
  initialInterval: 1,
  minimumInterval: 1,
  maximumInterval: 365,
  easeFactorDecay: 0.3,
  easeFactorIncrease: 0.15,
  easeFactorMinimum: 1.3,
  targetRetention: 0.9,
};

function AdvancedMemoryApp() {
  const {
    addItem,
    adaptDifficulty,
    completeSession,
  } = useSpacedRepetition(customParams);

  // Add item with custom schedule
  addItem('item-1', {
    scheduledDate: new Date().toISOString(),
    difficulty: 'hard',
    priority: 5,
    reason: 'Important concept',
  });

  // Adapt difficulty based on accuracy
  const adaptation = adaptDifficulty('item-1', 0.95);

  // Complete a review session
  completeSession(10, 8, ['good', 'good', 'easy'], 180);
}
```

## Architecture

### Core Components

1. **Spaced Repetition Engine** (`src/utils/spacedRepetition.ts`)
   - SM-2 algorithm implementation
   - Difficulty adaptation logic
   - Scheduling and priority management
   - Statistics calculation

2. **React Hooks** (`src/hooks/`)
   - `useSpacedRepetition`: Main hook for managing items and schedules
   - `useReviewQueue`: Hook for managing review queue
   - `useReviewSession`: Hook for managing review sessions

3. **Type Definitions** (`src/types/`)
   - Comprehensive TypeScript types for all components
   - Type-safe API interactions

### Data Flow

```
User Action
    ↓
Hook (useSpacedRepetition)
    ↓
Utils (spacedRepetition)
    ↓
State Management
    ↓
localStorage (Persistence)
```

## API Reference

### Types

#### DifficultyLevel
```typescript
type DifficultyLevel = 'very_easy' | 'easy' | 'medium' | 'hard' | 'very_hard';
```

#### RecallQuality
```typescript
type RecallQuality = 'again' | 'hard' | 'good' | 'easy';
```

#### SpacedRepetitionParams
```typescript
interface SpacedRepetitionParams {
  initialInterval: number;      // Initial interval in days
  minimumInterval: number;      // Minimum interval in days
  maximumInterval: number;      // Maximum interval in days
  easeFactorDecay: number;      // How much ease factor decreases on failure
  easeFactorIncrease: number;   // How much ease factor increases on success
  easeFactorMinimum: number;    // Minimum ease factor
  targetRetention: number;      // Target retention rate (0-1)
}
```

### Functions

#### calculateNextInterval
```typescript
function calculateNextInterval(
  easeFactor: number,
  quality: RecallQuality,
  currentInterval: number,
  params?: SpacedRepetitionParams
): number;
```
Calculates the next review interval based on the SM-2 algorithm.

#### updateEaseFactor
```typescript
function updateEaseFactor(
  currentEaseFactor: number,
  quality: RecallQuality,
  params?: SpacedRepetitionParams
): number;
```
Updates the ease factor based on recall quality.

#### adaptDifficulty
```typescript
function adaptDifficulty(
  previousDifficulty: DifficultyLevel,
  accuracy: number,
  params?: SpacedRepetitionParams
): DifficultyAdaptationResult;
```
Adapts difficulty based on performance accuracy.

#### getDueItems
```typescript
function getDueItems(
  schedules: Record<string, SpacedRepetitionSchedule>,
  now?: Date
): ReviewQueueItem[];
```
Gets all items due for review, sorted by priority.

#### calculateSpacedRepetitionStats
```typescript
function calculateSpacedRepetitionStats(
  schedules: Record<string, SpacedRepetitionSchedule>,
  now?: Date
): SpacedRepetitionStats;
```
Calculates comprehensive statistics for the spaced repetition system.

### React Hooks

#### useSpacedRepetition
```typescript
const {
  schedules,
  difficultyConfigs,
  sessionResults,
  isLoading,
  error,
  stats,
  addItem,
  removeItem,
  reviewItem,
  getDueItemsForReview,
  getItemsByStatus,
  getItemsDueInRange,
  completeSession,
  adaptDifficulty,
  resetItem,
  clearAll,
} = useSpacedRepetition(params?);
```

#### useReviewQueue
```typescript
const {
  queue,
  isLoading,
  totalDue,
  estimatedTime,
} = useReviewQueue(params?);
```

#### useReviewSession
```typescript
const {
  currentSession,
  startSession,
  recordReview,
  endSession,
  resetSession,
} = useReviewSession();
```

## Algorithm Details

### SM-2 Algorithm

The system uses a modified SM-2 algorithm:

1. **Initial Review**: First successful recall sets interval to 1 day
2. **Second Review**: Second successful recall sets interval to 6 days
3. **Subsequent Reviews**: Interval = previous_interval × ease_factor
4. **Ease Factor**: Starts at 2.5, increases on success, decreases on failure
5. **Failure**: Resets to initial interval and decreases ease factor

### Difficulty Adaptation

The system adapts difficulty based on performance:

- **High Accuracy (≥90%)**: Increases difficulty
- **Low Accuracy (≤50%)**: Decreases difficulty
- **Good Accuracy (70-80%)**: Slight increase with probability
- **Acceptable Accuracy (80-90%)**: Slight decrease with probability

## Configuration

### Default Parameters

```typescript
const DEFAULT_SPACED_REPETITION_PARAMS = {
  initialInterval: 1,      // 1 day
  minimumInterval: 1,      // 1 day
  maximumInterval: 365,    // 1 year
  easeFactorDecay: 0.3,
  easeFactorIncrease: 0.15,
  easeFactorMinimum: 1.3,
  targetRetention: 0.9,    // 90% retention target
};
```

### Custom Configuration

You can customize the algorithm by passing parameters:

```typescript
const customParams = {
  initialInterval: 2,      // Start with 2 days
  minimumInterval: 1,
  maximumInterval: 365,
  easeFactorDecay: 0.2,    // Less decay on failure
  easeFactorIncrease: 0.2, // More increase on success
  easeFactorMinimum: 1.4,
  targetRetention: 0.95,   // Higher retention target
};
```

## Performance

### Time Complexity

- **calculateNextInterval**: O(1)
- **updateEaseFactor**: O(1)
- **adaptDifficulty**: O(1)
- **getDueItems**: O(n log n) - sorting by priority
- **calculateSpacedRepetitionStats**: O(n)

### Space Complexity

- **Schedules**: O(n) where n is number of items
- **Difficulty Configs**: O(n)
- **Session Results**: O(m) where m is number of sessions

## Testing

Run the test suite:

```bash
npm run test
```

Tests cover:
- Algorithm calculations
- Hook behavior
- Edge cases
- Performance scenarios

## Best Practices

1. **Regular Reviews**: Review items consistently for best retention
2. **Accurate Ratings**: Rate your recall honestly for better adaptation
3. **Priority Management**: Use priority to focus on important items
4. **Session Tracking**: Complete sessions to track progress
5. **Difficulty Adjustment**: Use adaptDifficulty for fine-tuning

## Troubleshooting

### Items Not Appearing in Review Queue

- Check if scheduled date is in the past
- Verify item hasn't been mastered
- Check priority settings

### Difficulty Not Adapting

- Ensure accuracy is between 0 and 1
- Check if item exists in difficulty configs
- Verify adaptation logic is correct

### Performance Issues

- Limit number of items reviewed at once
- Use pagination for large datasets
- Optimize localStorage operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on the repository.
