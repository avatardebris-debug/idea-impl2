import { describe, it, expect } from 'vitest';
import {
  generateStoryConnection,
  createStoryItem,
  buildStory,
  addStoryItem,
  removeStoryItem,
  updateStoryText,
  exportStoryToPalace,
  importStoryFromPalace,
  getStoryStats,
  StoryItem,
  StoryBuilderState,
  StoryBuilderConfig,
} from '../src/utils/storyBuilder';
import { Palace, Room } from '../src/types/palace';

describe('StoryBuilder', () => {
  describe('generateStoryConnection', () => {
    it('should generate a story connection between two items', () => {
      const connection = generateStoryConnection('apple', 'banana', 'kitchen');
      
      expect(connection.fromItem).toBe('apple');
      expect(connection.toItem).toBe('banana');
      expect(connection.location).toBe('kitchen');
      expect(connection.connectionText).toContain('apple');
      expect(connection.connectionText).toContain('banana');
      expect(connection.connectionText).toContain('kitchen');
      expect(connection.confidence).toBe(0.85);
    });

    it('should generate different connection types', () => {
      const connections = [
        generateStoryConnection('cat', 'dog', 'park'),
        generateStoryConnection('book', 'pen', 'library'),
        generateStoryConnection('car', 'house', 'street'),
      ];

      // All should have valid connection text
      connections.forEach(conn => {
        expect(conn.connectionText).toBeDefined();
        expect(conn.connectionText.length).toBeGreaterThan(0);
      });
    });
  });

  describe('createStoryItem', () => {
    it('should create a story item with a connection', () => {
      const previousItem: StoryItem = {
        id: 'item-1',
        text: 'apple',
        storyText: 'Start with apple at kitchen',
        location: 'kitchen',
        createdAt: new Date().toISOString(),
      };

      const newItem = createStoryItem('banana', 'living room', previousItem);

      expect(newItem.text).toBe('banana');
      expect(newItem.location).toBe('living room');
      expect(newItem.storyText).toContain('apple');
      expect(newItem.storyText).toContain('banana');
      expect(newItem.storyText).toContain('living room');
    });

    it('should create a story item without a previous item', () => {
      const newItem = createStoryItem('apple', 'kitchen');

      expect(newItem.text).toBe('apple');
      expect(newItem.location).toBe('kitchen');
      expect(newItem.storyText).toContain('apple');
      expect(newItem.storyText).toContain('kitchen');
    });
  });

  describe('buildStory', () => {
    it('should build a story from items', () => {
      const items = [
        { text: 'apple', location: 'kitchen' },
        { text: 'banana', location: 'living room' },
        { text: 'orange', location: 'bedroom' },
      ];

      const state = buildStory(items);

      expect(state.selectedItems.length).toBe(3);
      expect(state.storyText).toContain('apple');
      expect(state.storyText).toContain('banana');
      expect(state.storyText).toContain('orange');
      expect(state.storyPreview).toBeDefined();
      expect(state.isGenerating).toBe(false);
    });

    it('should respect maxItems limit', () => {
      const items = Array.from({ length: 15 }, (_, i) => ({
        text: `item-${i}`,
        location: `room-${i}`,
      }));

      const config: StoryBuilderConfig = { maxItems: 5, maxStoryLength: 500, autoGenerate: false };
      const state = buildStory(items, config);

      expect(state.selectedItems.length).toBe(5);
    });

    it('should generate story preview', () => {
      const items = [
        { text: 'apple', location: 'kitchen' },
        { text: 'banana', location: 'living room' },
        { text: 'orange', location: 'bedroom' },
        { text: 'grape', location: 'dining room' },
      ];

      const state = buildStory(items);

      expect(state.storyPreview).toBeDefined();
      expect(state.storyPreview.length).toBeGreaterThan(0);
    });
  });

  describe('addStoryItem', () => {
    it('should add a story item', () => {
      const items: StoryItem[] = [
        {
          id: 'item-1',
          text: 'apple',
          storyText: 'Start with apple at kitchen',
          location: 'kitchen',
          createdAt: new Date().toISOString(),
        },
      ];

      const config: StoryBuilderConfig = { maxItems: 10, maxStoryLength: 500, autoGenerate: false };
      const result = addStoryItem(items, 'banana', 'living room', config);

      expect(result.length).toBe(2);
      expect(result[1].text).toBe('banana');
      expect(result[1].location).toBe('living room');
    });

    it('should not exceed maxItems', () => {
      const items: StoryItem[] = Array.from({ length: 10 }, (_, i) => ({
        id: `item-${i}`,
        text: `item-${i}`,
        storyText: `Story ${i}`,
        location: `room-${i}`,
        createdAt: new Date().toISOString(),
      }));

      const config: StoryBuilderConfig = { maxItems: 10, maxStoryLength: 500, autoGenerate: false };
      const result = addStoryItem(items, 'new-item', 'new-room', config);

      expect(result.length).toBe(10);
    });
  });

  describe('removeStoryItem', () => {
    it('should remove a story item', () => {
      const items: StoryItem[] = [
        {
          id: 'item-1',
          text: 'apple',
          storyText: 'Start with apple at kitchen',
          location: 'kitchen',
          createdAt: new Date().toISOString(),
        },
        {
          id: 'item-2',
          text: 'banana',
          storyText: 'Story 2',
          location: 'living room',
          createdAt: new Date().toISOString(),
        },
      ];

      const result = removeStoryItem(items, 'item-1');

      expect(result.length).toBe(1);
      expect(result[0].id).toBe('item-2');
    });

    it('should not remove non-existent item', () => {
      const items: StoryItem[] = [
        {
          id: 'item-1',
          text: 'apple',
          storyText: 'Start with apple at kitchen',
          location: 'kitchen',
          createdAt: new Date().toISOString(),
        },
      ];

      const result = removeStoryItem(items, 'non-existent');

      expect(result.length).toBe(1);
      expect(result[0].id).toBe('item-1');
    });
  });

  describe('updateStoryText', () => {
    it('should update story text', () => {
      const items: StoryItem[] = [
        {
          id: 'item-1',
          text: 'apple',
          storyText: 'Start with apple at kitchen',
          location: 'kitchen',
          createdAt: new Date().toISOString(),
        },
      ];

      const result = updateStoryText(items, 'Updated story text');

      expect(result[0].storyText).toBe('Updated story text');
    });
  });

  describe('exportStoryToPalace', () => {
    it('should export story to palace', () => {
      const palace: Palace = {
        id: 'palace-1',
        name: 'Memory Palace',
        description: 'A memory palace',
        rooms: [
          {
            id: 'room-1',
            name: 'Kitchen',
            description: 'A kitchen',
            items: ['apple', 'banana'],
          },
        ],
        createdAt: new Date().toISOString(),
      };

      const storyItems: StoryItem[] = [
        {
          id: 'story-1',
          text: 'orange',
          storyText: 'Story about orange',
          location: 'kitchen',
          createdAt: new Date().toISOString(),
        },
      ];

      const exportData = exportStoryToPalace(storyItems, palace);

      expect(exportData.palaceId).toBe('palace-1');
      expect(exportData.roomId).toBe('room-1');
      expect(exportData.storyItems.length).toBe(1);
      expect(exportData.exportedAt).toBeDefined();
    });

    it('should throw error for non-existent room', () => {
      const palace: Palace = {
        id: 'palace-1',
        name: 'Memory Palace',
        description: 'A memory palace',
        rooms: [
          {
            id: 'room-1',
            name: 'Kitchen',
            description: 'A kitchen',
            items: ['apple', 'banana'],
          },
        ],
        createdAt: new Date().toISOString(),
      };

      const storyItems: StoryItem[] = [
        {
          id: 'story-1',
          text: 'orange',
          storyText: 'Story about orange',
          location: 'kitchen',
          createdAt: new Date().toISOString(),
        },
      ];

      expect(() => exportStoryToPalace(storyItems, palace, 'non-existent-room')).toThrow('Room not found');
    });
  });

  describe('importStoryFromPalace', () => {
    it('should import story from palace', () => {
      const palace: Palace = {
        id: 'palace-1',
        name: 'Memory Palace',
        description: 'A memory palace',
        rooms: [
          {
            id: 'room-1',
            name: 'Kitchen',
            description: 'A kitchen',
            items: ['apple', 'banana'],
          },
        ],
        createdAt: new Date().toISOString(),
      };

      const storyItems: StoryItem[] = [
        {
          id: 'story-1',
          text: 'orange',
          storyText: 'Story about orange',
          location: 'kitchen',
          createdAt: new Date().toISOString(),
        },
      ];

      const importData = importStoryFromPalace(storyItems, palace);

      expect(importData.palaceId).toBe('palace-1');
      expect(importData.roomId).toBe('room-1');
      expect(importData.storyItems.length).toBe(1);
    });
  });

  describe('getStoryStats', () => {
    it('should calculate story statistics', () => {
      const items: StoryItem[] = [
        {
          id: 'item-1',
          text: 'apple',
          storyText: 'Start with apple at kitchen',
          location: 'kitchen',
          createdAt: new Date().toISOString(),
        },
        {
          id: 'item-2',
          text: 'banana',
          storyText: 'Story about banana',
          location: 'living room',
          createdAt: new Date().toISOString(),
        },
      ];

      const stats = getStoryStats(items);

      expect(stats.totalItems).toBe(2);
      expect(stats.totalCharacters).toBeGreaterThan(0);
      expect(stats.locationsUsed).toContain('kitchen');
      expect(stats.locationsUsed).toContain('living room');
      expect(stats.createdAt).toBeDefined();
      expect(stats.lastModified).toBeDefined();
    });

    it('should handle empty items array', () => {
      const stats = getStoryStats([]);

      expect(stats.totalItems).toBe(0);
      expect(stats.averageLength).toBe(0);
      expect(stats.totalCharacters).toBe(0);
      expect(stats.locationsUsed).toEqual([]);
    });
  });
});
