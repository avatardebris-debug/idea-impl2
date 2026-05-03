import { useState, useCallback, useMemo } from 'react';
import {
  MemoryPalaceItemUnion,
  Relationship,
  GraphNode,
  GraphEdge,
} from '../types/memoryPalace';
import { buildGraphData } from '../components/VisualizationModes/visualizationUtils';

interface UseNetworkGraphState {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedItemId: string | null;
}

interface UseNetworkGraphActions {
  setSelectedItem: (id: string | null) => void;
  selectItem: (item: MemoryPalaceItemUnion) => void;
  handleRemoveRelationship: (edgeId: string) => void;
  handleAddRelationship: (sourceId: string, targetId: string) => void;
}

export function useNetworkGraph(
  items: MemoryPalaceItemUnion[],
  relationships: Relationship[]
) {
  const [selectedItemId, setSelectedItemState] = useState<string | null>(null);

  // Build graph data from items and relationships
  const { nodes, edges } = useMemo(() => {
    return buildGraphData(items, relationships);
  }, [items, relationships]);

  const setSelectedItem = useCallback((id: string | null) => {
    setSelectedItemState(id);
  }, []);

  const selectItem = useCallback((item: MemoryPalaceItemUnion) => {
    setSelectedItemState(item.id);
  }, []);

  const handleRemoveRelationship = useCallback((edgeId: string) => {
    // This would be handled by the parent component
    console.log('Remove relationship:', edgeId);
  }, []);

  const handleAddRelationship = useCallback((sourceId: string, targetId: string) => {
    // This would be handled by the parent component
    console.log('Add relationship:', sourceId, targetId);
  }, []);

  const state: UseNetworkGraphState = {
    nodes,
    edges,
    selectedItemId,
  };

  const actions: UseNetworkGraphActions = {
    setSelectedItem,
    selectItem,
    handleRemoveRelationship,
    handleAddRelationship,
  };

  return {
    state,
    actions,
  };
}

export default useNetworkGraph;
