import { GraphNode, GraphEdge, MemoryPalaceItemUnion, Relationship } from '../types/memoryPalace';

/**
 * Extract nodes and edges from memory palace items and relationships
 */
export function buildGraphData(
  items: MemoryPalaceItemUnion[],
  relationships: Relationship[]
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodeMap = new Map<string, GraphNode>();
  const edgeMap = new Map<string, GraphEdge>();

  // Create nodes from items
  items.forEach((item) => {
    nodeMap.set(item.id, {
      id: item.id,
      label: item.metadata.title || item.type,
      type: item.type,
      color: getNodeColor(item.type),
      connections: [],
    });
  });

  // Create edges from relationships
  relationships.forEach((rel) => {
    const sourceNode = nodeMap.get(rel.sourceItemId);
    const targetNode = nodeMap.get(rel.targetItemId);

    if (sourceNode && targetNode) {
      // Create edge with unique key using a delimiter that won't appear in relationship types
      const edgeKey = `${rel.sourceItemId}__EDGE__${rel.targetItemId}__TYPE__${rel.relationshipType}`;
      
      if (!edgeMap.has(edgeKey)) {
        edgeMap.set(edgeKey, {
          id: rel.id,
          source: rel.sourceItemId,
          target: rel.targetItemId,
          type: rel.type,
          label: rel.label,
          strength: rel.strength,
          relationshipType: rel.relationshipType,
        });

        // Update connections for both nodes
        if (sourceNode.connections) {
          sourceNode.connections.push(rel.targetItemId);
        } else {
          sourceNode.connections = [rel.targetItemId];
        }

        if (targetNode.connections) {
          targetNode.connections.push(rel.sourceItemId);
        } else {
          targetNode.connections = [rel.sourceItemId];
        }
      }
    }
  });

  const nodes = Array.from(nodeMap.values());
  const edges = Array.from(edgeMap.values());

  return { nodes, edges };
}

/**
 * Compute force-directed layout positions
 */
export function computeLayout(
  nodes: GraphNode[],
  edges: GraphEdge[],
  width: number,
  height: number,
  iterations: number = 100
): { x: number; y: number }[] {
  const nodePositions = new Map<string, { x: number; y: number }>();
  const nodeVelocities = new Map<string, { vx: number; vy: number }>();

  // Initialize positions randomly within bounds
  nodes.forEach((node) => {
    nodePositions.set(node.id, {
      x: Math.random() * width,
      y: Math.random() * height,
    });
    nodeVelocities.set(node.id, { vx: 0, vy: 0 });
  });

  const k = Math.sqrt((width * height) / nodes.length);
  const gravity = 0.5;
  const repulsion = 1000;
  const springLength = k;
  const damping = 0.9;

  for (let iter = 0; iter < iterations; iter++) {
    // Repulsion forces between all nodes
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const nodeA = nodes[i];
        const nodeB = nodes[j];
        const posA = nodePositions.get(nodeA.id)!;
        const posB = nodePositions.get(nodeB.id)!;

        const dx = posB.x - posA.x;
        const dy = posB.y - posA.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = repulsion / (dist * dist);

        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        const velA = nodeVelocities.get(nodeA.id)!;
        const velB = nodeVelocities.get(nodeB.id)!;

        velA.vx -= fx;
        velA.vy -= fy;
        velB.vx += fx;
        velB.vy += fy;
      }
    }

    // Spring forces between connected nodes
    edges.forEach((edge) => {
      const sourcePos = nodePositions.get(edge.source);
      const targetPos = nodePositions.get(edge.target);

      if (sourcePos && targetPos) {
        const dx = targetPos.x - sourcePos.x;
        const dy = targetPos.y - sourcePos.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - springLength) * 0.05;

        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        const sourceVel = nodeVelocities.get(edge.source)!;
        const targetVel = nodeVelocities.get(edge.target)!;

        sourceVel.vx += fx;
        sourceVel.vy += fy;
        targetVel.vx -= fx;
        targetVel.vy -= fy;
      }
    });

    // Center gravity
    nodes.forEach((node) => {
      const pos = nodePositions.get(node.id)!;
      const vel = nodeVelocities.get(node.id)!;

      vel.vx += (width / 2 - pos.x) * gravity;
      vel.vy += (height / 2 - pos.y) * gravity;
    });

    // Update positions
    nodes.forEach((node) => {
      const pos = nodePositions.get(node.id)!;
      const vel = nodeVelocities.get(node.id)!;

      vel.vx *= damping;
      vel.vy *= damping;

      pos.x += vel.vx;
      pos.y += vel.vy;

      // Boundary constraints
      pos.x = Math.max(20, Math.min(width - 20, pos.x));
      pos.y = Math.max(20, Math.min(height - 20, pos.y));
    });
  }

  return Array.from(nodePositions.values());
}

/**
 * Get color for node based on type
 */
export function getNodeColor(type: string): string {
  const colors: Record<string, string> = {
    word: '#4CAF50',
    phrase: '#2196F3',
    image: '#9C27B0',
    date: '#FF9800',
    task: '#f44336',
    note: '#607D8B',
  };
  return colors[type] || '#666666';
}

/**
 * Get icon for node based on type
 */
export function getNodeIcon(type: string): string {
  const icons: Record<string, string> = {
    word: '📝',
    phrase: '💬',
    image: '🖼️',
    date: '📅',
    task: '✅',
    note: '📌',
  };
  return icons[type] || '🔗';
}
