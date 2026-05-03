import { Card, Suit, NumberCard } from '../types/memoryPalace';

/**
 * Association suggestion types
 */
export interface AssociationSuggestion {
  id: string;
  type: 'visual' | 'semantic' | 'numeric' | 'suit-based';
  text: string;
  description: string;
  confidence: number;
}

export interface AssociationContext {
  item: string;
  itemType: 'card' | 'number' | 'text';
  previousItem?: string;
  location?: string;
}

/**
 * Suit-based association mappings
 */
const SUIT_ASSOCIATIONS: Record<Suit, {
  imagery: string;
  keywords: string[];
  mnemonic: string;
}> = {
  hearts: {
    imagery: 'heart',
    keywords: ['love', 'compassion', 'emotion', 'warmth', 'passion'],
    mnemonic: 'H for Heart - imagine a beating heart',
  },
  diamonds: {
    imagery: 'diamond',
    keywords: ['wealth', 'value', 'sparkle', 'precious', 'clarity'],
    mnemonic: 'D for Diamond - imagine a sparkling diamond',
  },
  clubs: {
    imagery: 'club',
    keywords: ['nature', 'growth', 'luck', 'four-leaf', 'forest'],
    mnemonic: 'C for Club - imagine a four-leaf clover',
  },
  spades: {
    imagery: 'spade',
    keywords: ['tool', 'digging', 'black', 'sword', 'protection'],
    mnemonic: 'S for Spade - imagine a gardener\'s spade',
  },
};

/**
 * Number-based mnemonic associations (Major System inspired)
 */
const NUMBER_ASSOCIATIONS: Record<number, {
  imagery: string;
  keywords: string[];
  mnemonic: string;
}> = {
  1: { imagery: 'candle', keywords: ['one', 'single', 'pillar', 'light'], mnemonic: '1 looks like a candle' },
  2: { imagery: 'swan', keywords: ['two', 'pair', 'curve', 'grace'], mnemonic: '2 looks like a swan' },
  3: { imagery: 'heart', keywords: ['three', 'half', 'curve', 'love'], mnemonic: '3 looks like a heart' },
  4: { imagery: 'boat', keywords: ['four', 'square', 'stable', 'end'], mnemonic: '4 looks like a boat' },
  5: { imagery: 'hook', keywords: ['five', 'grab', 'catch', 'bend'], mnemonic: '5 looks like a hook' },
  6: { imagery: 'elephant', keywords: ['six', 'trunk', 'large', 'memory'], mnemonic: '6 looks like an elephant trunk' },
  7: { imagery: 'mountain', keywords: ['seven', 'peak', 'high', 'climb'], mnemonic: '7 looks like a mountain' },
  8: { imagery: 'snowman', keywords: ['eight', 'two', 'stack', 'cold'], mnemonic: '8 looks like a snowman' },
  9: { imagery: 'balloon', keywords: ['nine', 'float', 'round', 'up'], mnemonic: '9 looks like a balloon' },
  10: { imagery: 'bat', keywords: ['ten', 'baseball', 'hit', 'sport'], mnemonic: '10 looks like a baseball bat' },
};

/**
 * Generate suit-based association
 */
export const generateSuitAssociation = (suit: Suit): AssociationSuggestion => {
  const association = SUIT_ASSOCIATIONS[suit];
  return {
    id: `suit-${suit}`,
    type: 'suit-based',
    text: association.mnemonic,
    description: association.imagery,
    confidence: 0.9,
  };
};

/**
 * Generate numeric association
 */
export const generateNumericAssociation = (card: NumberCard): AssociationSuggestion => {
  const value = typeof card.value === 'number' ? card.value : parseInt(card.value as string);
  const association = NUMBER_ASSOCIATIONS[value as keyof typeof NUMBER_ASSOCIATIONS];
  
  if (association) {
    return {
      id: `number-${value}`,
      type: 'numeric',
      text: association.mnemonic,
      description: association.imagery,
      confidence: 0.85,
    };
  }

  return {
    id: `number-${value}`,
    type: 'numeric',
    text: `Visualize the number ${value} as a concrete object`,
    description: 'Use shape-based visualization',
    confidence: 0.7,
  };
};

/**
 * Generate visual association for number
 */
export const generateNumberVisual = (number: number): AssociationSuggestion => {
  const associations = [
    { num: 1, text: 'A tall candle standing alone', description: 'Visualize a single flame' },
    { num: 2, text: 'A graceful swan floating on water', description: 'See the curved neck' },
    { num: 3, text: 'A heart-shaped balloon', description: 'Feel the warmth' },
    { num: 4, text: 'A small boat on the ocean', description: 'See the sail' },
    { num: 5, text: 'A fisherman\'s hook', description: 'Imagine catching something' },
    { num: 6, text: 'An elephant with a long trunk', description: 'See the wrinkles' },
    { num: 7, text: 'A mountain peak in the clouds', description: 'Feel the height' },
    { num: 8, text: 'A snowman with two balls', description: 'See the carrot nose' },
    { num: 9, text: 'A colorful balloon floating up', description: 'Feel the string' },
    { num: 10, text: 'A baseball bat ready to swing', description: 'Hear the crack' },
  ];

  const assoc = associations.find(a => a.num === number);
  if (assoc) {
    return {
      id: `visual-${number}`,
      type: 'visual',
      text: assoc.text,
      description: assoc.description,
      confidence: 0.85,
    };
  }

  return {
    id: `visual-${number}`,
    type: 'visual',
    text: `Create a vivid image for number ${number}`,
    description: 'Use your imagination',
    confidence: 0.7,
  };
};

/**
 * Get association suggestions for a card
 */
export const getCardAssociations = (card: Card): AssociationSuggestion[] => {
  const suggestions: AssociationSuggestion[] = [];

  if ('suit' in card) {
    suggestions.push(generateSuitAssociation(card.suit));
    suggestions.push(generateNumericAssociation(card as NumberCard));
  }

  suggestions.push({
    id: 'card-general',
    type: 'visual',
    text: 'Create a vivid mental image combining the card\'s number and suit',
    description: 'The more exaggerated and unusual, the better you\'ll remember',
    confidence: 0.9,
  });

  return suggestions;
};

/**
 * Get association suggestions for a number
 */
export const getNumberAssociations = (number: number): AssociationSuggestion[] => {
  const suggestions: AssociationSuggestion[] = [];

  if (number >= 1 && number <= 10) {
    suggestions.push(generateNumberVisual(number));
  }

  suggestions.push({
    id: 'number-general',
    type: 'visual',
    text: 'Use the shape of the number to create a visual mnemonic',
    description: '1=candle, 2=swan, 3=heart, 4=boat, 5=hook, 6=elephant, 7=mountain, 8=snowman, 9=balloon, 10=bat',
    confidence: 0.85,
  });

  return suggestions;
};
