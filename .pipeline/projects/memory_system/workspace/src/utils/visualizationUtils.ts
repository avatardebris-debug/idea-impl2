/**
 * Utility functions for visualization modes
 */

import { MemoryPalaceItemUnion, Relationship, GraphNode, GraphEdge, MemoryPalaceItemType } from '../types/memoryPalace';

/**
 * Build graph data from items and relationships
 */
export const buildGraphData = (
  items: MemoryPalaceItemUnion[],
  relationships: Relationship[]
): { nodes: GraphNode[]; edges: GraphEdge[] } => {
  const nodeMap = new Map<string, GraphNode>();
  const edgeMap = new Map<string, GraphEdge>();

  // Create nodes from items
  items.forEach((item) => {
    nodeMap.set(item.id, {
      id: item.id,
      label: item.metadata.description || item.value.toString(),
      type: item.type,
      color: getNodeColor(item.type),
      radius: getNodeRadius(item.type),
    });
  });

  // Create edges from relationships
  relationships.forEach((rel) => {
    edgeMap.set(rel.id, {
      id: rel.id,
      source: rel.sourceItemId,
      target: rel.targetItemId,
      type: rel.type,
      label: rel.label,
      strength: rel.strength || 1,
    });
  });

  return {
    nodes: Array.from(nodeMap.values()),
    edges: Array.from(edgeMap.values()),
  };
};

/**
 * Compute layout for network graph using force-directed simulation
 */
export const computeLayout = (
  nodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number,
  repulsion: number
): { x: number; y: number }[] => {
  const positions = nodes.map((node, index) => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: 0,
    vy: 0,
  }));

  const iterations = 100;
  const stiffness = 0.01;
  const damping = 0.9;

  for (let iter = 0; iter < iterations; iter++) {
    // Apply repulsion between nodes
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = positions[i].x - positions[j].x;
        const dy = positions[i].y - positions[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = repulsion / (dist * dist);
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        positions[i].vx += fx;
        positions[i].vy += fy;
        positions[j].vx -= fx;
        positions[j].vy -= fy;
      }
    }

    // Apply attraction along edges
    edges.forEach((edge) => {
      const sourceIndex = nodes.findIndex((n) => n.id === edge.source);
      const targetIndex = nodes.findIndex((n) => n.id === edge.target);
      if (sourceIndex === -1 || targetIndex === -1) return;

      const dx = positions[targetIndex].x - positions[sourceIndex].x;
      const dy = positions[targetIndex].y - positions[sourceIndex].y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (dist - 100) * stiffness;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      positions[sourceIndex].vx += fx;
      positions[sourceIndex].vy += fy;
      positions[targetIndex].vx -= fx;
      positions[targetIndex].vy -= fy;
    });

    // Update positions
    positions.forEach((pos) => {
      pos.vx *= damping;
      pos.vy *= damping;
      pos.x += pos.vx;
      pos.y += pos.vy;

      // Keep within bounds
      pos.x = Math.max(50, Math.min(width - 50, pos.x));
      pos.y = Math.max(50, Math.min(height - 50, pos.y));
    });
  }

  return positions.map((pos) => ({ x: pos.x, y: pos.y }));
};

/**
 * Get node color based on item type
 */
export const getNodeColor = (type: MemoryPalaceItemType): string => {
  const colors: Record<MemoryPalaceItemType, string> = {
    word: '#4CAF50',
    phrase: '#2196F3',
    image: '#9C27B0',
    date: '#FF9800',
    card: '#E91E63',
    number: '#00BCD4',
  };
  return colors[type] || '#607D8B';
};

/**
 * Get node radius based on item type
 */
export const getNodeRadius = (type: MemoryPalaceItemType): number => {
  const radii: Record<MemoryPalaceItemType, number> = {
    word: 30,
    phrase: 35,
    image: 40,
    date: 35,
    card: 25,
    number: 25,
  };
  return radii[type] || 30;
};

/**
 * Get node icon based on item type
 */
export const getNodeIcon = (type: MemoryPalaceItemType): string => {
  const icons: Record<MemoryPalaceItemType, string> = {
    word: '📝',
    phrase: '💬',
    image: '🖼️',
    date: '📅',
    card: '🎴',
    number: '🔢',
  };
  return icons[type] || '📌';
};

/**
 * Get relationship type color
 */
export const getRelationshipColor = (type: string): string => {
  const colors: Record<string, string> = {
    related: '#9C27B0',
    linked: '#2196F3',
    associated: '#4CAF50',
    default: '#9E9E9E',
  };
  return colors[type] || colors.default;
};
