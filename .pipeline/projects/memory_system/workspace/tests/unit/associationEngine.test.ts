import { describe, it, expect } from 'vitest';
import {
  generateSuitAssociation,
  generateNumericAssociation,
  generateNumberVisual,
  getCardAssociations,
  getNumberAssociations,
  Card,
  NumberCard,
  Suit,
} from '../src/types/memoryPalace';
import {
  generateSuitAssociation as generateSuitAssoc,
  generateNumericAssociation as generateNumericAssoc,
  generateNumberVisual as generateNumVisual,
  getCardAssociations as getCardAssoc,
  getNumberAssociations as getNumAssoc,
  AssociationSuggestion,
} from '../src/utils/associationEngine';

describe('AssociationEngine', () => {
  describe('generateSuitAssociation', () => {
    it('should generate association for hearts', () => {
      const suggestion = generateSuitAssoc('hearts');
      
      expect(suggestion.type).toBe('suit-based');
      expect(suggestion.text).toContain('Heart');
      expect(suggestion.confidence).toBe(0.9);
    });

    it('should generate association for diamonds', () => {
      const suggestion = generateSuitAssoc('diamonds');
      
      expect(suggestion.type).toBe('suit-based');
      expect(suggestion.text).toContain('Diamond');
      expect(suggestion.confidence).toBe(0.9);
    });

    it('should generate association for clubs', () => {
      const suggestion = generateSuitAssoc('clubs');
      
      expect(suggestion.type).toBe('suit-based');
      expect(suggestion.text).toContain('Club');
      expect(suggestion.confidence).toBe(0.9);
    });

    it('should generate association for spades', () => {
      const suggestion = generateSuitAssoc('spades');
      
      expect(suggestion.type).toBe('suit-based');
      expect(suggestion.text).toContain('Spade');
      expect(suggestion.confidence).toBe(0.9);
    });
  });

  describe('generateNumericAssociation', () => {
    it('should generate association for number 1', () => {
      const card: NumberCard = {
        id: '1',
        type: 'number',
        value: 1,
      };
      
      const suggestion = generateNumericAssoc(card);
      
      expect(suggestion.type).toBe('numeric');
      expect(suggestion.text).toContain('1');
      expect(suggestion.confidence).toBe(0.85);
    });

    it('should generate association for number 5', () => {
      const card: NumberCard = {
        id: '5',
        type: 'number',
        value: 5,
      };
      
      const suggestion = generateNumericAssoc(card);
      
      expect(suggestion.type).toBe('numeric');
      expect(suggestion.text).toContain('5');
      expect(suggestion.confidence).toBe(0.85);
    });

    it('should handle number as string', () => {
      const card: NumberCard = {
        id: '7',
        type: 'number',
        value: '7',
      };
      
      const suggestion = generateNumericAssoc(card);
      
      expect(suggestion.type).toBe('numeric');
      expect(suggestion.text).toContain('7');
    });

    it('should handle out-of-range numbers', () => {
      const card: NumberCard = {
        id: '100',
        type: 'number',
        value: 100,
      };
      
      const suggestion = generateNumericAssoc(card);
      
      expect(suggestion.type).toBe('numeric');
      expect(suggestion.confidence).toBe(0.7);
    });
  });

  describe('generateNumberVisual', () => {
    it('should generate visual for number 1', () => {
      const suggestion = generateNumVisual(1);
      
      expect(suggestion.type).toBe('visual');
      expect(suggestion.text).toContain('candle');
      expect(suggestion.confidence).toBe(0.85);
    });

    it('should generate visual for number 2', () => {
      const suggestion = generateNumVisual(2);
      
      expect(suggestion.type).toBe('visual');
      expect(suggestion.text).toContain('swan');
      expect(suggestion.confidence).toBe(0.85);
    });

    it('should generate visual for number 10', () => {
      const suggestion = generateNumVisual(10);
      
      expect(suggestion.type).toBe('visual');
      expect(suggestion.text).toContain('bat');
      expect(suggestion.confidence).toBe(0.85);
    });

    it('should handle out-of-range numbers', () => {
      const suggestion = generateNumVisual(50);
      
      expect(suggestion.type).toBe('visual');
      expect(suggestion.confidence).toBe(0.7);
    });
  });

  describe('getCardAssociations', () => {
    it('should generate associations for a card with suit', () => {
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

      const associations = getCardAssoc(card);

      expect(associations.length).toBeGreaterThanOrEqual(2);
      expect(associations.some(a => a.type === 'suit-based')).toBe(true);
      expect(associations.some(a => a.type === 'numeric')).toBe(true);
      expect(associations.some(a => a.type === 'visual')).toBe(true);
    });

    it('should generate associations for a card without suit', () => {
      const card: Card = {
        id: 'card-2',
        type: 'card',
        name: 'Card',
        value: 5,
        isFlipped: false,
        isMatched: false,
      };

      const associations = getCardAssoc(card);

      expect(associations.length).toBeGreaterThanOrEqual(1);
      expect(associations.some(a => a.type === 'visual')).toBe(true);
    });
  });

  describe('getNumberAssociations', () => {
    it('should generate associations for number 1', () => {
      const associations = getNumAssoc(1);

      expect(associations.length).toBeGreaterThanOrEqual(1);
      expect(associations.some(a => a.type === 'visual')).toBe(true);
    });

    it('should generate associations for number 10', () => {
      const associations = getNumAssoc(10);

      expect(associations.length).toBeGreaterThanOrEqual(1);
      expect(associations.some(a => a.type === 'visual')).toBe(true);
    });

    it('should generate associations for out-of-range number', () => {
      const associations = getNumAssoc(50);

      expect(associations.length).toBeGreaterThanOrEqual(1);
      expect(associations.some(a => a.type === 'visual')).toBe(true);
    });
  });

  describe('Association confidence scores', () => {
    it('should have high confidence for suit associations', () => {
      const suits: Suit[] = ['hearts', 'diamonds', 'clubs', 'spades'];
      
      suits.forEach(suit => {
        const suggestion = generateSuitAssoc(suit);
        expect(suggestion.confidence).toBe(0.9);
      });
    });

    it('should have high confidence for numeric associations', () => {
      for (let i = 1; i <= 10; i++) {
        const card: NumberCard = {
          id: `${i}`,
          type: 'number',
          value: i,
        };
        
        const suggestion = generateNumericAssoc(card);
        expect(suggestion.confidence).toBe(0.85);
      }
    });

    it('should have high confidence for visual associations', () => {
      for (let i = 1; i <= 10; i++) {
        const suggestion = generateNumVisual(i);
        expect(suggestion.confidence).toBe(0.85);
      }
    });
  });
});
