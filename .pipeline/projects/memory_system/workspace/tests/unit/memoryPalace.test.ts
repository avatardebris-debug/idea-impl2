import { describe, it, expect } from 'vitest';
import {
  Card,
  NumberCard,
  Suit,
  PalaceLocation,
  PalaceRoom,
  Palace,
  PalaceState,
  PalaceExercise,
  PalaceExerciseType,
  PalaceExerciseDifficulty,
} from '../src/types/memoryPalace';

describe('MemoryPalace Types', () => {
  describe('Card types', () => {
    it('should create a valid card', () => {
      const card: Card = {
        id: 'card-1',
        type: 'card',
        name: 'Ace of Hearts',
        value: 1,
        suit: 'hearts',
        displayText: 'A♥',
        isFlipped: false,
        isMatched: false,
      };

      expect(card.id).toBe('card-1');
      expect(card.type).toBe('card');
      expect(card.suit).toBe('hearts');
      expect(card.displayText).toBe('A♥');
      expect(card.isFlipped).toBe(false);
      expect(card.isMatched).toBe(false);
    });

    it('should create a valid number card', () => {
      const numberCard: NumberCard = {
        id: '1',
        type: 'number',
        value: 1,
      };

      expect(numberCard.id).toBe('1');
      expect(numberCard.type).toBe('number');
      expect(numberCard.value).toBe(1);
    });

    it('should handle number card with string value', () => {
      const numberCard: NumberCard = {
        id: '10',
        type: 'number',
        value: '10',
      };

      expect(numberCard.value).toBe('10');
    });

    it('should handle card without suit', () => {
      const card: Card = {
        id: 'card-2',
        type: 'card',
        name: 'Card',
        value: 5,
        isFlipped: false,
        isMatched: false,
      };

      expect(card.suit).toBeUndefined();
    });
  });

  describe('Suit types', () => {
    it('should have valid suit values', () => {
      const suits: Suit[] = ['hearts', 'diamonds', 'clubs', 'spades'];

      expect(suits).toContain('hearts');
      expect(suits).toContain('diamonds');
      expect(suits).toContain('clubs');
      expect(suits).toContain('spades');
    });

    it('should have correct emoji for suits', () => {
      const suitEmojis: Record<Suit, string> = {
        hearts: '♥',
        diamonds: '♦',
        clubs: '♣',
        spades: '♠',
      };

      expect(suitEmojis.hearts).toBe('♥');
      expect(suitEmojis.diamonds).toBe('♦');
      expect(suitEmojis.clubs).toBe('♣');
      expect(suitEmojis.spades).toBe('♠');
    });
  });

  describe('PalaceLocation types', () => {
    it('should create a valid location', () => {
      const location: PalaceLocation = {
        id: 'loc-1',
        name: 'Table',
        description: 'A table',
      };

      expect(location.id).toBe('loc-1');
      expect(location.name).toBe('Table');
      expect(location.description).toBe('A table');
    });

    it('should have required fields', () => {
      const location: PalaceLocation = {
        id: 'loc-2',
        name: 'Chair',
        description: 'A chair',
      };

      expect(location.id).toBeDefined();
      expect(location.name).toBeDefined();
      expect(location.description).toBeDefined();
    });
  });

  describe('PalaceRoom types', () => {
    it('should create a valid room', () => {
      const room: PalaceRoom = {
        id: 'room-1',
        name: 'Kitchen',
        description: 'A kitchen',
        locations: [
          { id: 'loc-1', name: 'Table', description: 'A table' },
          { id: 'loc-2', name: 'Fridge', description: 'A fridge' },
        ],
      };

      expect(room.id).toBe('room-1');
      expect(room.name).toBe('Kitchen');
      expect(room.description).toBe('A kitchen');
      expect(room.locations.length).toBe(2);
    });

    it('should handle room without locations', () => {
      const room: PalaceRoom = {
        id: 'room-2',
        name: 'Empty Room',
        description: 'An empty room',
        locations: [],
      };

      expect(room.locations).toEqual([]);
    });

    it('should have required fields', () => {
      const room: PalaceRoom = {
        id: 'room-3',
        name: 'Bedroom',
        description: 'A bedroom',
        locations: [],
      };

      expect(room.id).toBeDefined();
      expect(room.name).toBeDefined();
      expect(room.description).toBeDefined();
    });
  });

  describe('Palace types', () => {
    it('should create a valid palace', () => {
      const palace: Palace = {
        id: 'palace-1',
        name: 'Memory Palace',
        description: 'A memory palace',
        rooms: [
          {
            id: 'room-1',
            name: 'Kitchen',
            description: 'A kitchen',
            locations: [
              { id: 'loc-1', name: 'Table', description: 'A table' },
            ],
          },
        ],
        createdAt: new Date().toISOString(),
      };

      expect(palace.id).toBe('palace-1');
      expect(palace.name).toBe('Memory Palace');
      expect(palace.description).toBe('A memory palace');
      expect(palace.rooms.length).toBe(1);
      expect(palace.createdAt).toBeDefined();
    });

    it('should handle palace without rooms', () => {
      const palace: Palace = {
        id: 'palace-2',
        name: 'Empty Palace',
        description: 'An empty palace',
        rooms: [],
        createdAt: new Date().toISOString(),
      };

      expect(palace.rooms).toEqual([]);
    });

    it('should have required fields', () => {
      const palace: Palace = {
        id: 'palace-3',
        name: 'Test Palace',
        description: 'A test palace',
        rooms: [],
        createdAt: new Date().toISOString(),
      };

      expect(palace.id).toBeDefined();
      expect(palace.name).toBeDefined();
      expect(palace.description).toBeDefined();
      expect(palace.createdAt).toBeDefined();
    });
  });

  describe('PalaceState types', () => {
    it('should create a valid palace state', () => {
      const state: PalaceState = {
        currentPalaceId: 'palace-1',
        currentRoomId: 'room-1',
        currentLocationId: 'loc-1',
        cards: [
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
        ],
        history: [],
        lastModified: new Date().toISOString(),
      };

      expect(state.currentPalaceId).toBe('palace-1');
      expect(state.currentRoomId).toBe('room-1');
      expect(state.currentLocationId).toBe('loc-1');
      expect(state.cards.length).toBe(1);
      expect(state.history.length).toBe(0);
      expect(state.lastModified).toBeDefined();
    });

    it('should handle empty cards array', () => {
      const state: PalaceState = {
        currentPalaceId: 'palace-1',
        currentRoomId: 'room-1',
        currentLocationId: 'loc-1',
        cards: [],
        history: [],
        lastModified: new Date().toISOString(),
      };

      expect(state.cards).toEqual([]);
    });

    it('should handle empty history array', () => {
      const state: PalaceState = {
        currentPalaceId: 'palace-1',
        currentRoomId: 'room-1',
        currentLocationId: 'loc-1',
        cards: [],
        history: [],
        lastModified: new Date().toISOString(),
      };

      expect(state.history).toEqual([]);
    });
  });

  describe('PalaceExercise types', () => {
    it('should create a valid exercise', () => {
      const exercise: PalaceExercise = {
        id: 'exercise-1',
        type: 'recall',
        difficulty: 'easy',
        targetCards: ['card-1'],
        completed: false,
        createdAt: new Date().toISOString(),
      };

      expect(exercise.id).toBe('exercise-1');
      expect(exercise.type).toBe('recall');
      expect(exercise.difficulty).toBe('easy');
      expect(exercise.targetCards.length).toBe(1);
      expect(exercise.completed).toBe(false);
      expect(exercise.createdAt).toBeDefined();
    });

    it('should handle exercise with no target cards', () => {
      const exercise: PalaceExercise = {
        id: 'exercise-2',
        type: 'recall',
        difficulty: 'easy',
        targetCards: [],
        completed: false,
        createdAt: new Date().toISOString(),
      };

      expect(exercise.targetCards).toEqual([]);
    });

    it('should have required fields', () => {
      const exercise: PalaceExercise = {
        id: 'exercise-3',
        type: 'recall',
        difficulty: 'easy',
        targetCards: [],
        completed: false,
        createdAt: new Date().toISOString(),
      };

      expect(exercise.id).toBeDefined();
      expect(exercise.type).toBeDefined();
      expect(exercise.difficulty).toBeDefined();
      expect(exercise.completed).toBeDefined();
      expect(exercise.createdAt).toBeDefined();
    });
  });

  describe('PalaceExerciseType', () => {
    it('should have valid exercise types', () => {
      const types: PalaceExerciseType[] = ['recall', 'association', 'visualization'];

      expect(types).toContain('recall');
      expect(types).toContain('association');
      expect(types).toContain('visualization');
    });
  });

  describe('PalaceExerciseDifficulty', () => {
    it('should have valid difficulty levels', () => {
      const difficulties: PalaceExerciseDifficulty[] = ['easy', 'medium', 'hard'];

      expect(difficulties).toContain('easy');
      expect(difficulties).toContain('medium');
      expect(difficulties).toContain('hard');
    });
  });

  describe('Type validation', () => {
    it('should validate card type', () => {
      const card: Card = {
        id: 'card-1',
        type: 'card',
        name: 'Ace of Hearts',
        value: 1,
        suit: 'hearts',
        displayText: 'A♥',
        isFlipped: false,
        isMatched: false,
      };

      expect(card.type).toBe('card');
    });

    it('should validate number card type', () => {
      const numberCard: NumberCard = {
        id: '1',
        type: 'number',
        value: 1,
      };

      expect(numberCard.type).toBe('number');
    });

    it('should validate palace room type', () => {
      const room: PalaceRoom = {
        id: 'room-1',
        name: 'Kitchen',
        description: 'A kitchen',
        locations: [],
      };

      expect(room.id).toBeDefined();
      expect(room.name).toBeDefined();
      expect(room.description).toBeDefined();
    });

    it('should validate palace location type', () => {
      const location: PalaceLocation = {
        id: 'loc-1',
        name: 'Table',
        description: 'A table',
      };

      expect(location.id).toBeDefined();
      expect(location.name).toBeDefined();
      expect(location.description).toBeDefined();
    });
  });
});
