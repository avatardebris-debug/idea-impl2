import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AnalyticsDashboard from '../src/components/AnalyticsDashboard';
import { useAccuracyAnalytics } from '../src/utils/accuracyAnalytics';
import { getPalaceStats } from '../src/utils/progressTracking';

// Mock the hooks and utilities
vi.mock('../src/utils/accuracyAnalytics', () => ({
  useAccuracyAnalytics: vi.fn(),
}));

vi.mock('../src/utils/progressTracking', () => ({
  getPalaceStats: vi.fn(),
}));

describe('AnalyticsDashboard', () => {
  const defaultProps = {
    palaceId: 'test-palace-1',
    palaceName: 'Test Palace',
    expectedItems: ['item1', 'item2', 'item3'],
    recallHistory: [
      {
        id: 'attempt-1',
        palaceId: 'test-palace-1',
        timestamp: new Date('2024-01-01').toISOString(),
        items: ['item1', 'item2', 'item3'],
        accuracy: 1.0,
        duration: 60,
        confidence: 0.9,
        errors: [],
      },
      {
        id: 'attempt-2',
        palaceId: 'test-palace-1',
        timestamp: new Date('2024-01-02').toISOString(),
        items: ['item1', 'item2'],
        accuracy: 0.67,
        duration: 45,
        confidence: 0.7,
        errors: [
          {
            errorType: 'omission',
            positionExpected: 2,
            positionRecalled: undefined,
            expected: 'item3',
            recalled: undefined,
          },
        ],
      },
    ],
    enabled: true,
  };

  const mockPalaceStats = {
    sessionHistory: [
      {
        startTime: new Date('2024-01-01').toISOString(),
        accuracy: 1.0,
        duration: 60,
        totalItems: 3,
        correctItems: 3,
      },
      {
        startTime: new Date('2024-01-02').toISOString(),
        accuracy: 0.67,
        duration: 45,
        totalItems: 3,
        correctItems: 2,
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the dashboard header with palace name', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText(/Memory Palace Analytics: Test Palace/i)).toBeInTheDocument();
  });

  it('renders all tab buttons', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Detailed Analysis')).toBeInTheDocument();
    expect(screen.getByText('Learning Curve')).toBeInTheDocument();
    expect(screen.getByText('Recommendations')).toBeInTheDocument();
  });

  it('renders Overview tab by default', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Average Accuracy')).toBeInTheDocument();
    expect(screen.getByText('Total Sessions')).toBeInTheDocument();
  });

  it('switches to Detailed Analysis tab when clicked', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    const detailedTab = screen.getByText('Detailed Analysis');
    fireEvent.click(detailedTab);

    expect(screen.getByText('Detailed Analysis')).toHaveClass('active');
  });

  it('switches to Learning Curve tab when clicked', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    const learningTab = screen.getByText('Learning Curve');
    fireEvent.click(learningTab);

    expect(screen.getByText('Learning Curve')).toHaveClass('active');
  });

  it('switches to Recommendations tab when clicked', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    const recommendationsTab = screen.getByText('Recommendations');
    fireEvent.click(recommendationsTab);

    expect(screen.getByText('Recommendations')).toHaveClass('active');
  });

  it('displays current accuracy metrics when available', () => {
    const mockMetrics = {
      accuracy: 0.85,
      recallSpeed: 45.5,
      confidence: 0.75,
    };

    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: mockMetrics,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByText('45.5s/item')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('displays error analysis when errors exist', () => {
    const mockErrorAnalysis = [
      {
        errorType: 'omission',
        positionExpected: 2,
        positionRecalled: undefined,
        expected: 'item3',
        recalled: undefined,
      },
      {
        errorType: 'substitution',
        positionExpected: 1,
        positionRecalled: 1,
        expected: 'item2',
        recalled: 'itemX',
      },
    ];

    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: mockErrorAnalysis,
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('2 Errors')).toBeInTheDocument();
    expect(screen.getByText('Omission')).toBeInTheDocument();
    expect(screen.getByText('Substitution')).toBeInTheDocument();
  });

  it('displays learning recommendations when available', () => {
    const mockPatterns = {
      'Best Recall Time': 'Morning',
      'Optimal Session Length': '15-20 minutes',
    };

    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: mockPatterns,
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Best Recall Time')).toBeInTheDocument();
    expect(screen.getByText('Morning')).toBeInTheDocument();
  });

  it('displays personalized recommendations when available', () => {
    const mockRecommendations = [
      'Focus on improving recall speed',
      'Practice visualization techniques',
      'Try mnemonic devices for difficult items',
    ];

    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: mockRecommendations,
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Focus on improving recall speed')).toBeInTheDocument();
    expect(screen.getByText('Practice visualization techniques')).toBeInTheDocument();
  });

  it('shows loading state when data is loading', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: true,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Loading recommendations...')).toBeInTheDocument();
  });

  it('shows error state when there is an error', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: 'Failed to load analytics',
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Error: Failed to load analytics')).toBeInTheDocument();
  });

  it('calls refresh when refresh button is clicked', () => {
    const mockRefresh = vi.fn();

    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: mockRefresh,
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    const refreshButton = screen.getByText('Refresh Data');
    fireEvent.click(refreshButton);

    expect(mockRefresh).toHaveBeenCalledTimes(1);
  });

  it('displays export button', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Export Data')).toBeInTheDocument();
  });

  it('displays session history when available', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Session History')).toBeInTheDocument();
    expect(screen.getByText('2024-01-01')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('handles empty error analysis gracefully', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('No errors detected')).toBeInTheDocument();
  });

  it('handles empty recommendations gracefully', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('No specific recommendations at this time')).toBeInTheDocument();
  });

  it('displays error suggestions for common error types', () => {
    const mockErrorAnalysis = [
      {
        errorType: 'omission',
        positionExpected: 2,
        positionRecalled: undefined,
        expected: 'item3',
        recalled: undefined,
      },
    ];

    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: mockErrorAnalysis,
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    const recommendationsTab = screen.getByText('Recommendations');
    fireEvent.click(recommendationsTab);

    expect(screen.getByText('Focus on remembering all items')).toBeInTheDocument();
  });

  it('renders with disabled state', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} enabled={false} />);

    expect(screen.getByText('Memory Palace Analytics: Test Palace')).toBeInTheDocument();
  });

  it('handles null current metrics gracefully', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Average Accuracy')).toBeInTheDocument();
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('handles empty learning curve gracefully', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Learning Curve')).toBeInTheDocument();
  });

  it('handles empty patterns gracefully', () => {
    useAccuracyAnalytics.mockReturnValue({
      currentMetrics: null,
      errorAnalysis: [],
      learningCurve: [],
      patterns: {},
      recommendations: [],
      progress: {},
      isLoading: false,
      error: null,
      refresh: vi.fn(),
    });

    getPalaceStats.mockReturnValue(mockPalaceStats);

    render(<AnalyticsDashboard {...defaultProps} />);

    expect(screen.getByText('Learning Patterns')).toBeInTheDocument();
  });
});
