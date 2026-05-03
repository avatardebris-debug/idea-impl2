import { describe, it, expect } from 'vitest';
import {
  calculateItemCharacteristics,
  calculateRoomCharacteristics,
  calculateCompatibilityScore,
  optimizePlacement,
  groupItemsByCategory,
  getItemPlacementSuggestions,
  ItemCharacteristics,
  RoomCharacteristics,
  PlacementRecommendation,
} from '../src/utils/placementOptimizer';
import { PalaceRoom } from '../src/types/palace';

describe('PlacementOptimizer', () => {
  describe('calculateItemCharacteristics', () => {
    it('should calculate characteristics for string items', () => {
      const characteristics = calculateItemCharacteristics('apple');

      expect(characteristics.id).toBe('apple');
      expect(characteristics.type).toBe('text');
      expect(characteristics.complexity).toBe('simple');
      expect(characteristics.visualStrength).toBe(0.5);
      expect(characteristics.emotionalContent).toBe(0.3);
      expect(characteristics.size).toBe('medium');
    });

    it('should calculate characteristics for love-related items', () => {
      const characteristics = calculateItemCharacteristics('love');

      expect(characteristics.emotionalContent).toBe(0.9);
      expect(characteristics.complexity).toBe('medium');
    });

    it('should calculate characteristics for fear-related items', () => {
      const characteristics = calculateItemCharacteristics('scary');

      expect(characteristics.emotionalContent).toBe(0.8);
      expect(characteristics.complexity).toBe('medium');
    });

    it('should calculate characteristics for large items', () => {
      const characteristics = calculateItemCharacteristics('big');

      expect(characteristics.size).toBe('large');
      expect(characteristics.complexity).toBe('medium');
    });

    it('should calculate characteristics for small items', () => {
      const characteristics = calculateItemCharacteristics('tiny');

      expect(characteristics.size).toBe('small');
      expect(characteristics.complexity).toBe('simple');
    });

    it('should calculate characteristics for cards', () => {
      const card = {
        id: 'card-1',
        type: 'card',
        name: 'Ace of Hearts',
        value: 1,
        suit: 'hearts',
        displayText: 'A♥',
        isFlipped: false,
        isMatched: false,
      };

      const characteristics = calculateItemCharacteristics(card);

      expect(characteristics.id).toBe('card-1');
      expect(characteristics.type).toBe('card');
      expect(characteristics.category).toBe('hearts');
      expect(characteristics.visualStrength).toBe(0.8);
      expect(characteristics.complexity).toBe('medium');
    });

    it('should calculate characteristics for number cards', () => {
      const numberCard = {
        id: '1',
        type: 'number',
        value: 1,
      };

      const characteristics = calculateItemCharacteristics(numberCard);

      expect(characteristics.id).toBe('1');
      expect(characteristics.type).toBe('card');
      expect(characteristics.category).toBe('number');
      expect(characteristics.visualStrength).toBe(0.7);
      expect(characteristics.complexity).toBe('simple');
    });

    it('should calculate characteristics for numbers 1-10', () => {
      const characteristics = calculateItemCharacteristics('5');

      expect(characteristics.category).toBe('number');
      expect(characteristics.visualStrength).toBe(0.7);
      expect(characteristics.complexity).toBe('simple');
    });

    it('should calculate characteristics for numbers 11-100', () => {
      const characteristics = calculateItemCharacteristics('50');

      expect(characteristics.category).toBe('number');
      expect(characteristics.visualStrength).toBe(0.6);
      expect(characteristics.complexity).toBe('medium');
    });

    it('should calculate characteristics for numbers > 100', () => {
      const characteristics = calculateItemCharacteristics('150');

      expect(characteristics.category).toBe('number');
      expect(characteristics.visualStrength).toBe(0.5);
      expect(characteristics.complexity).toBe('complex');
    });
  });

  describe('calculateRoomCharacteristics', () => {
    it('should calculate characteristics for simple room', () => {
      const room: PalaceRoom = {
        id: 'room-1',
        name: 'Kitchen',
        description: 'A kitchen',
        locations: [
          { id: 'loc-1', name: 'Table', description: 'A table' },
        ],
      };

      const characteristics = calculateRoomCharacteristics(room);

      expect(characteristics.id).toBe('room-1');
      expect(characteristics.name).toBe('Kitchen');
      expect(characteristics.capacity).toBe(1);
      expect(characteristics.complexity).toBe('simple');
      expect(characteristics.visualDensity).toBe(0.067);
    });

    it('should calculate characteristics for medium room', () => {
      const room: PalaceRoom = {
        id: 'room-2',
        name: 'Living Room',
        description: 'A living room',
        locations: Array.from({ length: 7 }, (_, i) => ({
          id: `loc-${i}`,
          name: `Location ${i}`,
          description: `Description ${i}`,
        })),
      };

      const characteristics = calculateRoomCharacteristics(room);

      expect(characteristics.capacity).toBe(7);
      expect(characteristics.complexity).toBe('medium');
    });

    it('should calculate characteristics for complex room', () => {
      const room: PalaceRoom = {
        id: 'room-3',
        name: 'Mansion',
        description: 'A mansion',
        locations: Array.from({ length: 15 }, (_, i) => ({
          id: `loc-${i}`,
          name: `Location ${i}`,
          description: `Description ${i}`,
        })),
      };

      const characteristics = calculateRoomCharacteristics(room);

      expect(characteristics.capacity).toBe(15);
      expect(characteristics.complexity).toBe('complex');
    });
  });

  describe('calculateCompatibilityScore', () => {
    it('should calculate score for matching complexity', () => {
      const item: ItemCharacteristics = {
        id: 'item-1',
        type: 'text',
        complexity: 'simple',
        visualStrength: 0.5,
        emotionalContent: 0.3,
        size: 'medium',
      };

      const room: RoomCharacteristics = {
        id: 'room-1',
        name: 'Kitchen',
        capacity: 1,
        complexity: 'simple',
        visualDensity: 0.1,
        emotionalTone: 'neutral',
      };

      const score = calculateCompatibilityScore(item, room);

      expect(score).toBe(0.7);
    });

    it('should calculate score with visual strength bonus', () => {
      const item: ItemCharacteristics = {
        id: 'item-1',
        type: 'text',
        complexity: 'simple',
        visualStrength: 0.8,
        emotionalContent: 0.3,
        size: 'medium',
      };

      const room: RoomCharacteristics = {
        id: 'room-1',
        name: 'Kitchen',
        capacity: 1,
        complexity: 'simple',
        visualDensity: 0.1,
        emotionalTone: 'neutral',
      };

      const score = calculateCompatibilityScore(item, room);

      expect(score).toBe(0.8);
    });

    it('should calculate score with emotional content bonus', () => {
      const item: ItemCharacteristics = {
        id: 'item-1',
        type: 'text',
        complexity: 'simple',
        visualStrength: 0.5,
        emotionalContent: 0.8,
        size: 'medium',
      };

      const room: RoomCharacteristics = {
        id: 'room-1',
        name: 'Kitchen',
        capacity: 1,
        complexity: 'simple',
        visualDensity: 0.1,
        emotionalTone: 'neutral',
      };

      const score = calculateCompatibilityScore(item, room);

      expect(score).toBe(0.8);
    });

    it('should calculate score for large item in complex room', () => {
      const item: ItemCharacteristics = {
        id: 'item-1',
        type: 'text',
        complexity: 'simple',
        visualStrength: 0.5,
        emotionalContent: 0.3,
        size: 'large',
      };

      const room: RoomCharacteristics = {
        id: 'room-1',
        name: 'Mansion',
        capacity: 15,
        complexity: 'complex',
        visualDensity: 0.5,
        emotionalTone: 'neutral',
      };

      const score = calculateCompatibilityScore(item, room);

      expect(score).toBe(0.7);
    });

    it('should return score between 0 and 1', () => {
      const item: ItemCharacteristics = {
        id: 'item-1',
        type: 'text',
        complexity: 'simple',
        visualStrength: 0.5,
        emotionalContent: 0.3,
        size: 'medium',
      };

      const room: RoomCharacteristics = {
        id: 'room-1',
        name: 'Kitchen',
        capacity: 1,
        complexity: 'simple',
        visualDensity: 0.1,
        emotionalTone: 'neutral',
      };

      const score = calculateCompatibilityScore(item, room);

      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(1);
    });
  });

  describe('optimizePlacement', () => {
    it('should optimize placement for items', () => {
      const items = ['apple', 'banana', 'orange'];
      const rooms: PalaceRoom[] = [
        {
          id: 'room-1',
          name: 'Kitchen',
          description: 'A kitchen',
          locations: [
            { id: 'loc-1', name: 'Table', description: 'A table' },
            { id: 'loc-2', name: 'Fridge', description: 'A fridge' },
          ],
        },
      ];

      const recommendations = optimizePlacement(items, rooms);

      expect(recommendations.length).toBe(3);
      expect(recommendations[0].itemId).toBe('apple');
      expect(recommendations[0].roomId).toBe('room-1');
      expect(recommendations[0].confidence).toBeGreaterThan(0);
    });

    it('should place items in different locations', () => {
      const items = ['apple', 'banana'];
      const rooms: PalaceRoom[] = [
        {
          id: 'room-1',
          name: 'Kitchen',
          description: 'A kitchen',
          locations: [
            { id: 'loc-1', name: 'Table', description: 'A table' },
            { id: 'loc-2', name: 'Fridge', description: 'A fridge' },
          ],
        },
      ];

      const recommendations = optimizePlacement(items, rooms);

      const locations = recommendations.map(r => r.locationIndex);
      expect(locations).not.toEqual([...new Set(locations)]); // Should have different locations
    });

    it('should handle empty items array', () => {
      const items: string[] = [];
      const rooms: PalaceRoom[] = [
        {
          id: 'room-1',
          name: 'Kitchen',
          description: 'A kitchen',
          locations: [
            { id: 'loc-1', name: 'Table', description: 'A table' },
          ],
        },
      ];

      const recommendations = optimizePlacement(items, rooms);

      expect(recommendations.length).toBe(0);
    });

    it('should handle items with different complexities', () => {
      const items = ['big', 'tiny', 'scary'];
      const rooms: PalaceRoom[] = [
        {
          id: 'room-1',
          name: 'Mansion',
          description: 'A mansion',
          locations: Array.from({ length: 5 }, (_, i) => ({
            id: `loc-${i}`,
            name: `Location ${i}`,
            description: `Description ${i}`,
          })),
        },
      ];

      const recommendations = optimizePlacement(items, rooms);

      expect(recommendations.length).toBe(3);
      recommendations.forEach(rec => {
        expect(rec.confidence).toBeGreaterThan(0);
        expect(rec.reasoning).toBeDefined();
      });
    });
  });

  describe('groupItemsByCategory', () => {
    it('should group items by category', () => {
      const items = ['apple', 'love', 'big', '100'];
      const groups = groupItemsByCategory(items);

      expect(Object.keys(groups).length).toBeGreaterThan(0);
      expect(groups.other).toBeDefined();
      expect(groups.number).toBeDefined();
    });

    it('should group cards by suit', () => {
      const items = [
        {
          id: 'card-1',
          type: 'card',
          name: 'Ace of Hearts',
          value: 1,
          suit: 'hearts',
          displayText: 'A♥',
          isFlipped: false,
          isMatched: false,
        },
        {
          id: 'card-2',
          type: 'card',
          name: 'King of Spades',
          value: 13,
          suit: 'spades',
          displayText: 'K♠',
          isFlipped: false,
          isMatched: false,
        },
      ];

      const groups = groupItemsByCategory(items);

      expect(groups.hearts).toBeDefined();
      expect(groups.spades).toBeDefined();
      expect(groups.hearts.length).toBe(1);
      expect(groups.spades.length).toBe(1);
    });

    it('should handle empty items array', () => {
      const groups = groupItemsByCategory([]);

      expect(Object.keys(groups).length).toBe(0);
    });
  });

  describe('getItemPlacementSuggestions', () => {
    it('should get placement suggestions for an item', () => {
      const item = 'apple';
      const rooms: PalaceRoom[] = [
        {
          id: 'room-1',
          name: 'Kitchen',
          description: 'A kitchen',
          locations: [
            { id: 'loc-1', name: 'Table', description: 'A table' },
            { id: 'loc-2', name: 'Fridge', description: 'A fridge' },
          ],
        },
      ];

      const suggestions = getItemPlacementSuggestions(item, rooms);

      expect(suggestions.length).toBeLessThanOrEqual(3);
      expect(suggestions[0].itemId).toBe('apple');
      expect(suggestions[0].confidence).toBeGreaterThan(0);
    });

    it('should exclude specified locations', () => {
      const item = 'apple';
      const rooms: PalaceRoom[] = [
        {
          id: 'room-1',
          name: 'Kitchen',
          description: 'A kitchen',
          locations: [
            { id: 'loc-1', name: 'Table', description: 'A table' },
            { id: 'loc-2', name: 'Fridge', description: 'A fridge' },
          ],
        },
      ];

      const suggestions = getItemPlacementSuggestions(item, rooms, [
        { roomId: 'room-1', locationIndex: 0 },
      ]);

      expect(suggestions[0].locationIndex).not.toBe(0);
    });

    it('should return suggestions sorted by confidence', () => {
      const item = 'apple';
      const rooms: PalaceRoom[] = [
        {
          id: 'room-1',
          name: 'Kitchen',
          description: 'A kitchen',
          locations: [
            { id: 'loc-1', name: 'Table', description: 'A table' },
            { id: 'loc-2', name: 'Fridge', description: 'A fridge' },
          ],
        },
      ];

      const suggestions = getItemPlacementSuggestions(item, rooms);

      for (let i = 1; i < suggestions.length; i++) {
        expect(suggestions[i - 1].confidence).toBeGreaterThanOrEqual(suggestions[i].confidence);
      }
    });
  });
});
