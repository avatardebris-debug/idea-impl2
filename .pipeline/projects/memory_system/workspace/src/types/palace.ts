import { PalaceExerciseSession } from './memoryPalace';

/**
 * Item in a memory palace room
 */
export interface Item {
  id: string;
  text: string;
  createdAt: string;
}

/**
 * Room for memory palace exercises
 */
export interface Room {
  id: string;
  name: string;
  description: string;
  items: Item[];
}

/**
 * Memory palace for storing memory items
 */
export interface Palace {
  id: string;
  name: string;
  description: string;
  rooms: Room[];
  relationships: string[]; // IDs of relationships
  createdAt: string;
}

/**
 * Memory palace statistics
 */
export interface PalaceStats {
  palaceId: string;
  palaceName: string;
  totalSessions: number;
  totalAttempts: number;
  correctRecalls: number;
  totalRooms: number;
  lastSessionTimestamp: string | null;
  firstSessionTimestamp: string | null;
  sessionHistory: PalaceExerciseSession[];
}

/**
 * Memory palace exercise statistics
 */
export interface PalaceExerciseStats {
  palaceId: string;
  palaceName: string;
  roomsVisited: number;
  timeElapsed: number;
  itemsPlaced: number;
}
