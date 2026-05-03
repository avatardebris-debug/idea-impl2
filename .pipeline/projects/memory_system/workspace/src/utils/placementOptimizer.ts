import { Card, NumberCard, PalaceLocation, PalaceRoom } from '../types/memoryPalace';

/**
 * Item characteristics for smart placement
 */
export interface ItemCharacteristics {
  id: string;
  type: 'card' | 'number' | 'text';
  category?: string;
  complexity: 'simple' | 'medium' | 'complex';
  visualStrength: number; // 0-1, higher = more visualizable
  emotionalContent: number; // 0-1, higher = more emotional
  size: 'small' | 'medium' | 'large';
}

/**
 * Placement recommendation
 */
export interface PlacementRecommendation {
  itemId: string;
  roomId: string;
  locationIndex: number;
  confidence: number;
  reasoning: string;
}

/**
 * Room characteristics
 */
export interface RoomCharacteristics {
  id: string;
  name: string;
  capacity: number;
  complexity: 'simple' | 'medium' | 'complex';
  visualDensity: number; // 0-1, higher = more visual elements
  emotionalTone: 'neutral' | 'positive' | 'negative' | 'mixed';
}

/**
 * Calculate item characteristics from item data
 */
export const calculateItemCharacteristics = (item: string | Card | NumberCard): ItemCharacteristics => {
  let category: string | undefined;
  let complexity: ItemCharacteristics['complexity'] = 'simple';
  let visualStrength = 0.5;
  let emotionalContent = 0.3;
  let size: ItemCharacteristics['size'] = 'medium';

  const itemStr = typeof item === 'string' ? item.toLowerCase() : '';

  // Card-specific analysis
  if (typeof item !== 'string' && 'suit' in item) {
    const card = item as Card;
    category = card.suit;
    visualStrength = 0.8;
    complexity = 'medium';
  }

  // Number analysis
  if (!category && typeof item === 'string' && !isNaN(Number(item))) {
    const num = parseInt(item);
    if (num >= 1 && num <= 10) {
      category = 'number';
      visualStrength = 0.7;
      complexity = 'simple';
    } else if (num >= 11 && num <= 100) {
      category = 'number';
      visualStrength = 0.6;
      complexity = 'medium';
    } else {
      category = 'number';
      visualStrength = 0.5;
      complexity = 'complex';
    }
  }

  // Text-based analysis
  if (!category) {
    if (itemStr.includes('love') || itemStr.includes('heart') || itemStr.includes('happy')) {
      emotionalContent = 0.9;
      complexity = 'medium';
    } else if (itemStr.includes('fear') || itemStr.includes('scary') || itemStr.includes('danger')) {
      emotionalContent = 0.8;
      complexity = 'medium';
    } else if (itemStr.includes('big') || itemStr.includes('large') || itemStr.includes('huge')) {
      size = 'large';
      complexity = 'medium';
    } else if (itemStr.includes('small') || itemStr.includes('tiny') || itemStr.includes('mini')) {
      size = 'small';
      complexity = 'simple';
    } else {
      complexity = 'simple';
    }
  }

  return {
    id: typeof item === 'string' ? item : item.id,
    type: typeof item === 'string' ? 'text' : 'card',
    category,
    complexity,
    visualStrength,
    emotionalContent,
    size,
  };
};

/**
 * Calculate room characteristics
 */
export const calculateRoomCharacteristics = (room: PalaceRoom): RoomCharacteristics => {
  const locationCount = room.locations.length;
  const complexity = locationCount > 10 ? 'complex' : locationCount > 5 ? 'medium' : 'simple';
  const visualDensity = locationCount / 15; // Normalize to 0-1 range

  return {
    id: room.id,
    name: room.name,
    capacity: locationCount,
    complexity,
    visualDensity,
    emotionalTone: 'neutral',
  };
};

/**
 * Calculate compatibility score between item and room
 */
