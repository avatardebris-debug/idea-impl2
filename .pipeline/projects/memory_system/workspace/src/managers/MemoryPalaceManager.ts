import { Palace, PalaceStats, PalaceExerciseStats, Room } from '../types/palace';
import {
  MemoryPalaceItemUnion,
  MemoryPalaceItemType,
  Relationship,
  GraphNode,
  GraphEdge,
  VisualizationMode,
} from '../types/memoryPalace';

const STORAGE_KEY = 'memory_palaces';

/**
 * MemoryPalaceManager
 * Manages memory palaces and their data
 */
export class MemoryPalaceManager {
  private palaces: Palace[] = [];
  private items: Map<string, MemoryPalaceItemUnion> = new Map();
  private relationships: Map<string, Relationship> = new Map();

  constructor() {
    this.loadPalaces();
  }

  /**
   * Load palaces from localStorage
   */
  private loadPalaces(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        this.palaces = data.palaces || [];
        this.items = new Map(data.items || []);
        this.relationships = new Map(data.relationships || []);
      }
    } catch (error) {
      console.error('Error loading palaces:', error);
      this.palaces = [];
      this.items = new Map();
      this.relationships = new Map();
    }
  }

  /**
   * Save palaces to localStorage
   */
  private savePalaces(): void {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          palaces: this.palaces,
          items: Array.from(this.items.entries()),
          relationships: Array.from(this.relationships.entries()),
        })
      );
    } catch (error) {
      console.error('Error saving palaces:', error);
    }
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `palace_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Generate unique item ID
   */
  private generateItemId(): string {
    return `item_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get all palaces
   */
  getAllPalaces(): Palace[] {
    return this.palaces;
  }

  /**
   * Get a specific palace
   */
  getPalace(palaceId: string): Palace | null {
    return this.palaces.find(p => p.id === palaceId) || null;
  }

  /**
   * Create a new memory palace
   */
  createPalace(name: string, description: string = ''): Palace {
    const palace: Palace = {
      id: this.generateId(),
      name,
      description,
      rooms: [],
      createdAt: new Date().toISOString(),
    };

    this.palaces.push(palace);
    this.savePalaces();

    return palace;
  }

  /**
   * Delete a palace
   */
  deletePalace(palaceId: string): boolean {
    const index = this.palaces.findIndex(p => p.id === palaceId);
    if (index === -1) {
      return false;
    }

    this.palaces.splice(index, 1);

    // Remove all items and relationships associated with this palace
    for (const [itemId, item] of this.items.entries()) {
      if (item.metadata.room && item.metadata.room.startsWith(palaceId)) {
        this.items.delete(itemId);
      }
    }

    for (const [relId, rel] of this.relationships.entries()) {
      if (
        rel.sourceItemId.startsWith(palaceId) ||
        rel.targetItemId.startsWith(palaceId)
      ) {
        this.relationships.delete(relId);
      }
    }

    this.savePalaces();
    return true;
  }

  /**
   * Update a palace
   */
  updatePalace(palace: Palace): Palace {
    const index = this.palaces.findIndex(p => p.id === palace.id);
    if (index === -1) {
      return palace;
    }

    this.palaces[index] = palace;
    this.savePalaces();

    return palace;
  }

  /**
   * Add a room to a palace
   */
  addRoom(palaceId: string, roomName: string, roomDescription: string = ''): Room | null {
    const palace = this.getPalace(palaceId);
    if (!palace) {
      return null;
    }

    const room: Room = {
      id: this.generateId(),
      name: roomName,
      description: roomDescription,
      items: [],
    };

    palace.rooms.push(room);
    this.updatePalace(palace);

    return room;
  }

  /**
   * Remove a room from a palace
   */
  removeRoom(palaceId: string, roomId: string): boolean {
    const palace = this.getPalace(palaceId);
    if (!palace) {
      return false;
    }

    const index = palace.rooms.findIndex(r => r.id === roomId);
    if (index === -1) {
      return false;
    }

    palace.rooms.splice(index, 1);
    this.updatePalace(palace);

    return true;
  }

  /**
   * Add an item to a room
   */
  addItemToRoom(
    palaceId: string,
    roomId: string,
    itemType: MemoryPalaceItemType,
    value: string | number | object,
    metadata: Record<string, unknown> = {}
  ): MemoryPalaceItemUnion | null {
    const palace = this.getPalace(palaceId);
    if (!palace) {
      return null;
    }

    const room = palace.rooms.find(r => r.id === roomId);
    if (!room) {
      return null;
    }

    const item: MemoryPalaceItemUnion = {
      id: this.generateItemId(),
      type: itemType,
      value,
      metadata: {
        ...metadata,
        room: `${palaceId}_${roomId}`,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.items.set(item.id, item);
    room.items.push(item.id);
    this.updatePalace(palace);

    return item;
  }

  /**
   * Remove an item from a room
   */
  removeItemFromRoom(palaceId: string, roomId: string, itemId: string): boolean {
    const palace = this.getPalace(palaceId);
    if (!palace) {
      return false;
    }

    const room = palace.rooms.find(r => r.id === roomId);
    if (!room) {
      return false;
    }

    const index = room.items.indexOf(itemId);
    if (index === -1) {
      return false;
    }

    room.items.splice(index, 1);
    this.items.delete(itemId);
    this.updatePalace(palace);

    return true;
  }

  /**
   * Get all items in a palace
   */
  getPalaceItems(palaceId: string): MemoryPalaceItemUnion[] {
    const palace = this.getPalace(palaceId);
    if (!palace) {
      return [];
    }

    const itemIds = palace.rooms.flatMap(room => room.items);
    return itemIds
      .map(id => this.items.get(id))
      .filter((item): item is MemoryPalaceItemUnion => item !== undefined);
  }

  /**
   * Get all items in a specific room
   */
  getRoomItems(palaceId: string, roomId: string): MemoryPalaceItemUnion[] {
    const palace = this.getPalace(palaceId);
    if (!palace) {
      return [];
    }

    const room = palace.rooms.find(r => r.id === roomId);
    if (!room) {
      return [];
    }

    return room.items
      .map(id => this.items.get(id))
      .filter((item): item is MemoryPalaceItemUnion => item !== undefined);
  }

  /**
   * Update an item
   */
  updateItem(itemId: string, updates: Partial<MemoryPalaceItemUnion>): MemoryPalaceItemUnion | null {
    const item = this.items.get(itemId);
    if (!item) {
      return null;
    }

    const updatedItem = {
      ...item,
      ...updates,
      updatedAt: new Date().toISOString(),
    };

    this.items.set(itemId, updatedItem);
    this.savePalaces();

    return updatedItem;
  }

  /**
   * Add a relationship between items
   */
  addRelationship(
    sourceItemId: string,
    targetItemId: string,
    type: string,
    label?: string,
    strength?: number
  ): Relationship | null {
    const sourceItem = this.items.get(sourceItemId);
    const targetItem = this.items.get(targetItemId);

    if (!sourceItem || !targetItem) {
      return null;
    }

    const relationship: Relationship = {
      id: this.generateId(),
      sourceItemId,
      targetItemId,
      type,
      label: label || type,
      strength: strength || 1,
    };

    this.relationships.set(relationship.id, relationship);
    this.savePalaces();

    return relationship;
  }

  /**
   * Remove a relationship
   */
  removeRelationship(relationshipId: string): boolean {
    return this.relationships.delete(relationshipId);
  }

  /**
   * Get all relationships for an item
   */
  getItemRelationships(itemId: string): Relationship[] {
    return Array.from(this.relationships.values()).filter(
      rel => rel.sourceItemId === itemId || rel.targetItemId === itemId
    );
  }

  /**
   * Get graph data for network visualization
   */
  getGraphData(palaceId: string): { nodes: GraphNode[]; edges: GraphEdge[] } {
    const items = this.getPalaceItems(palaceId);
    const relationships = this.getItemRelationshipsForPalace(palaceId);

    const nodes: GraphNode[] = items.map(item => ({
      id: item.id,
      label: typeof item.value === 'string' ? item.value : String(item.value),
      type: item.type,
      color: this.getItemColor(item.type),
    }));

    const edges: GraphEdge[] = relationships.map(rel => ({
      id: rel.id,
      source: rel.sourceItemId,
      target: rel.targetItemId,
      type: rel.type,
      label: rel.label,
      strength: rel.strength,
    }));

    return { nodes, edges };
  }

  /**
   * Get relationships for a specific palace
   */
  private getItemRelationshipsForPalace(palaceId: string): Relationship[] {
    const palaceItems = this.getPalaceItems(palaceId);
    const palaceItemIds = new Set(palaceItems.map(item => item.id));

    return Array.from(this.relationships.values()).filter(
      rel => palaceItemIds.has(rel.sourceItemId) && palaceItemIds.has(rel.targetItemId)
    );
  }

  /**
   * Get visualization data for a specific mode
   */
  getVisualizationData(palaceId: string, mode: VisualizationMode): any {
    switch (mode) {
      case 'network':
        return this.getGraphData(palaceId);
      case 'timeline':
        return this.getTimelineData(palaceId);
      case 'map':
        return this.getMapData(palaceId);
      default:
        return this.getGridData(palaceId);
    }
  }

  /**
   * Get grid data for visualization
   */
  private getGridData(palaceId: string): { rooms: any[] } {
    const palace = this.getPalace(palaceId);
    if (!palace) {
      return { rooms: [] };
    }

    return {
      rooms: palace.rooms.map(room => ({
        id: room.id,
        name: room.name,
        description: room.description,
        itemCount: room.items.length,
        items: room.items.map(itemId => this.items.get(itemId)),
      })),
    };
  }

  /**
   * Get timeline data for visualization
   */
  private getTimelineData(palaceId: string): { events: any[] } {
    const items = this.getPalaceItems(palaceId);

    return {
      events: items
        .filter(item => item.type === 'date' || item.metadata.date)
        .map(item => ({
          id: item.id,
          label: typeof item.value === 'string' ? item.value : String(item.value),
          timestamp: item.metadata.date || item.createdAt,
          type: item.type,
        }))
        .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()),
    };
  }

  /**
   * Get map data for visualization
   */
  private getMapData(palaceId: string): { locations: any[] } {
    const items = this.getPalaceItems(palaceId);

    return {
      locations: items
        .filter(item => item.metadata.location)
        .map(item => ({
          id: item.id,
          label: typeof item.value === 'string' ? item.value : String(item.value),
          location: item.metadata.location,
          type: item.type,
        })),
    };
  }

  /**
   * Get item color based on type
   */
  private getItemColor(type: MemoryPalaceItemType): string {
    const colors: Record<MemoryPalaceItemType, string> = {
      word: '#3498db',
      phrase: '#9b59b6',
      image: '#e74c3c',
      date: '#2ecc71',
      card: '#f39c12',
      number: '#1abc9c',
    };
    return colors[type] || '#95a5a6';
  }

  /**
   * Get palace statistics
   */
  getPalaceStats(palaceId: string): PalaceStats | null {
    const palace = this.getPalace(palaceId);
    if (!palace) {
      return null;
    }

    // Count total items
    const totalItems = palace.rooms.reduce((sum, room) => sum + room.items.length, 0);

    // Get exercise session history (would come from ExerciseSessionManager in real app)
    const sessionHistory: any[] = [];

    return {
      palaceId: palace.id,
      palaceName: palace.name,
      totalSessions: sessionHistory.length,
      totalAttempts: sessionHistory.reduce((sum, s) => sum + s.totalItems, 0),
      correctRecalls: sessionHistory.reduce((sum, s) => sum + s.correctItems, 0),
      totalRooms: palace.rooms.length,
      lastSessionTimestamp: sessionHistory.length > 0 ? sessionHistory[sessionHistory.length - 1].endTime : null,
      firstSessionTimestamp: sessionHistory.length > 0 ? sessionHistory[0].startTime : null,
      sessionHistory,
    };
  }

  /**
   * Get exercise statistics for a palace
   */
  getPalaceExerciseStats(palaceId: string): PalaceExerciseStats | null {
    const palace = this.getPalace(palaceId);
    if (!palace) {
      return null;
    }

    const totalItems = palace.rooms.reduce((sum, room) => sum + room.items.length, 0);

    return {
      palaceId: palace.id,
      palaceName: palace.name,
      roomsVisited: palace.rooms.length,
      timeElapsed: 0, // Would be calculated from exercise sessions
      itemsPlaced: totalItems,
    };
  }

  /**
   * Search items in a palace
   */
  searchItems(palaceId: string, query: string): MemoryPalaceItemUnion[] {
    const items = this.getPalaceItems(palaceId);
    const searchLower = query.toLowerCase();

    return items.filter(item => {
      const valueStr = typeof item.value === 'string' ? item.value : String(item.value);
      const metadataStr = JSON.stringify(item.metadata).toLowerCase();

      return (
        valueStr.toLowerCase().includes(searchLower) ||
        metadataStr.includes(searchLower)
      );
    });
  }

  /**
   * Export palace data
   */
  exportPalace(palaceId: string): string {
    const palace = this.getPalace(palaceId);
    if (!palace) {
      return '';
    }

    const exportData = {
      palace,
      items: this.getPalaceItems(palaceId),
      relationships: this.getItemRelationshipsForPalace(palaceId),
      exportedAt: new Date().toISOString(),
    };

    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Import palace data
   */
  importPalaceData(jsonData: string): Palace | null {
    try {
      const data = JSON.parse(jsonData);
      const palace = data.palace as Palace;

      // Validate palace structure
      if (!palace.id || !palace.name || !palace.rooms) {
        return null;
      }

      // Check if palace already exists
      if (this.getPalace(palace.id)) {
        return null;
      }

      // Add palace
      this.palaces.push(palace);

      // Add items
      if (data.items) {
        for (const item of data.items) {
          this.items.set(item.id, item);
          // Update room item references
          const room = palace.rooms.find(r => r.id === item.metadata.room);
          if (room && !room.items.includes(item.id)) {
            room.items.push(item.id);
          }
        }
      }

      // Add relationships
      if (data.relationships) {
        for (const rel of data.relationships) {
          this.relationships.set(rel.id, rel);
        }
      }

      this.savePalaces();

      return palace;
    } catch (error) {
      console.error('Error importing palace data:', error);
      return null;
    }
  }
}

// Export singleton instance
export const memoryPalaceManager = new MemoryPalaceManager();
