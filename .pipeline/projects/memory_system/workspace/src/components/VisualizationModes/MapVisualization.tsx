import React, { useMemo, useState } from 'react';
import { MemoryPalaceItemUnion, LocationData } from '../../types/memoryPalace';

interface MapVisualizationProps {
  items: MemoryPalaceItemUnion[];
  onItemSelect?: (item: MemoryPalaceItemUnion) => void;
  selectedItemId?: string;
}

interface ItemWithLocation extends MemoryPalaceItemUnion {
  locationData?: LocationData;
}

const getItemsWithLocation = (items: MemoryPalaceItemUnion[]): ItemWithLocation[] => {
  return items
    .filter((item) => {
      const loc = item.metadata.location;
      return loc && typeof loc === 'object' && 'latitude' in loc && 'longitude' in loc;
    })
    .map((item) => ({
      ...item,
      locationData: item.metadata.location as LocationData,
    }));
};

const getClusterCenter = (items: ItemWithLocation[]) => {
  if (items.length === 0) return { lat: 0, lng: 0 };
  const sum = items.reduce(
    (acc, item) => ({
      lat: acc.lat + (item.locationData?.latitude || 0),
      lng: acc.lng + (item.locationData?.longitude || 0),
    }),
    { lat: 0, lng: 0 }
  );
  return {
    lat: sum.lat / items.length,
    lng: sum.lng / items.length,
  };
};

export const MapVisualization: React.FC<MapVisualizationProps> = ({
  items,
  onItemSelect,
  selectedItemId,
}) => {
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const itemsWithLocation = useMemo(() => getItemsWithLocation(items), [items]);
  const center = useMemo(() => getClusterCenter(itemsWithLocation), [itemsWithLocation]);

  const handleItemSelect = (item: MemoryPalaceItemUnion) => {
    if (onItemSelect) {
      onItemSelect(item);
    }
  };

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.2, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.2, 0.5));
  const handleReset = () => {
    setZoom(1);
    setOffset({ x: 0, y: 0 });
  };

  if (itemsWithLocation.length === 0) {
    return (
      <div className="map-visualization empty">
        <p className="map-empty-message">
          No items with location data. Showing grid fallback.
        </p>
        <div className="map-grid-fallback">
          {items.slice(0, 6).map((item) => (
            <div
              key={item.id}
              className="map-grid-item"
              onClick={() => handleItemSelect(item)}
              role="button"
              tabIndex={0}
              aria-label={`Item: ${item.type}`}
            >
              <span className="map-grid-item-icon">📍</span>
              <span className="map-grid-item-label">{item.type}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const handleDragStart = (e: React.MouseEvent) => {
    const startX = e.clientX - offset.x;
    const startY = e.clientY - offset.y;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      setOffset({
        x: moveEvent.clientX - startX,
        y: moveEvent.clientY - startY,
      });
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  return (
    <div className="map-visualization" role="region" aria-label="Map visualization">
      <div className="map-controls">
        <button onClick={handleZoomIn} className="map-control-btn" aria-label="Zoom in">
          +
        </button>
        <button onClick={handleZoomOut} className="map-control-btn" aria-label="Zoom out">
          -
        </button>
        <button onClick={handleReset} className="map-control-btn" aria-label="Reset view">
          ⟲
        </button>
        <span className="map-zoom-level">{Math.round(zoom * 100)}%</span>
      </div>

      <div
        className="map-container"
        onClick={handleDragStart}
        role="button"
        tabIndex={0}
        aria-label="Map view - drag to pan"
      >
        <div
          className="map-content"
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
          }}
        >
          <div className="map-center-marker" style={{ left: '50%', top: '50%' }}>
            🎯
          </div>

          {itemsWithLocation.map((item) => {
            const lat = item.locationData?.latitude || 0;
            const lng = item.locationData?.longitude || 0;
            const latOffset = (lat - center.lat) * 1000;
            const lngOffset = (lng - center.lng) * 1000;

            return (
              <div
                key={item.id}
                className={`map-marker ${selectedItemId === item.id ? 'selected' : ''}`}
                style={{
                  left: `calc(50% + ${lngOffset}px)`,
                  top: `calc(50% + ${latOffset}px)`,
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  handleItemSelect(item);
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleItemSelect(item);
                  }
                }}
                aria-label={`${item.type} at ${lat.toFixed(4)}, ${lng.toFixed(4)}`}
                aria-selected={selectedItemId === item.id}
              >
                <div className="map-marker-pin">
                  <span className="map-marker-icon">📍</span>
                </div>
                <div className="map-marker-label">
                  {item.metadata.location?.city || item.metadata.location?.address || item.type}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="map-legend">
        <span className="map-legend-item">
          <span className="map-legend-icon">📍</span> Location
        </span>
        <span className="map-legend-item">
          <span className="map-legend-icon">🎯</span> Center
        </span>
      </div>
    </div>
  );
};

export default MapVisualization;
