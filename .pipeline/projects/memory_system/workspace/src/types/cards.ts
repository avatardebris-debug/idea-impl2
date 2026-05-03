import { Suit } from './memoryPalace';

/**
 * Card game statistics
 */
export interface CardGameStats {
  moves: number;
  timeElapsed: number;
  pairsFound: number;
  totalPairs: number;
}

/**
 * Card exercise props for memory games
 */
export interface CardExerciseProps {
  cardCount?: number;
  onExerciseComplete?: (stats: CardGameStats) => void;
}

/**
 * Card matching game props
 */
export interface CardMatchingGameProps {
  cardCount?: number;
  onGameComplete?: (stats: CardGameStats) => void;
}

/**
 * Card flip animation state
 */
export interface CardFlipState {
  isFlipped: boolean;
  isMatched: boolean;
  flipAnimation: boolean;
}

/**
 * Card selection state for matching games
 */
export interface CardSelectionState {
  firstCard: CardWithSuit | null;
  secondCard: CardWithSuit | null;
  isLocked: boolean;
}
