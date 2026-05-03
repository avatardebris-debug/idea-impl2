import React, { useState, useCallback } from 'react';
import {
  MemoryPalaceItemUnion,
  Relationship,
  VisualizationMode,
} from '../../types/memoryPalace';
import {
  VisualizationSwitcher,
  TimelineVisualization,
  MapVisualization,
  NetworkGraphVisualization,
} from '../VisualizationModes';

interface MemoryPalaceCanvasProps {
  items: MemoryPalaceItemUnion[];
  relationships: Relationship[];
  onItemSelect?: (item: MemoryPalaceItemUnion) => void;
  onRelationshipSelect?: (relationship: Relationship) => void;
}

export const MemoryPalaceCanvas: React.FC<MemoryPalaceCanvasProps> = ({
  items,
  relationships,
  onItemSelect,
  onRelationshipSelect,
}) => {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [selectedRelationship, setSelectedRelationship] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<VisualizationMode>('timeline');

  const handleItemSelect = useCallback(
    (item: MemoryPalaceItemUnion) => {
      setSelectedItem(item.id);
      setSelectedRelationship(null);
      if (onItemSelect) {
        onItemSelect(item);
      }
    },
    [onItemSelect]
  );

  const handleRelationshipSelect = useCallback(
    (relationship: Relationship) => {
      setSelectedRelationship(relationship.id);
      setSelectedItem(null);
      if (onRelationshipSelect) {
        onRelationshipSelect(relationship);
      }
    },
    [onRelationshipSelect]
  );

  const handleViewModeChange = useCallback((mode: VisualizationMode) => {
    setViewMode(mode);
  }, []);

  return (
    <div className="memory-palace-canvas">
      <VisualizationSwitcher
        currentMode={viewMode}
        onModeChange={handleViewModeChange}
      />

      <div className="memory-palace-content">
        {viewMode === 'timeline' && (
          <TimelineVisualization
            items={items}
            selectedItemId={selectedItem}
            onItemSelect={handleItemSelect}
          />
        )}

        {viewMode === 'map' && (
          <MapVisualization
            items={items}
            selectedItemId={selectedItem}
            onItemSelect={handleItemSelect}
          />
        )}

        {viewMode === 'network' && (
          <NetworkGraphVisualization
            items={items}
            relationships={relationships}
            selectedItemId={selectedItem}
            onItemSelect={handleItemSelect}
          />
        )}
      </div>

      <div className="memory-palace-status">
        <span className="memory-palace-status-item">
          {items.length} items
        </span>
        <span className="memory-palace-status-divider">|</span>
        <span className="memory-palace-status-item">
          {relationships.length} relationships
        </span>
        {selectedItem && (
          <>
            <span className="memory-palace-status-divider">|</span>
            <span className="memory-palace-status-selected">
              Selected: {selectedItem}
            </span>
          </>
        )}
      </div>
    </div>
  );
};

export default MemoryPalaceCanvas;
