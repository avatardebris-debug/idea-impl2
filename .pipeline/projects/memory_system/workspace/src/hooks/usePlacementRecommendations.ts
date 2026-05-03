import { useState, useCallback, useEffect } from 'react';
import { optimizePlacement, getItemPlacementSuggestions, ItemCharacteristics } from '../utils/placementOptimizer';
import { Card, NumberCard, PalaceRoom } from '../types/memoryPalace';

interface UsePlacementRecommendationsProps {
  items: (string | Card | NumberCard)[];
  rooms: PalaceRoom[];
  enabled?: boolean;
}

interface PlacementRecommendations {
  recommendations: {
    itemId: string;
    roomId: string;
    locationIndex: number;
    confidence: number;
    reasoning: string;
  }[];
  isLoading: boolean;
  error: string | null;
  itemCharacteristics: ItemCharacteristics[];
  refresh: () => void;
  getSuggestionsForItem: (item: string | Card | NumberCard, excludeLocations?: { roomId: string; locationIndex: number }[]) => {
    itemId: string;
    roomId: string;
    locationIndex: number;
    confidence: number;
    reasoning: string;
  }[];
}

export const usePlacementRecommendations = ({
  items,
  rooms,
  enabled = true,
}: UsePlacementRecommendationsProps): PlacementRecommendations => {
  const [recommendations, setRecommendations] = useState<PlacementRecommendations['recommendations']>([]);
  const [itemCharacteristics, setItemCharacteristics] = useState<ItemCharacteristics[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performOptimization = useCallback(() => {
    if (!enabled || items.length === 0 || rooms.length === 0) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Simulate async operation for better UX
      setTimeout(() => {
        const optimized = optimizePlacement(items, rooms);
        setRecommendations(optimized);
        setIsLoading(false);
      }, 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to optimize placement');
      setIsLoading(false);
    }
  }, [items, rooms, enabled]);

  useEffect(() => {
    if (enabled) {
      performOptimization();
    }
  }, [items, rooms, enabled, performOptimization]);

  const refresh = useCallback(() => {
    performOptimization();
  }, [performOptimization]);

  const getSuggestionsForItem = useCallback((
    item: string | Card | NumberCard,
    excludeLocations: { roomId: string; locationIndex: number }[] = []
  ) => {
    return getItemPlacementSuggestions(item, rooms, excludeLocations);
  }, [rooms]);

  return {
    recommendations,
    isLoading,
    error,
    itemCharacteristics,
    refresh,
    getSuggestionsForItem,
  };
};

export default usePlacementRecommendations;
