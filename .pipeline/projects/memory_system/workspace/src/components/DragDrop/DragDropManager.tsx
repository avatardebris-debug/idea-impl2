import React, { useCallback, useState } from 'react';
import { MemoryPalaceItemUnion, ItemType } from '../../types/memoryPalace';

interface DragDropManagerProps {
  items: MemoryPalaceItemUnion[];
  onItemsChange: (items: MemoryPalaceItemUnion[]) => void;
  onItemReorder?: (fromIndex: number, toIndex: number) => void;
  onItemMoveToLocation?: (itemId: string, locationId: string) => void;
}

export const DragDropManager: React.FC<DragDropManagerProps> = ({
  items,
  onItemsChange,
  onItemReorder,
  onItemMoveToLocation,
}) => {
  const [draggedItem, setDraggedItem] = useState<MemoryPalaceItemUnion | null>(null);
  const [dragOverLocation, setDragOverLocation] = useState<string | null>(null);

  const handleDragStart = useCallback((e: React.DragEvent, item: MemoryPalaceItemUnion) => {
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', item.id);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedItem(null);
    setDragOverLocation(null);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, locationId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverLocation(locationId);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOverLocation(null);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent, locationId: string) => {
      e.preventDefault();
      setDragOverLocation(null);

      if (!draggedItem) return;

      if (onItemMoveToLocation) {
        onItemMoveToLocation(draggedItem.id, locationId);
      }

      setDraggedItem(null);
    },
    [draggedItem, onItemMoveToLocation]
  );

  const handleReorder = useCallback(
    (fromIndex: number, toIndex: number) => {
      if (onItemReorder) {
        onItemReorder(fromIndex, toIndex);
      }
    },
    [onItemReorder]
  );

  const getItemIcon = (type: ItemType): string => {
    const icons: Record<ItemType, string> = {
      word: '📝',
      phrase: '💬',
      image: '🖼️',
      date: '📅',
      task: '✅',
      note: '📌',
    };
    return icons[type] || '🔗';
  };

  return (
    <div className="drag-drop-manager">
      <div className="drag-drop-items">
        {items.map((item, index) => (
          <div
            key={item.id}
            className={`drag-drop-item ${draggedItem?.id === item.id ? 'dragging' : ''}`}
            draggable
            onDragStart={(e) => handleDragStart(e, item)}
            onDragEnd={handleDragEnd}
            onClick={() => handleReorder(index, index)}
          >
            <span className="drag-drop-item-icon">{getItemIcon(item.type)}</span>
            <span className="drag-drop-item-label">{item.metadata.title || item.type}</span>
            <span className="drag-drop-item-type">{item.type}</span>
          </div>
        ))}
      </div>

      {onItemMoveToLocation && (
        <div className="drag-drop-locations">
          <h4>Drop Locations</h4>
          <div className="drop-zone" onDragOver={(e) => handleDragOver(e, 'location-1')} onDragLeave={handleDragLeave} onDrop={(e) => handleDrop(e, 'location-1')}>
            <span>📍 Location 1</span>
            {dragOverLocation === 'location-1' && <span className="drop-highlight">Drop Here</span>}
          </div>
          <div className="drop-zone" onDragOver={(e) => handleDragOver(e, 'location-2')} onDragLeave={handleDragLeave} onDrop={(e) => handleDrop(e, 'location-2')}>
            <span>📍 Location 2</span>
            {dragOverLocation === 'location-2' && <span className="drop-highlight">Drop Here</span>}
          </div>
        </div>
      )}
    </div>
  );
};

export default DragDropManager;
