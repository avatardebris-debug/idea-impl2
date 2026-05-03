import { Palace, Room } from '../types/palace';
import { StoryItem, StoryBuilderState, StoryBuilderConfig, StoryConnection, StoryExport, StoryImport, StoryStats } from '../types/storyBuilder';

export { StoryItem, StoryBuilderState, StoryBuilderConfig, StoryConnection, StoryExport, StoryImport, StoryStats };

const DEFAULT_CONFIG: StoryBuilderConfig = {
  maxItems: 10,
  maxStoryLength: 500,
  autoGenerate: false,
};

/**
 * Generate a story connection between two items using the loci method
 */
export const generateStoryConnection = (
  fromItem: string,
  toItem: string,
  location: string
): StoryConnection => {
  const connections = [
    `Imagine ${fromItem} traveling to ${location}, where it encounters ${toItem}.`,
    `Picture ${fromItem} at ${location}, suddenly transformed into ${toItem}.`,
    `Visualize ${fromItem} and ${toItem} interacting at ${location} in an unexpected way.`,
    `See ${fromItem} moving through ${location}, leaving a trail that becomes ${toItem}.`,
    `Envision ${fromItem} hiding inside ${location}, only to be discovered as ${toItem}.`,
  ];
  
  const connectionText = connections[Math.floor(Math.random() * connections.length)];
  
  return {
    fromItem,
    toItem,
    location,
    connectionText,
    confidence: 0.85,
  };
};

/**
 * Create a story item with a generated story connection
 */
export const createStoryItem = (
  itemText: string,
  location: string,
  previousItem?: StoryItem
): StoryItem => {
  const storyText = previousItem
    ? generateStoryConnection(previousItem.text, itemText, location).connectionText
    : `Begin your journey with ${itemText} at ${location}.`;
  
  return {
    id: `story-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    text: itemText,
    storyText,
    location,
    createdAt: new Date().toISOString(),
  };
};

/**
 * Build a complete story from items
 */
export const buildStory = (
  items: { text: string; location: string }[],
  config: StoryBuilderConfig = DEFAULT_CONFIG
): StoryBuilderState => {
  if (items.length > config.maxItems) {
    items = items.slice(0, config.maxItems);
  }

  const storyItems: StoryItem[] = [];
  let storyPreview = '';

  items.forEach((item, index) => {
    const previousItem = storyItems[storyItems.length - 1];
    const storyItem = createStoryItem(item.text, item.location, previousItem);
    storyItems.push(storyItem);
    
    if (index < 3) {
      storyPreview += storyItem.storyText + ' ';
    }
  });

  const fullStory = storyItems.map(item => item.storyText).join(' ');
  
  return {
    selectedItems: storyItems,
    storyText: fullStory,
    isGenerating: false,
    storyPreview: storyPreview.trim(),
  };
};

/**
 * Add an item to the story
 */
export const addStoryItem = (
  items: StoryItem[],
  itemText: string,
  location: string,
  config: StoryBuilderConfig = DEFAULT_CONFIG
): StoryItem[] => {
  if (items.length >= config.maxItems) {
    return items;
  }

  const previousItem = items[items.length - 1];
  const newItem = createStoryItem(itemText, location, previousItem);
  
  return [...items, newItem];
};

/**
 * Remove an item from the story
 */
export const removeStoryItem = (
  items: StoryItem[],
  itemId: string
): StoryItem[] => {
  return items.filter(item => item.id !== itemId);
};

/**
 * Update the story text
 */
export const updateStoryText = (
  items: StoryItem[],
  storyText: string
): StoryItem[] => {
  return items.map((item, index) => ({
    ...item,
    storyText: index === items.length - 1 ? storyText : item.storyText,
  }));
};

/**
 * Export story to palace items
 */
export const exportStoryToPalace = (
  storyItems: StoryItem[],
  palace: Palace,
  roomId?: string
): StoryExport => {
  const targetRoomId = roomId || palace.rooms[0]?.id;
  const targetRoom = palace.rooms.find(r => r.id === targetRoomId);
  
  if (!targetRoom) {
    throw new Error('Room not found');
  }

  const newItems = storyItems.map(item => item.text);
  const updatedRooms = [
    { ...targetRoom, items: [...targetRoom.items, ...newItems] },
    ...palace.rooms.filter(r => r.id !== targetRoomId),
  ];

  const exportData: StoryExport = {
    storyItems,
    palaceId: palace.id,
    roomId: targetRoomId,
    exportedAt: new Date().toISOString(),
  };

  return exportData;
};

/**
 * Import story from palace items
 */
export const importStoryFromPalace = (
  palace: Palace,
  roomId: string
): StoryBuilderState => {
  const room = palace.rooms.find(r => r.id === roomId);
  if (!room) {
    return {
      selectedItems: [],
      storyText: '',
      isGenerating: false,
      storyPreview: '',
    };
  }

  const storyItems: StoryItem[] = room.items.map((itemText, index) => ({
    id: `story-${index}`,
    text: itemText,
    storyText: `Item ${index + 1}: ${itemText}`,
    location: room.name,
    createdAt: new Date().toISOString(),
  }));

  const storyPreview = storyItems.slice(0, 3).map(item => item.storyText).join(' ');

  return {
    selectedItems: storyItems,
    storyText: storyItems.map(item => item.storyText).join(' '),
    isGenerating: false,
    storyPreview: storyPreview.trim(),
  };
};

/**
 * Get story statistics
 */
export const getStoryStats = (items: StoryItem[]): StoryStats => {
  const totalCharacters = items.reduce((sum, item) => sum + item.storyText.length, 0);
  const locationsUsed = [...new Set(items.map(item => item.location))];
  
  return {
    totalItems: items.length,
    averageLength: items.length > 0 ? Math.round(totalCharacters / items.length) : 0,
    totalCharacters,
    locationsUsed,
    createdAt: items[0]?.createdAt || new Date().toISOString(),
    lastModified: items.length > 0 ? items[items.length - 1].createdAt : new Date().toISOString(),
  };
};
