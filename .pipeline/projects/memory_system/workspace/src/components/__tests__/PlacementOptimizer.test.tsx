import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { PlacementOptimizer } from './PlacementOptimizer';
import { usePlacementRecommendations } from '../hooks/usePlacementRecommendations';

// Mock the hook
jest.mock('../hooks/usePlacementRecommendations', () => ({
  usePlacementRecommendations: jest.fn(),
}));

describe('PlacementOptimizer', () => {
  const mockRooms = [
    {
      id: 'room-1',
      name: 'Living Room',
      description: 'Main living area',
      locations: [
        { id: 'loc-1', name: 'Sofa', description: 'Comfortable sofa' },
        { id: 'loc-2', name: 'Coffee Table', description: 'Center table' },
      ],
    },
    {
      id: 'room-2',
      name: 'Kitchen',
      description: 'Cooking area',
      locations: [
        { id: 'loc-3', name: 'Counter', description: 'Kitchen counter' },
        { id: 'loc-4', name: 'Fridge', description: 'Refrigerator' },
      ],
    },
  ];

  const mockItems = ['Apple', 'Banana', 'Orange'];

  const defaultProps = {
    items: mockItems,
    rooms: mockRooms,
    onPlacementComplete: jest.fn(),
    enabled: true,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the component header', () => {
    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    expect(screen.getByText(/Smart Placement Optimizer/i)).toBeInTheDocument();
  });

  it('displays items to place', () => {
    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    mockItems.forEach(item => {
      expect(screen.getByText(item)).toBeInTheDocument();
    });
  });

  it('shows loading state during optimization', () => {
    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: true,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    expect(screen.getByText(/Analyzing items and rooms/i)).toBeInTheDocument();
  });

  it('displays error message when there is an error', () => {
    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: false,
      error: 'Test error message',
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    expect(screen.getByText(/Test error message/i)).toBeInTheDocument();
  });

  it('renders recommendations when available', () => {
    const mockRecommendations = [
      {
        itemId: 'Apple',
        roomId: 'room-1',
        locationIndex: 0,
        confidence: 0.85,
        reasoning: 'High visual contrast works well',
        roomName: 'Living Room',
        locationName: 'Sofa',
      },
    ];

    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: mockRecommendations,
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    expect(screen.getByText(/Living Room/i)).toBeInTheDocument();
    expect(screen.getByText(/Sofa/i)).toBeInTheDocument();
    expect(screen.getByText(/High visual contrast/i)).toBeInTheDocument();
  });

  it('allows selecting an item', () => {
    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    const firstItem = screen.getAllByRole('button')[0];
    fireEvent.click(firstItem);

    expect(screen.getByText(/Selected Item Details/i)).toBeInTheDocument();
  });

  it('allows refreshing recommendations', () => {
    const mockRefresh = jest.fn();
    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: false,
      error: null,
      refresh: mockRefresh,
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    const refreshButton = screen.getByText(/Refresh/i);
    fireEvent.click(refreshButton);

    expect(mockRefresh).toHaveBeenCalled();
  });

  it('disables refresh button when loading', () => {
    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: true,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    const refreshButton = screen.getByText(/Optimizing.../i);
    expect(refreshButton).toBeDisabled();
  });

  it('shows confidence level with color coding', () => {
    const mockRecommendations = [
      {
        itemId: 'Apple',
        roomId: 'room-1',
        locationIndex: 0,
        confidence: 0.9,
        reasoning: 'High confidence placement',
        roomName: 'Living Room',
        locationName: 'Sofa',
      },
    ];

    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: mockRecommendations,
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    expect(screen.getByText(/High/i)).toBeInTheDocument();
    expect(screen.getByText(/90%/i)).toBeInTheDocument();
  });

  it('handles card items correctly', () => {
    const cardItems = [
      { id: 'card-1', value: 12, suit: 'hearts', displayText: '12 of Hearts' },
      { id: 'card-2', value: 7, suit: 'spades', displayText: '7 of Spades' },
    ];

    const cardProps = {
      ...defaultProps,
      items: cardItems,
    };

    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...cardProps} />);

    expect(screen.getByText('12 of Hearts')).toBeInTheDocument();
    expect(screen.getByText('7 of Spades')).toBeInTheDocument();
  });

  it('handles number items correctly', () => {
    const numberItems = [
      { id: 'num-1', value: 42, displayText: '42' },
      { id: 'num-2', value: 17, displayText: '17' },
    ];

    const numberProps = {
      ...defaultProps,
      items: numberItems,
    };

    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...numberProps} />);

    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('17')).toBeInTheDocument();
  });

  it('calls onPlacementComplete when placement is made', () => {
    const mockOnPlacementComplete = jest.fn();
    const propsWithCallback = {
      ...defaultProps,
      onPlacementComplete: mockOnPlacementComplete,
    };

    const mockRecommendations = [
      {
        itemId: 'Apple',
        roomId: 'room-1',
        locationIndex: 0,
        confidence: 0.85,
        reasoning: 'Good placement',
        roomName: 'Living Room',
        locationName: 'Sofa',
      },
    ];

    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: mockRecommendations,
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...propsWithCallback} />);

    // Select item
    const firstItem = screen.getAllByRole('button')[0];
    fireEvent.click(firstItem);

    // Click place button
    const placeButton = screen.getByText(/Place Here/i);
    fireEvent.click(placeButton);

    expect(mockOnPlacementComplete).toHaveBeenCalled();
  });

  it('excludes locations after placement', () => {
    const mockRecommendations = [
      {
        itemId: 'Apple',
        roomId: 'room-1',
        locationIndex: 0,
        confidence: 0.85,
        reasoning: 'Good placement',
        roomName: 'Living Room',
        locationName: 'Sofa',
      },
    ];

    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: mockRecommendations,
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    // Select item
    const firstItem = screen.getAllByRole('button')[0];
    fireEvent.click(firstItem);

    // Click place button
    const placeButton = screen.getByText(/Place Here/i);
    fireEvent.click(placeButton);

    // Check exclusion list appears
    expect(screen.getByText(/Excluded Locations/i)).toBeInTheDocument();
  });

  it('handles empty items list', () => {
    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer items={[]} rooms={mockRooms} />);

    expect(screen.getByText(/Items to Place \(0\)/i)).toBeInTheDocument();
  });

  it('handles empty rooms list', () => {
    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer items={mockItems} rooms={[]} />);

    expect(screen.getByText(/Items to Place/i)).toBeInTheDocument();
  });

  it('displays disabled state when enabled=false', () => {
    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: [],
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} enabled={false} />);

    // Component should still render but not perform optimization
    expect(screen.getByText(/Smart Placement Optimizer/i)).toBeInTheDocument();
  });

  it('shows different confidence levels with appropriate colors', () => {
    const mockRecommendations = [
      {
        itemId: 'Apple',
        roomId: 'room-1',
        locationIndex: 0,
        confidence: 0.95,
        reasoning: 'Very high confidence',
        roomName: 'Living Room',
        locationName: 'Sofa',
      },
      {
        itemId: 'Banana',
        roomId: 'room-2',
        locationIndex: 1,
        confidence: 0.75,
        reasoning: 'Medium confidence',
        roomName: 'Kitchen',
        locationName: 'Counter',
      },
      {
        itemId: 'Orange',
        roomId: 'room-1',
        locationIndex: 1,
        confidence: 0.5,
        reasoning: 'Low confidence',
        roomName: 'Living Room',
        locationName: 'Coffee Table',
      },
    ];

    (usePlacementRecommendations as jest.Mock).mockReturnValue({
      recommendations: mockRecommendations,
      isLoading: false,
      error: null,
      refresh: jest.fn(),
      getSuggestionsForItem: jest.fn(),
    });

    render(<PlacementOptimizer {...defaultProps} />);

    expect(screen.getByText(/High/i)).toBeInTheDocument();
    expect(screen.getByText(/Medium/i)).toBeInTheDocument();
    expect(screen.getByText(/Low/i)).toBeInTheDocument();
  });
});
