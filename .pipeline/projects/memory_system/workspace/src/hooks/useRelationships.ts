import { useState, useCallback, useMemo } from 'react';
import { Relationship, MemoryPalaceItemUnion } from '../types/memoryPalace';

interface UseRelationshipsState {
  relationships: Relationship[];
  selectedItemId: string | null;
}

interface UseRelationshipsActions {
  addRelationship: (relationship: Omit<Relationship, 'id'>) => void;
  removeRelationship: (id: string) => void;
  updateRelationship: (id: string, updates: Partial<Relationship>) => void;
  getRelatedItems: (itemId: string) => Relationship[];
  getConnectedItems: (itemId: string) => string[];
  clearSelection: () => void;
}

export function useRelationships(initialRelationships: Relationship[] = []) {
  const [state, setState] = useState<UseRelationshipsState>({
    relationships: initialRelationships,
    selectedItemId: null,
  });

  const addRelationship = useCallback((relationship: Omit<Relationship, 'id'>) => {
    const newRelationship: Relationship = {
      id: `rel-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      ...relationship,
    };

    setState((prev) => ({
      ...prev,
      relationships: [...prev.relationships, newRelationship],
    }));
  }, []);

  const removeRelationship = useCallback((id: string) => {
    setState((prev) => ({
      ...prev,
      relationships: prev.relationships.filter((rel) => rel.id !== id),
    }));
  }, []);

  const updateRelationship = useCallback((id: string, updates: Partial<Relationship>) => {
    setState((prev) => ({
      ...prev,
      relationships: prev.relationships.map((rel) =>
        rel.id === id ? { ...rel, ...updates } : rel
      ),
    }));
  }, []);

  const getRelatedItems = useCallback((itemId: string): Relationship[] => {
    return state.relationships.filter(
      (rel) => rel.sourceItemId === itemId || rel.targetItemId === itemId
    );
  }, [state.relationships]);

  const getConnectedItems = useCallback((itemId: string): string[] => {
    const related = getRelatedItems(itemId);
    return related.map((rel) =>
      rel.sourceItemId === itemId ? rel.targetItemId : rel.sourceItemId
    );
  }, [getRelatedItems]);

  const clearSelection = useCallback(() => {
    setState((prev) => ({
      ...prev,
      selectedItemId: null,
    }));
  }, []);

  const relationshipStats = useMemo(() => {
    const stats = {
      total: state.relationships.length,
      byType: {} as Record<string, number>,
      byStrength: {
        strong: 0,
        medium: 0,
        weak: 0,
        undefined: 0,
      },
    };

    state.relationships.forEach((rel) => {
      // Count by type
      stats.byType[rel.type] = (stats.byType[rel.type] || 0) + 1;

      // Count by strength (handle undefined/null values)
      if (rel.strength === undefined || rel.strength === null) {
        stats.byStrength.undefined++;
      } else if (rel.strength >= 0.7) {
        stats.byStrength.strong++;
      } else if (rel.strength >= 0.4) {
        stats.byStrength.medium++;
      } else if (rel.strength < 0.4) {
        stats.byStrength.weak++;
      }
    });

    return stats;
  }, [state.relationships]);

  return {
    state: {
      relationships: state.relationships,
      selectedItemId: state.selectedItemId,
    },
    actions: {
      addRelationship,
      removeRelationship,
      updateRelationship,
      getRelatedItems,
      getConnectedItems,
      clearSelection,
    },
    stats: relationshipStats,
  };
}

export default useRelationships;
