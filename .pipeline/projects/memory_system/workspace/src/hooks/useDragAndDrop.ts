/**
 * Custom hook for drag and drop functionality
 */

import { useState, useCallback, useRef } from 'react';
import { MemoryPalaceItemUnion, MemoryPalaceItemType, DragState, DropZoneState } from '../types/memoryPalace';

interface UseDragAndDropProps {
  items: MemoryPalaceItemUnion[];
  onItemMove?: (itemId: string, newLocation: string, newRoom: string) => void;
  onItemCreate?: (item: MemoryPalaceItemUnion, location: string, room: string) => void;
}

interface UseDragAndDropReturn {
  dragState: DragState;
  dropZoneState: DropZoneState;
  handleDragStart: (e: React.DragEvent, item: MemoryPalaceItemUnion) => void;
  handleDragOver: (e: React.DragEvent) => void;
  handleDrop: (e: React.DragEvent, location: string, room: string) => void;
  handleDragEnter: (location: string, room: string) => void;
  handleDragLeave: () => void;
  handleDragEnd: () => void;
  isDraggable: (item: MemoryPalaceItemUnion) => boolean;
}

export const useDragAndDrop = ({
  items,
  onItemMove,
  onItemCreate,
}: UseDragAndDropProps): UseDragAndDropReturn => {
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    draggedItemId: null,
    draggedItemType: null,
    sourceLocation: null,
    sourceRoom: null,
  });

  const [dropZoneState, setDropZoneState] = useState<DropZoneState>({
    isOver: false,
    targetLocation: null,
    targetRoom: null,
  });

  const handleDragStart = useCallback((
    e: React.DragEvent,
    item: MemoryPalaceItemUnion
  ) => {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', item.id);

    setDragState({
      isDragging: true,
      draggedItemId: item.id,
      draggedItemType: item.type,
      sourceLocation: item.metadata.location?.location || null,
      sourceRoom: item.metadata.location?.room || null,
    });
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  const handleDrop = useCallback((
    e: React.DragEvent,
    location: string,
    room: string
  ) => {
    e.preventDefault();
    const itemId = e.dataTransfer.getData('text/plain');

    if (!itemId) return;

    const item = items.find((i) => i.id === itemId);
    if (!item) return;

    if (onItemMove && item.metadata.location?.location === location && item.metadata.location?.room === room) {
      // Item is already in this location/room, no action needed
      setDragState({
        isDragging: false,
        draggedItemId: null,
        draggedItemType: null,
        sourceLocation: null,
        sourceRoom: null,
      });
      setDropZoneState({
        isOver: false,
        targetLocation: null,
        targetRoom: null,
      });
      return;
    }

    if (onItemMove) {
      onItemMove(itemId, location, room);
    }

    setDragState({
      isDragging: false,
      draggedItemId: null,
      draggedItemType: null,
      sourceLocation: null,
      sourceRoom: null,
    });
    setDropZoneState({
      isOver: false,
      targetLocation: null,
      targetRoom: null,
    });
  }, [items, onItemMove]);

  const handleDragEnter = useCallback((location: string, room: string) => {
    setDropZoneState({
      isOver: true,
      targetLocation: location,
      targetRoom: room,
    });
  }, []);

  const handleDragLeave = useCallback(() => {
    setDropZoneState({
      isOver: false,
      targetLocation: null,
      targetRoom: null,
    });
  }, []);

  const handleDragEnd = useCallback(() => {
    setDragState({
      isDragging: false,
      draggedItemId: null,
      draggedItemType: null,
      sourceLocation: null,
      sourceRoom: null,
    });
    setDropZoneState({
      isOver: false,
      targetLocation: null,
      targetRoom: null,
    });
  }, []);

  const isDraggable = useCallback((item: MemoryPalaceItemUnion): boolean => {
    // Items can be dragged if they have location data
    return item.metadata.location !== null && item.metadata.location !== undefined;
  }, []);

  return {
    dragState,
    dropZoneState,
    handleDragStart,
    handleDragOver,
    handleDrop,
    handleDragEnter,
    handleDragLeave,
    handleDragEnd,
    isDraggable,
  };
};

export default useDragAndDrop;
