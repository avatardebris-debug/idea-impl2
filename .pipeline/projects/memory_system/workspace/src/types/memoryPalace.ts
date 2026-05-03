/**
 * Memory Palace types for recall and accuracy analytics
 */

/**
 * A card item (e.g., playing card)
 */
export interface Card {
  id: string;
  type: 'card';
  name: string;
  value: number;
}

/**
 * A number item
 */
export interface NumberCard {
  id: string;
  type: 'number';
  value: number;
}

/**
 * A recalled item with confidence score
 */
export interface RecalledItem {
  item: string | Card | NumberCard;
  confidence: number; // 0-1
}

/**
 * A recall attempt record
 */
export interface RecallAttempt {
  id: string;
  timestamp: string;
  expectedItems: (string | Card | NumberCard)[];
  recalledItems: RecalledItem[];
  duration: number; // seconds
}

/**
 * Palace location for memory palace exercises
 */
export interface PalaceLocation {
  id: string;
  name: string;
  description: string;
  position: number;
  x: number;
  y: number;
  z: number;
}

/**
 * Memory palace exercise session
 */
export interface PalaceExerciseSession {
  id: string;
  palaceId: string;
  palaceName: string;
  exerciseType: 'spatial' | 'recall';
  startTime: string;
  endTime: string;
  duration: number; // in seconds
  score: number;
  totalItems: number;
  correctItems: number;
  accuracy: number;
  difficulty: string;
}

/**
 * Memory palace stats
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
 * Palace exercise stats
 */
export interface PalaceExerciseStats {
  palaceId: string;
  palaceName: string;
  roomsVisited: number;
  timeElapsed: number;
  itemsPlaced: number;
}

/**
 * Memory palace room
 */
export interface PalaceRoom {
  id: string;
  name: string;
  description: string;
  locations: PalaceLocation[];
}

/**
 * Card suit types
 */
export type Suit = 'hearts' | 'diamonds' | 'clubs' | 'spades';

/**
 * Extended Card interface with suit
 */
export interface CardWithSuit {
  id: string;
  value: string | number;
  suit: Suit;
  displayText: string;
  isFlipped: boolean;
  isMatched: boolean;
}

// ============================================
// Phase 4: Extended Data Type Definitions
// ============================================

/**
 * Base interface for all memory palace items
 */
export interface MemoryPalaceItem {
  id: string;
  type: MemoryPalaceItemType;
  value: string | number | object;
  metadata: MemoryPalaceItemMetadata;
  createdAt: string;
  updatedAt: string;
}

/**
 * Supported memory palace item types
 */
export type MemoryPalaceItemType = 'word' | 'phrase' | 'image' | 'date' | 'card' | 'number';

/**
 * Metadata for memory palace items
 */
export interface MemoryPalaceItemMetadata {
  description?: string;
  tags?: string[];
  location?: string;
  room?: string;
  notes?: string;
  [key: string]: unknown;
}

/**
 * Word item for memory palace
 */
export interface WordItem extends MemoryPalaceItem {
  type: 'word';
  value: string;
  metadata: MemoryPalaceItemMetadata & {
    definition?: string;
    partOfSpeech?: string;
    language?: string;
  };
}

/**
 * Phrase item for memory palace
 */
export interface PhraseItem extends MemoryPalaceItem {
  type: 'phrase';
  value: string;
  metadata: MemoryPalaceItemMetadata & {
    source?: string;
    author?: string;
    language?: string;
  };
}

/**
 * Image item for memory palace
 */
export interface ImageItem extends MemoryPalaceItem {
  type: 'image';
  value: string; // URL or base64 data
  metadata: MemoryPalaceItemMetadata & {
    altText?: string;
    width?: number;
    height?: number;
    format?: 'jpg' | 'png' | 'gif' | 'svg' | 'webp';
    source?: 'url' | 'upload';
  };
}

/**
 * Date item for memory palace
 */
export interface DateItem extends MemoryPalaceItem {
  type: 'date';
  value: string | number; // ISO date string or timestamp
  metadata: MemoryPalaceItemMetadata & {
    dateLabel?: string;
    isEvent?: boolean;
    recurring?: boolean;
    category?: string;
  };
}

/**
 * Task item for memory palace
 */
export interface TaskItem extends MemoryPalaceItem {
  type: 'task';
  value: string;
  metadata: MemoryPalaceItemMetadata & {
    description?: string;
    status?: 'pending' | 'completed' | 'in_progress';
    dueDate?: string | number;
    priority?: 'low' | 'medium' | 'high';
  };
}

/**
 * Note item for memory palace
 */
export interface NoteItem extends MemoryPalaceItem {
  type: 'note';
  value: string;
  metadata: MemoryPalaceItemMetadata & {
    text?: string;
    date?: string | number;
  };
}

/**
 * Union type for all memory palace items
 */
export type MemoryPalaceItemUnion = WordItem | PhraseItem | ImageItem | DateItem | TaskItem | NoteItem | Card | NumberCard;

/**
 * Visualization mode types
 */
export type VisualizationMode = 'grid' | 'timeline' | 'map' | 'network';

/**
 * Location data for map visualization
 */
export interface LocationData {
  latitude: number;
  longitude: number;
  address?: string;
  city?: string;
  country?: string;
}

/**
 * Relationship data for network visualization
 */
export interface Relationship {
  id: string;
  sourceItemId: string;
  targetItemId: string;
  type: string;
  label?: string;
  strength?: number;
}

/**
 * Node data for network graph
 */
export interface GraphNode {
  id: string;
  label: string;
  type: string;
  x?: number;
  y?: number;
  radius?: number;
  color?: string;
}

/**
 * Edge data for network graph
 */
export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  label?: string;
  strength?: number;
}

/**
 * Drag and drop state
 */
export interface DragState {
  isDragging: boolean;
  draggedItemId: string | null;
  draggedItemType: MemoryPalaceItemType | null;
  sourceLocation: string | null;
  sourceRoom: string | null;
}

/**
 * Drop zone state
 */
export interface DropZoneState {
  isOver: boolean;
  targetLocation: string | null;
  targetRoom: string | null;
}
