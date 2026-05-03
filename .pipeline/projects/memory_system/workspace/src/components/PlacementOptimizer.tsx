import React, { useState, useCallback } from 'react';
import { usePlacementRecommendations } from '../hooks/usePlacementRecommendations';
import { Card, NumberCard, PalaceRoom, PalaceLocation } from '../types/memoryPalace';
import { Suit } from '../types/cards';
import './PlacementOptimizer.css';

interface PlacementOptimizerProps {
  items: (string | Card | NumberCard)[];
  rooms: PalaceRoom[];
  onPlacementComplete?: (placements: Array<{
    itemId: string;
    roomId: string;
    locationIndex: number;
    confidence: number;
  }>) => void;
  enabled?: boolean;
}

interface ItemWithCharacteristics {
  item: string | Card | NumberCard;
  characteristics: {
    type: 'card' | 'number' | 'text';
    category?: string;
    complexity: 'simple' | 'medium' | 'complex';
    visualStrength: number;
    emotionalContent: number;
    size: 'small' | 'medium' | 'large';
  };
}

const PlacementOptimizer: React.FC<PlacementOptimizerProps> = ({
  items,
  rooms,
  onPlacementComplete,
  enabled = true,
}) => {
  const {
    recommendations,
    isLoading,
    error,
    refresh,
    getSuggestionsForItem,
  } = usePlacementRecommendations({
    items,
    rooms,
    enabled,
  });

  const [selectedItem, setSelectedItem] = useState<string | Card | NumberCard | null>(null);
  const [excludeLocations, setExcludeLocations] = useState<
    Array<{ roomId: string; locationIndex: number }>
  >([]);

  const handleOptimize = useCallback(() => {
    refresh();
  }, [refresh]);

  const handleItemSelect = useCallback((item: string | Card | NumberCard) => {
    setSelectedItem(item);
  }, []);

  const handlePlaceItem = useCallback((
    itemId: string,
    roomId: string,
    locationIndex: number
  ) => {
    setExcludeLocations(prev => [
      ...prev,
      { roomId, locationIndex },
    ]);
    setSelectedItem(null);
  }, []);

  const handleClearExclusions = useCallback(() => {
    setExcludeLocations([]);
  }, []);

  const handlePlacementComplete = useCallback((
    placements: Array<{
      itemId: string;
      roomId: string;
      locationIndex: number;
      confidence: number;
    }>
  ) => {
    onPlacementComplete?.(placements);
  }, [onPlacementComplete]);

  const getItemDisplay = (item: string | Card | NumberCard): string => {
    if (typeof item === 'string') {
      return item;
    }
    if ('displayText' in item) {
      return item.displayText;
    }
    if ('value' in item) {
      return String(item.value);
    }
    return 'Unknown';
  };

  const getDifficultyColor = (complexity: string): string => {
    switch (complexity) {
      case 'simple': return '#28a745';
      case 'medium': return '#ffc107';
      case 'complex': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getComplexityLabel = (complexity: string): string => {
    switch (complexity) {
      case 'simple': return 'Simple';
      case 'medium': return 'Medium';
      case 'complex': return 'Complex';
      default: return complexity;
    }
  };

  const getConfidenceLabel = (confidence: number): string => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return '#28a745';
    if (confidence >= 0.6) return '#ffc107';
    return '#dc3545';
  };

  return (
    <div className="placement-optimizer">
      <div className="placement-optimizer-header">
        <h2>🧠 Smart Placement Optimizer</h2>
        <p>AI-powered memory palace item placement recommendations</p>
      </div>

      {error && (
        <div className="placement-error">
          ⚠️ {error}
        </div>
      )}

      <div className="placement-optimizer-content">
        {/* Items Panel */}
        <div className="placement-items-panel">
          <h3>📦 Items to Place ({items.length})</h3>
          <div className="items-list">
            {items.map((item, index) => (
              <div
                key={`${typeof item === 'string' ? item : item.id}-${index}`}
                className={`item-card ${selectedItem === item ? 'selected' : ''}`}
                onClick={() => handleItemSelect(item)}
              >
                <div className="item-display">
                  {getItemDisplay(item)}
                </div>
                <div className="item-meta">
                  <span className="item-type">
                    {typeof item === 'string' ? 'Text' : 'Card/Number'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations Panel */}
        <div className="placement-recommendations-panel">
          <div className="recommendations-header">
            <h3>🎯 Placement Recommendations ({recommendations.length})</h3>
            <button
              className="btn-refresh"
              onClick={handleOptimize}
              disabled={isLoading}
            >
              {isLoading ? '⏳ Optimizing...' : '🔄 Refresh'}
            </button>
          </div>

          {isLoading && (
            <div className="optimizing-indicator">
              <div className="spinner"></div>
              <p>Analyzing items and rooms...</p>
            </div>
          )}

          <div className="recommendations-list">
            {recommendations.map((rec, index) => {
              const item = items.find(i =>
                typeof i === 'string' ? i === rec.itemId : i.id === rec.itemId
              );

              return (
                <div key={`${rec.itemId}-${index}`} className="recommendation-card">
                  <div className="recommendation-header">
                    <span className="recommendation-item">
                      {item ? getItemDisplay(item) : rec.itemId}
                    </span>
                    <span
                      className="recommendation-confidence"
                      style={{
                        backgroundColor: getConfidenceColor(rec.confidence),
                        color: rec.confidence >= 0.8 ? '#fff' : '#000',
                      }}
                    >
                      {getConfidenceLabel(rec.confidence)} ({(rec.confidence * 100).toFixed(0)}%)
                    </span>
                  </div>

                  <div className="recommendation-details">
                    <div className="room-info">
                      <span className="room-name">{rec.roomName}</span>
                      <span className="location-name">Location {rec.locationIndex + 1}</span>
                    </div>

                    <div className="recommendation-reasoning">
                      <span className="reasoning-label">💡 Why this works:</span>
                      <p className="reasoning-text">{rec.reasoning}</p>
                    </div>

                    {selectedItem === item && (
                      <div className="place-action">
                        <button
                          className="btn-place"
                          onClick={() => handlePlaceItem(rec.itemId, rec.roomId, rec.locationIndex)}
                        >
                          ✅ Place Here
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Item Details */}
        {selectedItem && (
          <div className="selected-item-details">
            <h3>📋 Selected Item Details</h3>
            <div className="item-details-content">
              <div className="detail-row">
                <strong>Item:</strong>
                <span>{getItemDisplay(selectedItem)}</span>
              </div>
              <div className="detail-row">
                <strong>Type:</strong>
                <span>{typeof selectedItem === 'string' ? 'Text' : 'Card/Number'}</span>
              </div>
              <div className="detail-row">
                <strong>Best Rooms:</strong>
                <span>
                  {recommendations
                    .filter(r => r.itemId === (typeof selectedItem === 'string' ? selectedItem : selectedItem.id))
                    .slice(0, 3)
                    .map(r => r.roomName)
                    .join(', ') || 'None'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Exclusion List */}
        {excludeLocations.length > 0 && (
          <div className="exclusion-list">
            <h3>🚫 Excluded Locations ({excludeLocations.length})</h3>
            <div className="exclusions">
              {excludeLocations.map((excl, index) => (
                <div key={index} className="exclusion-item">
                  <span>Location {index + 1}</span>
                  <button onClick={handleClearExclusions}>Clear All</button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlacementOptimizer;
