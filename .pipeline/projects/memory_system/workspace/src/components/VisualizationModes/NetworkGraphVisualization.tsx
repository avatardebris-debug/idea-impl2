import React, { useState, useCallback, useMemo } from 'react';
import {
  MemoryPalaceItemUnion,
  Relationship,
  VisualizationMode,
  GraphNode,
  GraphEdge,
} from '../../../types/memoryPalace';
import { buildGraphData } from './visualizationUtils';
import './NetworkGraphVisualization.css';

interface NetworkGraphVisualizationProps {
  items: MemoryPalaceItemUnion[];
  relationships: Relationship[];
  selectedItemId?: string | null;
  onItemSelect?: (item: MemoryPalaceItemUnion) => void;
  onRelationshipRemove?: (edgeId: string) => void;
  onRelationshipAdd?: (sourceId: string, targetId: string) => void;
}

export const NetworkGraphVisualization: React.FC<NetworkGraphVisualizationProps> = ({
  items,
  relationships,
  selectedItemId,
  onItemSelect,
}) => {
  const [nodePositions, setNodePositions] = useState<Record<string, { x: number; y: number }>>({});
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Build graph data from items and relationships
  const { nodes, edges } = useMemo(() => {
    return buildGraphData(items, relationships);
  }, [items, relationships]);

  // Initialize node positions on first render
  React.useEffect(() => {
    if (Object.keys(nodePositions).length === 0 && nodes.length > 0) {
      const initialPositions: Record<string, { x: number; y: number }> = {};
      const centerX = 400;
      const centerY = 300;
      const radius = 200;
      const angleStep = (2 * Math.PI) / nodes.length;

      nodes.forEach((node, index) => {
        const angle = index * angleStep;
        initialPositions[node.id] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
        };
      });

      setNodePositions(initialPositions);
    }
  }, [nodes]);

  const handleNodeMouseDown = useCallback((
    e: React.MouseEvent,
    nodeId: string,
    node: GraphNode
  ) => {
    e.stopPropagation();
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setDraggingNodeId(nodeId);
    setDragOffset({ x, y });

    if (onItemSelect) {
      const item = items.find((i) => i.id === nodeId);
      if (item) {
        onItemSelect(item);
      }
    }
  }, [items, onItemSelect]);

  const handleNodeMouseMove = useCallback((e: React.MouseEvent) => {
    if (!draggingNodeId) return;

    const rect = e.currentTarget.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left - dragOffset.x;
    const y = e.clientY - rect.top - dragOffset.y;

    setNodePositions((prev) => ({
      ...prev,
      [draggingNodeId]: { x, y },
    }));
  }, [draggingNodeId, dragOffset]);

  const handleNodeMouseUp = useCallback(() => {
    setDraggingNodeId(null);
    setDragOffset({ x: 0, y: 0 });
  }, []);

  const handleNodeMouseLeave = useCallback(() => {
    setDraggingNodeId(null);
    setDragOffset({ x: 0, y: 0 });
  }, []);

  const handleCanvasClick = useCallback(() => {
    // Deselect when clicking on empty canvas
    if (onItemSelect) {
      onItemSelect(null as any);
    }
  }, [onItemSelect]);

  const getNodeStyle = useCallback((node: GraphNode) => {
    const position = nodePositions[node.id] || { x: 0, y: 0 };
    const isSelected = selectedItemId === node.id;

    return {
      left: position.x,
      top: position.y,
      transform: 'translate(-50%, -50%)',
      opacity: draggingNodeId === node.id ? 0.7 : 1,
      cursor: draggingNodeId ? 'grabbing' : 'grab',
      zIndex: draggingNodeId === node.id ? 1000 : 1,
    };
  }, [nodePositions, selectedItemId, draggingNodeId]);

  const getEdgeStyle = useCallback((edge: GraphEdge) => {
    const sourcePos = nodePositions[edge.source] || { x: 0, y: 0 };
    const targetPos = nodePositions[edge.target] || { x: 0, y: 0 };

    const startX = sourcePos.x;
    const startY = sourcePos.y;
    const endX = targetPos.x;
    const endY = targetPos.y;

    // Calculate control points for curved edge
    const midX = (startX + endX) / 2;
    const midY = (startY + endY) / 2;
    const dx = endX - startX;
    const dy = endY - startY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const offset = Math.min(dist * 0.3, 100);

    // Perpendicular offset for curve
    const curveOffsetX = -dy / dist * offset;
    const curveOffsetY = dx / dist * offset;

    const pathData = `M ${startX} ${startY} Q ${midX + curveOffsetX} ${midY + curveOffsetY} ${endX} ${endY}`;

    // Determine edge style based on strength or type
    let strokeWidth = 2;
    let strokeDasharray = 'none';
    let strokeColor = '#2196F3'; // Default medium
    
    if (edge.strength !== undefined) {
      if (edge.strength >= 0.7) {
        strokeWidth = 3;
        strokeColor = '#4CAF50'; // Strong - green
      } else if (edge.strength >= 0.4) {
        strokeWidth = 2;
        strokeColor = '#2196F3'; // Medium - blue
      } else if (edge.strength < 0.4) {
        strokeWidth = 1;
        strokeDasharray = '5,5';
        strokeColor = '#9E9E9E'; // Weak - gray
      }
    } else if (edge.type) {
      if (edge.type === 'strong') {
        strokeWidth = 3;
        strokeColor = '#4CAF50';
      } else if (edge.type === 'medium') {
        strokeWidth = 2;
        strokeColor = '#2196F3';
      } else if (edge.type === 'weak') {
        strokeWidth = 1;
        strokeDasharray = '5,5';
        strokeColor = '#9E9E9E';
      }
    }

    return {
      d: pathData,
      strokeWidth,
      strokeDasharray,
      strokeColor,
    };
  }, [nodePositions]);

  return (
    <div className="network-graph-visualization">
      <svg
        className="network-graph-svg"
        onClick={handleCanvasClick}
        onMouseMove={handleNodeMouseMove}
        onMouseUp={handleNodeMouseUp}
        onMouseLeave={handleNodeMouseLeave}
      >
        {/* Edges */}
        <g className="network-graph-edges">
          {edges.map((edge, index) => {
            const style = getEdgeStyle(edge);
            return (
              <path
                key={`edge-${index}`}
                d={style.d}
                stroke={style.strokeColor}
                strokeWidth={style.strokeWidth}
                strokeDasharray={style.strokeDasharray}
                fill="none"
                className="network-graph-edge"
              />
            );
          })}
        </g>

        {/* Nodes */}
        <g className="network-graph-nodes">
          {nodes.map((node, index) => {
            const style = getNodeStyle(node);
            const isSelected = selectedItemId === node.id;

            return (
              <g
                key={`node-${index}`}
                className="network-graph-node-group"
                onMouseDown={(e) => handleNodeMouseDown(e, node.id, node)}
                style={style}
              >
                {/* Node circle */}
                <circle
                  r={20}
                  fill={node.color}
                  stroke={isSelected ? '#FF9800' : '#fff'}
                  strokeWidth={isSelected ? 3 : 2}
                  className="network-graph-node-circle"
                />

                {/* Node label */}
                <text
                  y={30}
                  textAnchor="middle"
                  fill="#333"
                  fontSize="12"
                  className="network-graph-node-label"
                >
                  {node.label}
                </text>

                {/* Connection count badge */}
                {node.connections && node.connections.length > 0 && (
                  <circle
                    cx={35}
                    cy={-10}
                    r={12}
                    fill="#FF9800"
                    stroke="#fff"
                    strokeWidth={2}
                    className="network-graph-connection-badge"
                  >
                    <text
                      x={35}
                      y={-6}
                      textAnchor="middle"
                      fill="#fff"
                      fontSize="10"
                      fontWeight="bold"
                    >
                      {node.connections.length}
                    </text>
                  </circle>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      <div className="network-graph-legend">
        <div className="legend-item">
          <span className="legend-dot" style={{ backgroundColor: '#4CAF50' }}></span>
          <span>Strong (≥0.7)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ backgroundColor: '#2196F3' }}></span>
          <span>Medium (0.4-0.7)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ backgroundColor: '#9E9E9E' }}></span>
          <span>Weak (≤0.4)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ backgroundColor: '#FF9800' }}></span>
          <span>Selected Node</span>
        </div>
      </div>
    </div>
  );
};

export default NetworkGraphVisualization;
