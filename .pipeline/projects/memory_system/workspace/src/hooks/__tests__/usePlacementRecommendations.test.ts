import { renderHook, act } from '@testing-library/react';
import { usePlacementRecommendations } from '../hooks/usePlacementRecommendations';
import { optimizePlacement, getItemPlacementSuggestions } from '../utils/placementOptimizer';

// Mock the utility functions
jest.mock('../utils/placementOptimizer', () => ({
  optimizePlacement: jest.fn(),
  getItemPlacementSuggestions: jest.fn(),
}));

describe('usePlacementRecommendations', () => {
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

  const mockRecommendations = [
    {
      itemId: 'Apple',
      roomId: 'room-1',
      locationIndex: 0,
      confidence: 0.85,
      reasoning: 'High visual contrast works well',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('initializes with empty recommendations and loading state', () => {
    const { result } = renderHook(() => usePlacementRecommendations({
      items: mockItems,
      rooms: mockRooms,
    }));

    expect(result.current.recommendations).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('calls optimizePlacement when items or rooms change', () => {
    (optimizePlacement as jest.Mock).mockReturnValue(mockRecommendations);

    const { result } = renderHook(
      ({ items, rooms }) => usePlacementRecommendations({ items, rooms }),
      {
        initialProps: {
          items: mockItems,
          rooms: mockRooms,
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).toHaveBeenCalledWith(mockItems, mockRooms);
  });

  it('updates recommendations after optimization completes', () => {
    (optimizePlacement as jest.Mock).mockReturnValue(mockRecommendations);

    const { result } = renderHook(
      ({ items, rooms }) => usePlacementRecommendations({ items, rooms }),
      {
        initialProps: {
          items: mockItems,
          rooms: mockRooms,
        },
      }
    );

    expect(result.current.recommendations).toEqual([]);

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(result.current.recommendations).toEqual(mockRecommendations);
    expect(result.current.isLoading).toBe(false);
  });

  it('sets error state when optimization fails', () => {
    (optimizePlacement as jest.Mock).mockImplementation(() => {
      throw new Error('Optimization failed');
    });

    const { result } = renderHook(
      ({ items, rooms }) => usePlacementRecommendations({ items, rooms }),
      {
        initialProps: {
          items: mockItems,
          rooms: mockRooms,
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(result.current.error).toBe('Optimization failed');
    expect(result.current.isLoading).toBe(false);
  });

  it('does not optimize when enabled is false', () => {
    const { result } = renderHook(
      ({ items, rooms, enabled }) => usePlacementRecommendations({ items, rooms, enabled }),
      {
        initialProps: {
          items: mockItems,
          rooms: mockRooms,
          enabled: false,
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).not.toHaveBeenCalled();
    expect(result.current.recommendations).toEqual([]);
  });

  it('does not optimize when items array is empty', () => {
    const { result } = renderHook(
      ({ items, rooms }) => usePlacementRecommendations({ items, rooms }),
      {
        initialProps: {
          items: [],
          rooms: mockRooms,
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).not.toHaveBeenCalled();
  });

  it('does not optimize when rooms array is empty', () => {
    const { result } = renderHook(
      ({ items, rooms }) => usePlacementRecommendations({ items, rooms }),
      {
        initialProps: {
          items: mockItems,
          rooms: [],
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).not.toHaveBeenCalled();
  });

  it('allows manual refresh via refresh function', () => {
    (optimizePlacement as jest.Mock).mockReturnValue(mockRecommendations);

    const { result } = renderHook(
      ({ items, rooms }) => usePlacementRecommendations({ items, rooms }),
      {
        initialProps: {
          items: mockItems,
          rooms: mockRooms,
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(result.current.recommendations).toEqual(mockRecommendations);

    // Refresh
    act(() => {
      result.current.refresh();
    });

    expect(optimizePlacement).toHaveBeenCalledTimes(2);
  });

  it('provides getSuggestionsForItem function', () => {
    const mockSuggestions = [
      {
        itemId: 'Apple',
        roomId: 'room-1',
        locationIndex: 0,
        confidence: 0.9,
        reasoning: 'Best match',
      },
    ];

    (getItemPlacementSuggestions as jest.Mock).mockReturnValue(mockSuggestions);

    const { result } = renderHook(() => usePlacementRecommendations({
      items: mockItems,
      rooms: mockRooms,
    }));

    const suggestions = result.current.getSuggestionsForItem('Apple');

    expect(getItemPlacementSuggestions).toHaveBeenCalledWith('Apple', mockRooms, []);
    expect(suggestions).toEqual(mockSuggestions);
  });

  it('allows excluding locations when getting suggestions', () => {
    const mockSuggestions = [
      {
        itemId: 'Apple',
        roomId: 'room-2',
        locationIndex: 0,
        confidence: 0.8,
        reasoning: 'Alternative location',
      },
    ];

    (getItemPlacementSuggestions as jest.Mock).mockReturnValue(mockSuggestions);

    const { result } = renderHook(() => usePlacementRecommendations({
      items: mockItems,
      rooms: mockRooms,
    }));

    const excludedLocations = [
      { roomId: 'room-1', locationIndex: 0 },
    ];

    const suggestions = result.current.getSuggestionsForItem('Apple', excludedLocations);

    expect(getItemPlacementSuggestions).toHaveBeenCalledWith('Apple', mockRooms, excludedLocations);
    expect(suggestions).toEqual(mockSuggestions);
  });

  it('handles card items correctly', () => {
    const cardItems = [
      { id: 'card-1', value: 12, suit: 'hearts', displayText: '12 of Hearts' },
      { id: 'card-2', value: 7, suit: 'spades', displayText: '7 of Spades' },
    ];

    (optimizePlacement as jest.Mock).mockReturnValue(mockRecommendations);

    const { result } = renderHook(
      ({ items, rooms }) => usePlacementRecommendations({ items, rooms }),
      {
        initialProps: {
          items: cardItems,
          rooms: mockRooms,
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).toHaveBeenCalledWith(cardItems, mockRooms);
  });

  it('handles number items correctly', () => {
    const numberItems = [
      { id: 'num-1', value: 42, displayText: '42' },
      { id: 'num-2', value: 17, displayText: '17' },
    ];

    (optimizePlacement as jest.Mock).mockReturnValue(mockRecommendations);

    const { result } = renderHook(
      ({ items, rooms }) => usePlacementRecommendations({ items, rooms }),
      {
        initialProps: {
          items: numberItems,
          rooms: mockRooms,
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).toHaveBeenCalledWith(numberItems, mockRooms);
  });

  it('updates when items change', () => {
    (optimizePlacement as jest.Mock).mockReturnValue(mockRecommendations);

    const { result, rerender } = renderHook(
      ({ items, rooms }) => usePlacementRecommendations({ items, rooms }),
      {
        initialProps: {
          items: mockItems,
          rooms: mockRooms,
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).toHaveBeenCalledTimes(1);

    // Change items
    const newItems = ['New Item 1', 'New Item 2'];
    rerender({ items: newItems, rooms: mockRooms });

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).toHaveBeenCalledTimes(2);
  });

  it('updates when rooms change', () => {
    (optimizePlacement as jest.Mock).mockReturnValue(mockRecommendations);

    const { result, rerender } = renderHook(
      ({ items, rooms }) => usePlacementRecommendations({ items, rooms }),
      {
        initialProps: {
          items: mockItems,
          rooms: mockRooms,
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).toHaveBeenCalledTimes(1);

    // Change rooms
    const newRooms = [
      {
        id: 'room-3',
        name: 'Bedroom',
        description: 'Sleeping area',
        locations: [
          { id: 'loc-5', name: 'Bed', description: 'Bed' },
        ],
      },
    ];
    rerender({ items: mockItems, rooms: newRooms });

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).toHaveBeenCalledTimes(2);
  });

  it('can toggle enabled state', () => {
    (optimizePlacement as jest.Mock).mockReturnValue(mockRecommendations);

    const { result, rerender } = renderHook(
      ({ items, rooms, enabled }) => usePlacementRecommendations({ items, rooms, enabled }),
      {
        initialProps: {
          items: mockItems,
          rooms: mockRooms,
          enabled: true,
        },
      }
    );

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).toHaveBeenCalledTimes(1);

    // Disable
    rerender({ items: mockItems, rooms: mockRooms, enabled: false });

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).toHaveBeenCalledTimes(1);

    // Re-enable
    rerender({ items: mockItems, rooms: mockRooms, enabled: true });

    act(() => {
      jest.advanceTimersByTime(100);
    });

    expect(optimizePlacement).toHaveBeenCalledTimes(2);
  });

  it('handles error from getItemPlacementSuggestions', () => {
    (getItemPlacementSuggestions as jest.Mock).mockImplementation(() => {
      throw new Error('Suggestions failed');
    });

    const { result } = renderHook(() => usePlacementRecommendations({
      items: mockItems,
      rooms: mockRooms,
    }));

    expect(() => {
      result.current.getSuggestionsForItem('Apple');
    }).toThrow('Suggestions failed');
  });

  it('returns empty array from getSuggestionsForItem when no rooms', () => {
    (getItemPlacementSuggestions as jest.Mock).mockReturnValue([]);

    const { result } = renderHook(() => usePlacementRecommendations({
      items: mockItems,
      rooms: [],
    }));

    const suggestions = result.current.getSuggestionsForItem('Apple');

    expect(suggestions).toEqual([]);
  });
});
