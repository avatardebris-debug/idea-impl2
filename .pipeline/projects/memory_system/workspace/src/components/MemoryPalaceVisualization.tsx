import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Palace, Room } from '../types/palace';
import { useMemoryPalace } from '../hooks/useMemoryPalace';
import { useVisualization } from '../hooks/useVisualization';
import { useNetworkGraph } from '../hooks/useNetworkGraph';
import { NetworkGraphVisualization } from './VisualizationModes/NetworkGraphVisualization';
import './MemoryPalaceVisualization.css';

export interface VisualizationConfig {
  showLabels: boolean;
  showConnections: boolean;
  animationSpeed: 'slow' | 'medium' | 'fast';
  highlightActive: boolean;
  zoomLevel: number;
}

export interface VisualizationState {
  activeRoomId: string | null;
  hoveredRoomId: string | null;
  isAnimating: boolean;
  viewMode: 'grid' | 'list' | 'tree';
}

export interface VisualizationProps {
  palace: Palace;
  config?: VisualizationConfig;
  onRoomSelect?: (roomId: string) => void;
  onRoomHover?: (roomId: string | null) => void;
}

const DEFAULT_CONFIG: VisualizationConfig = {
  showLabels: true,
  showConnections: true,
  animationSpeed: 'medium',
  highlightActive: true,
  zoomLevel: 1,
};

const DEFAULT_STATE: VisualizationState = {
  activeRoomId: null,
  hoveredRoomId: null,
  isAnimating: false,
  viewMode: 'grid',
};

/**
 * Calculate room position in grid layout
 */
const calculateGridPosition = (index: number, totalRooms: number): { x: number; y: number } => {
  const cols = Math.ceil(Math.sqrt(totalRooms));
  const x = index % cols;
  const y = Math.floor(index / cols);
  return { x, y };
};

/**
 * Calculate room position in list layout
 */
const calculateListPosition = (index: number): { x: number; y: number } => {
  return { x: 0, y: index };
};

/**
 * Calculate room position in tree layout
 */
const calculateTreePosition = (index: number, depth: number): { x: number; y: number } => {
  const x = Math.sin(depth * 0.5) * 200 + 100;
  const y = index * 80 + 50;
  return { x, y };
};

/**
 * Get animation duration based on speed setting
 */
const getAnimationDuration = (speed: VisualizationConfig['animationSpeed']): number => {
  switch (speed) {
    case 'slow':
      return 1000;
    case 'medium':
      return 600;
    case 'fast':
      return 300;
    default:
      return 600;
  }
};

/**
 * MemoryPalaceVisualization Component
 * Visualizes the memory palace structure with interactive rooms
 */
