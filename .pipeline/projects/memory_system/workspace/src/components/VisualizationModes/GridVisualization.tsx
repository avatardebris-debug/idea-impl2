import React, { useMemo } from 'react';
import { MemoryPalaceItemUnion } from '../../types/memoryPalace';

interface GridVisualizationProps {
  items: MemoryPalaceItemUnion[];
  onItemSelect?: (item: MemoryPalaceItemUnion) => void;
  selectedItemId?: string;
}

const getItemIcon = (type: string): string => {
  const icons: Record<string, string> = {
    word: '📝',
    phrase: '💬',
    image: '🖼️',
    date: '📅',
    task: '✅',
    note: '📌',
    card: '🎴',
    number: '🔢',
  };
  return icons[type] || '🔗';
};

const getItemColor = (type: string): string => {
  const colors: Record<string, string> = {
    word: '#4CAF50',
    phrase: '#2196F3',
    image: '#9C27B0',
    date: '#FF9800',
    task: '#f44336',
    note: '#607D8B',
    card: '#FF5722',
    number: '#795548',
  };
  return colors[type] || '#666666';
};

const GridVisualization: React.FC<GridVisualizationProps> = ({
  items,
  onItemSelect,
  selectedItemId,
}) => {
  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => {
      // Sort by type first, then by creation date
      if (a.type !== b.type) {
        return a.type.localeCompare(b.type);
      }
      return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
    });
  }, [items]);

  const handleItemClick = (item: MemoryPalaceItemUnion) => {
    if (onItemSelect) {
      onItemSelect(item);
    }
  };

  if (items.length === 0) {
    return (
      <div className="grid-visualization">
        <div className="grid-empty-state">
          <div className="empty-icon">📦</div>
          <h3>No items to display</h3>
          <p>Add items to your memory palace to see them here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid-visualization">
      <div className="grid-header">
        <h2>Memory Palace Items</h2>
        <span className="item-count">{items.length} items</span>
      </div>

      <div className="grid-container">
        {sortedItems.map((item) => {
          const isSelected = selectedItemId === item.id;
          const icon = getItemIcon(item.type);
          const color = getItemColor(item.type);

          return (
            <div
              key={item.id}
              className={`grid-item ${isSelected ? 'selected' : ''}`}
              onClick={() => handleItemClick(item)}
              style={{ borderLeftColor: color }}
            >
              <div className="grid-item-icon">{icon}</div>
              <div className="grid-item-content">
                <div className="grid-item-title">
                  {item.metadata.title || 
                   (item.type === 'word' ? item.value : 
                    item.type === 'phrase' ? item.value :
                    item.type === 'date' ? new Date(item.value).toLocaleDateString() :
                    item.type === 'card' ? (item as any).name :
                    item.type === 'number' ? String(item.value) :
                    item.value)}
                </div>
                {item.metadata.description && (
                  <div className="grid-item-description">
                    {item.metadata.description}
                  </div>
                )}
                <div className="grid-item-meta">
                  <span className="grid-item-type">{item.type}</span>
                  <span className="grid-item-date">
                    {new Date(item.createdAt).toLocaleDateString()}
                  </span>
                </div>
              </div>
              {isSelected && <div className="grid-item-selected-indicator"></div>}
            </div>
          );
        })}
      </div>

      <div className="grid-footer">
        <div className="grid-legend">
          <h4>Item Types</h4>
          <div className="legend-grid">
            <div className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: '#4CAF50' }}></span>
              <span>Word</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: '#2196F3' }}></span>
              <span>Phrase</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: '#9C27B0' }}></span>
              <span>Image</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: '#FF9800' }}></span>
              <span>Date</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: '#f44336' }}></span>
              <span>Task</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: '#607D8B' }}></span>
              <span>Note</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: '#FF5722' }}></span>
              <span>Card</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: '#795548' }}></span>
              <span>Number</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GridVisualization;
