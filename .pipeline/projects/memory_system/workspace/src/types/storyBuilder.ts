/**
 * Story Builder types for memory palace exercises
 */

/**
 * A story item that connects memory items through narrative
 */
export interface StoryItem {
  id: string;
  text: string;
  storyText: string;
  location: string;
  createdAt: string;
}

/**
 * State for the StoryBuilder component
 */
export interface StoryBuilderState {
  selectedItems: StoryItem[];
  storyText: string;
  isGenerating: boolean;
  storyPreview: string;
}

/**
 * Configuration options for StoryBuilder
 */
export interface StoryBuilderConfig {
  maxItems: number;
  maxStoryLength: number;
  autoGenerate: boolean;
}

/**
 * Story connection between two items
 */
export interface StoryConnection {
  fromItem: string;
  toItem: string;
  location: string;
  connectionText: string;
  confidence: number;
}

/**
 * Story export format for palace integration
 */
export interface StoryExport {
  storyItems: StoryItem[];
  palaceId: string;
  roomId: string;
  exportedAt: string;
}

/**
 * Story import format from palace
 */
export interface StoryImport {
  palaceId: string;
  roomId: string;
  items: string[];
  importAt: string;
}

/**
 * Story statistics
 */
export interface StoryStats {
  totalItems: number;
  averageLength: number;
  totalCharacters: number;
  locationsUsed: string[];
  createdAt: string;
  lastModified: string;
}
