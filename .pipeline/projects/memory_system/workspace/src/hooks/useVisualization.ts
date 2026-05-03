import { useState, useCallback, useMemo } from 'react';
import { VisualizationMode, MemoryPalaceItemUnion } from '../types/memoryPalace';

interface UseVisualizationState {
  mode: VisualizationMode;
  items: MemoryPalaceItemUnion[];
  selectedItemId: string | null;
  onItemSelect: (item: MemoryPalaceItemUnion) => void;
}

interface UseVisualizationActions {
  setMode: (mode: VisualizationMode) => void;
  setItems: (items: MemoryPalaceItemUnion[]) => void;
  setSelectedItem: (id: string | null) => void;
  selectItem: (item: MemoryPalaceItemUnion) => void;
}

export function useVisualization(initialMode: VisualizationMode = 'grid') {
  const [mode, setModeState] = useState<VisualizationMode>(initialMode);
  const [items, setItemsState] = useState<MemoryPalaceItemUnion[]>([]);
  const [selectedItemId, setSelectedItemState] = useState<string | null>(null);

  const setMode = useCallback((newMode: VisualizationMode) => {
    setModeState(newMode);
  }, []);

  const setItems = useCallback((newItems: MemoryPalaceItemUnion[]) => {
    setItemsState(newItems);
  }, []);

  const setSelectedItem = useCallback((id: string | null) => {
    setSelectedItemState(id);
  }, []);

  const selectItem = useCallback((item: MemoryPalaceItemUnion) => {
    setSelectedItemState(item.id);
  }, []);

  const visualizationData = useMemo(() => {
    return {
      mode,
      items,
      selectedItemId,
      onItemSelect: selectItem,
    };
  }, [mode, items, selectedItemId, selectItem]);

  return {
    state: visualizationData,
    actions: {
      setMode,
      setItems,
      setSelectedItem,
      selectItem,
    },
  };
}

export default useVisualization;