export const calculateCompatibilityScore = (
  item: ItemCharacteristics,
  room: RoomCharacteristics
): number => {
  let score = 0.5; // Base score

  // Complexity matching
  if (item.complexity === room.complexity) {
    score += 0.2;
  } else if (item.complexity === 'complex' && room.complexity === 'medium') {
    score += 0.1;
  } else if (item.complexity === 'simple' && room.complexity === 'medium') {
    score += 0.1;
  }

  // Visual strength bonus
  if (item.visualStrength > 0.7) {
    score += 0.1;
  }

  // Emotional content bonus
  if (item.emotionalContent > 0.7) {
    score += 0.1;
  }

  // Size matching (large items in large rooms)
  if (item.size === 'large' && room.complexity === 'complex') {
    score += 0.1;
  }

  return Math.max(0, Math.min(1, score));
};

/**
 * Smart placement optimizer
 */
export const optimizePlacement = (
  items: (string | Card | NumberCard)[],
  rooms: PalaceRoom[],
  maxItemsPerLocation: number = 1
): PlacementRecommendation[] => {
  const itemCharacteristics = items.map(item => calculateItemCharacteristics(item));
  const roomCharacteristics = rooms.map(room => calculateRoomCharacteristics(room));

  const recommendations: PlacementRecommendation[] = [];

  // Sort items by complexity (place complex items first)
  const sortedItems = itemCharacteristics.sort((a, b) =>
    b.complexity.localeCompare(a.complexity)
  );

  // Track available locations
  const availableLocations: { roomId: string; locationIndex: number }[] = [];
  roomCharacteristics.forEach(room => {
    for (let i = 0; i < room.locations.length; i++) {
      availableLocations.push({
        roomId: room.id,
        locationIndex: i,
      });
    }
  });

  // Place each item
  for (const item of sortedItems) {
    // Calculate compatibility scores for all available locations
    const locationScores = availableLocations.map(loc => {
      const room = roomCharacteristics.find(r => r.id === loc.roomId);
      if (!room) return null;

      const score = calculateCompatibilityScore(item, room);
      return {
        ...loc,
        score,
        room,
      };
    }).filter((loc): loc is { roomId: string; locationIndex: number; score: number; room: RoomCharacteristics } => loc !== null);

    // Sort by score and pick the best
    locationScores.sort((a, b) => b.score - a.score);

    if (locationScores.length > 0) {
      const bestLocation = locationScores[0];
      recommendations.push({
        itemId: item.id,
        roomId: bestLocation.roomId,
        locationIndex: bestLocation.locationIndex,
        confidence: bestLocation.score,
        reasoning: `Matched ${item.complexity} item to ${bestLocation.room.complexity} room with ${bestLocation.score.toFixed(2)} compatibility`,
      });

      // Remove used location
      availableLocations.splice(
        availableLocations.findIndex(loc =>
          loc.roomId === bestLocation.roomId && loc.locationIndex === bestLocation.locationIndex
        ),
        1
      );
    }
  }

  return recommendations;
};

/**
 * Group items by category for better organization
 */
export const groupItemsByCategory = (items: (string | Card | NumberCard)[]): Record<string, (string | Card | NumberCard)[]> => {
  const groups: Record<string, (string | Card | NumberCard)[]> = {};

  items.forEach(item => {
    const characteristics = calculateItemCharacteristics(item);
    const category = characteristics.category || 'other';

    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(item);
  });

  return groups;
};

/**
 * Get placement suggestions for a specific item
 */
export const getItemPlacementSuggestions = (
  item: string | Card | NumberCard,
  rooms: PalaceRoom[],
  excludeLocations: { roomId: string; locationIndex: number }[] = []
): PlacementRecommendation[] => {
  const itemCharacteristics = calculateItemCharacteristics(item);
  const roomCharacteristics = rooms.map(room => calculateRoomCharacteristics(room));

  const suggestions: PlacementRecommendation[] = [];

  for (const room of roomCharacteristics) {
    for (let i = 0; i < room.locations.length; i++) {
      const isExcluded = excludeLocations.some(
        loc => loc.roomId === room.id && loc.locationIndex === i
      );

      if (isExcluded) continue;

      const score = calculateCompatibilityScore(itemCharacteristics, room);
      suggestions.push({
        itemId: itemCharacteristics.id,
        roomId: room.id,
        locationIndex: i,
        confidence: score,
        reasoning: `Compatibility score: ${score.toFixed(2)}`,
      });
    }
  }

  // Sort by confidence and return top 3
  return suggestions
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 3);
};