const MemoryPalaceVisualization: React.FC<VisualizationProps> = ({
  palace,
  config = DEFAULT_CONFIG,
  onRoomSelect,
  onRoomHover,
}) => {
  const [state, setState] = useState<VisualizationState>(DEFAULT_STATE);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number | null>(null);

  // Use hooks for memory palace and visualization management
  const { 
    rooms, 
    items, 
    relationships, 
    addRoom, 
    removeRoom, 
    addItem, 
    removeItem, 
    addRelationship, 
    removeRelationship 
  } = useMemoryPalace();

  const { 
    viewMode, 
    showLabels, 
    showConnections, 
    highlightActive, 
    zoomLevel, 
    setViewMode, 
    setShowLabels, 
    setShowConnections, 
    setHighlightActive, 
    setZoomLevel 
  } = useVisualization();

  const { 
    state: { nodes, edges, selectedItemId },
    actions: { setSelectedItem, selectItem, handleRemoveRelationship, handleAddRelationship }
  } = useNetworkGraph(items, relationships);

  const animationDuration = getAnimationDuration(config.animationSpeed);

  // Handle room selection
  const handleRoomSelect = useCallback((roomId: string) => {
    setState(prev => ({
      ...prev,
      activeRoomId: roomId,
    }));
    onRoomSelect?.(roomId);
  }, [onRoomSelect]);

  // Handle room hover
  const handleRoomHover = useCallback((roomId: string | null) => {
    setState(prev => ({
      ...prev,
      hoveredRoomId: roomId,
    }));
    onRoomHover?.(roomId);
  }, [onRoomHover]);

  // Handle view mode change
  const handleViewModeChange = useCallback((mode: VisualizationState['viewMode']) => {
    setState(prev => ({
      ...prev,
      viewMode: mode,
    }));
    setViewMode(mode);
  }, [setViewMode]);

  // Handle zoom
  const handleZoom = useCallback((delta: number) => {
    setState(prev => ({
      ...prev,
      zoomLevel: Math.max(0.5, Math.min(2, prev.zoomLevel + delta)),
    }));
    setZoomLevel(Math.max(0.5, Math.min(2, zoomLevel + delta)));
  }, [zoomLevel, setZoomLevel]);

  // Animate room entrance
  const animateRoomEntrance = useCallback((roomId: string, delay: number) => {
    setState(prev => ({
      ...prev,
      isAnimating: true,
    }));

    animationRef.current = window.setTimeout(() => {
      setState(prev => ({
        ...prev,
        isAnimating: false,
      }));
    }, delay + animationDuration);
  }, [animationDuration]);

  // Cleanup animation on unmount
  useEffect(() => {
    return () => {
      if (animationRef.current) {
        window.clearTimeout(animationRef.current);
      }
    };
  }, []);

  // Get room position based on view mode
  const getRoomPosition = useCallback((index: number): { x: number; y: number } => {
    switch (viewMode) {
      case 'list':
        return calculateListPosition(index);
      case 'tree':
        return calculateTreePosition(index, Math.floor(index / 3));
      case 'grid':
      default:
        return calculateGridPosition(index, rooms.length);
    }
  }, [rooms.length, viewMode]);

  // Render a single room card
  const renderRoomCard = (room: Room, index: number) => {
    const position = getRoomPosition(index);
    const isActive = state.activeRoomId === room.id;
    const isHovered = state.hoveredRoomId === room.id;
    const isEmpty = room.items.length === 0;

    return (
      <div
        key={room.id}
        className={`memory-palace-room ${isActive ? 'active' : ''} ${isHovered ? 'hovered' : ''} ${isEmpty ? 'empty' : ''}`}
        style={{
          transform: `translate(${position.x}px, ${position.y}px) scale(${zoomLevel})`,
          animationDelay: `${index * 100}ms`,
        }}
        onClick={() => handleRoomSelect(room.id)}
        onMouseEnter={() => handleRoomHover(room.id)}
        onMouseLeave={() => handleRoomHover(null)}
      >
        {/* Room label */}
        {showLabels && (
          <div className="memory-palace-room-label">
            {room.name}
          </div>
        )}

        {/* Room items */}
        <div className="memory-palace-room-items">
          {room.items.map((item, itemIndex) => (
            <div
              key={itemIndex}
              className="memory-palace-item"
              style={{
                animationDelay: `${index * 100 + itemIndex * 50}ms`,
              }}
            >
              {item}
            </div>
          ))}
        </div>

        {/* Room status indicator */}
        <div className="memory-palace-room-status">
          <div className={`status-dot ${isActive ? 'active' : ''} ${isEmpty ? 'empty' : 'filled'}`}></div>
          <span className="item-count">{room.items.length} items</span>
        </div>
      </div>
    );
  };

  // Render connections between rooms
  const renderConnections = () => {
    if (!showConnections || rooms.length < 2) {
      return null;
    }

    const connections = [];
    for (let i = 0; i < rooms.length - 1; i++) {
      const startPos = getRoomPosition(i);
      const endPos = getRoomPosition(i + 1);
      
      connections.push(
        <line
          key={`connection-${i}`}
          x1={startPos.x + 50}
          y1={startPos.y + 50}
          x2={endPos.x + 50}
          y2={endPos.y + 50}
          className="memory-palace-connection"
          style={{
            opacity: state.hoveredRoomId === rooms[i].id || state.hoveredRoomId === rooms[i + 1].id ? 1 : 0.3,
          }}
        />
      );
    }

    return (
      <svg className="memory-palace-connections" style={{ transform: `scale(${zoomLevel})` }}>
        {connections}
      </svg>
    );
  };

  // Render view mode controls
  const renderViewControls = () => (
    <div className="memory-palace-view-controls">
      <button
        className={`view-mode-btn ${viewMode === 'grid' ? 'active' : ''}`}
        onClick={() => handleViewModeChange('grid')}
        title="Grid View"
      >
        📊 Grid
      </button>
      <button
        className={`view-mode-btn ${viewMode === 'list' ? 'active' : ''}`}
        onClick={() => handleViewModeChange('list')}
        title="List View"
      >
        📋 List
      </button>
      <button
        className={`view-mode-btn ${viewMode === 'tree' ? 'active' : ''}`}
        onClick={() => handleViewModeChange('tree')}
        title="Tree View"
      >
        🌳 Tree
      </button>
    </div>
  );

  // Render zoom controls
  const renderZoomControls = () => (
    <div className="memory-palace-zoom-controls">
      <button
        className="zoom-btn"
        onClick={() => handleZoom(-0.1)}
        title="Zoom Out"
      >
        -
      </button>
      <span className="zoom-level">{Math.round(zoomLevel * 100)}%</span>
      <button
        className="zoom-btn"
        onClick={() => handleZoom(0.1)}
        title="Zoom In"
      >
        +
      </button>
    </div>
  );

  // Render room statistics
  const renderStatistics = () => {
    const totalItems = rooms.reduce((sum, room) => sum + room.items.length, 0);
    const activeRooms = rooms.filter(room => room.id === state.activeRoomId).length;

    return (
      <div className="memory-palace-stats">
        <div className="stat-item">
          <span className="stat-value">{rooms.length}</span>
          <span className="stat-label">Rooms</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{totalItems}</span>
          <span className="stat-label">Items</span>
        </div>
        <div className="stat-item">
          <span className="stat-value">{activeRooms}</span>
          <span className="stat-label">Active</span>
        </div>
      </div>
    );
  };

  return (
    <div className="memory-palace-visualization" ref={containerRef}>
      {/* Header */}
      <div className="memory-palace-header">
        <h2>🏰 Memory Palace Visualization</h2>
        <div className="memory-palace-header-actions">
          {renderViewControls()}
          {renderZoomControls()}
        </div>
      </div>

      {/* Main Visualization Area */}
      <div className="memory-palace-visualization-area">
        {/* Background grid */}
        <div className="memory-palace-grid">
          <div className="grid-line horizontal"></div>
          <div className="grid-line vertical"></div>
        </div>

        {/* Connections layer */}
        {renderConnections()}

        {/* Rooms layer */}
        <div className="memory-palace-rooms">
          {rooms.length === 0 ? (
            <div className="memory-palace-empty">
              <div className="memory-palace-empty-icon">🏰</div>
              <p>No rooms in your memory palace yet.</p>
              <p className="memory-palace-empty-hint">Add rooms to start building your memory palace!</p>
            </div>
          ) : (
            rooms.map((room, index) => renderRoomCard(room, index))
          )}
        </div>

        {/* Statistics */}
        {renderStatistics()}
      </div>

      {/* Legend */}
      <div className="memory-palace-legend">
        <div className="legend-item">
          <div className="legend-dot active"></div>
          <span>Active Room</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot hovered"></div>
          <span>Hovered Room</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot filled"></div>
          <span>Has Items</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot empty"></div>
          <span>Empty Room</span>
        </div>
      </div>

      {/* Network Graph Visualization */}
      <NetworkGraphVisualization
        items={items}
        relationships={relationships}
        selectedItemId={selectedItemId}
        onItemSelect={selectItem}
      />
    </div>
  );
};

export default MemoryPalaceVisualization;
