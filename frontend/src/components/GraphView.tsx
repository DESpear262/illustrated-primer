/**
 * Graph view component for AI Tutor application.
 * 
 * Displays knowledge tree graph using Cytoscape.js with ELK layout.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import cytoscape, { Core, NodeSingular, EdgeSingular } from 'cytoscape';
import { GraphData, GraphNode, GraphEdge, HoverPayload } from '../lib/api';
import { HoverCard } from './HoverCard';

// Try to register ELK layout extension
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const elk = require('cytoscape-elk');
  if (elk && typeof elk.default === 'function') {
    cytoscape.use(elk.default);
  } else if (elk && typeof elk === 'function') {
    cytoscape.use(elk);
  }
} catch (error) {
  console.warn('ELK layout not available, using fallback layout');
}

/**
 * Graph view component props.
 */
interface GraphViewProps {
  data: GraphData;
  onNodeClick?: (nodeId: string) => void;
  onHover?: (nodeId: string) => Promise<HoverPayload | null>;
  searchQuery?: string;
  collapsedNodes?: Set<string>;
  onToggleCollapse?: (nodeId: string) => void;
  onZoomChange?: (zoom: number) => void;
  controlsRef?: React.MutableRefObject<GraphViewControls | null>;
}

/**
 * Graph view component.
 */
export function GraphView({
  data,
  onNodeClick,
  onHover,
  searchQuery = '',
  collapsedNodes = new Set(),
  onToggleCollapse,
  onZoomChange,
  controlsRef: externalControlsRef,
}: GraphViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [hoverPayload, setHoverPayload] = useState<HoverPayload | null>(null);
  const [hoverPosition, setHoverPosition] = useState<{ x: number; y: number } | null>(null);
  const [hoverNodeId, setHoverNodeId] = useState<string | null>(null);
  const hoverTimeoutRef = useRef<number | null>(null);

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements: data,
      style: [
        {
          selector: 'node[type="topic"]',
          style: {
            'background-color': '#3B82F6',
            'label': 'data(label)',
            'width': 60,
            'height': 60,
            'shape': 'round-rectangle',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#ffffff',
            'font-size': '12px',
            'font-weight': 'bold',
            'border-width': 2,
            'border-color': '#1E40AF',
          },
        },
        {
          selector: 'node[type="skill"]',
          style: {
            'background-color': (node: NodeSingular) => {
              const mastery = node.data('mastery') || 0;
              // Color intensity based on mastery (0.0 = light green, 1.0 = dark green)
              const intensity = Math.floor(mastery * 100);
              return `hsl(142, 70%, ${70 - intensity * 0.3}%)`;
            },
            'label': 'data(label)',
            'width': 50,
            'height': 50,
            'shape': 'ellipse',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#ffffff',
            'font-size': '11px',
            'font-weight': 'bold',
            'border-width': 2,
            'border-color': '#059669',
          },
        },
        {
          selector: 'node[type="event"]',
          style: {
            'background-color': '#6B7280',
            'label': 'data(label)',
            'width': 40,
            'height': 40,
            'shape': 'diamond',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#ffffff',
            'font-size': '10px',
            'border-width': 1,
            'border-color': '#4B5563',
          },
        },
        {
          selector: 'edge[type="parent-child"]',
          style: {
            'width': 2,
            'line-color': '#3B82F6',
            'target-arrow-color': '#3B82F6',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
          },
        },
        {
          selector: 'edge[type="belongs-to"]',
          style: {
            'width': 2,
            'line-color': '#10B981',
            'line-style': 'dashed',
            'target-arrow-color': '#10B981',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
          },
        },
        {
          selector: 'edge[type="evidence"]',
          style: {
            'width': 1,
            'line-color': '#6B7280',
            'line-style': 'dotted',
            'target-arrow-color': '#6B7280',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#F59E0B',
          },
        },
        {
          selector: 'node.highlight',
          style: {
            'border-width': 3,
            'border-color': '#EF4444',
          },
        },
      ],
      layout: {
        name: 'breadthfirst',
        directed: true,
        roots: undefined, // Will be determined automatically
        spacingFactor: 1.5,
        padding: 50,
      },
      minZoom: 0.1,
      maxZoom: 2,
    });

    cyRef.current = cy;

    // Node click handler
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeId = node.id();
      if (onNodeClick) {
        onNodeClick(nodeId);
      }
    });

    // Node hover handler
    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target;
      const nodeId = node.id();
      
      // Clear existing timeout
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }

      // Set hover position (relative to viewport)
      const position = node.renderedPosition();
      const containerRect = containerRef.current?.getBoundingClientRect();
      if (containerRect) {
        setHoverPosition({
          x: containerRect.left + position.x,
          y: containerRect.top + position.y,
        });
      }
      setHoverNodeId(nodeId);

      // Fetch hover payload with delay (debounced to avoid excessive requests)
      hoverTimeoutRef.current = window.setTimeout(async () => {
        if (onHover && hoverNodeId === nodeId) {
          try {
            const payload = await onHover(nodeId);
            // Only set payload if still hovering over the same node
            if (hoverNodeId === nodeId) {
              setHoverPayload(payload);
            }
          } catch (error) {
            console.error('Failed to fetch hover payload:', error);
          }
        }
      }, 200);
    });

    cy.on('mouseout', 'node', () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
        hoverTimeoutRef.current = null;
      }
      setHoverPayload(null);
      setHoverPosition(null);
      setHoverNodeId(null);
    });

    // Fit to screen on initial load
    cy.fit(undefined, 50);

    // Track zoom changes
    cy.on('zoom', () => {
      if (onZoomChange) {
        onZoomChange(cy.zoom());
      }
    });

    // Expose zoom controls via ref
    if (onZoomChange) {
      onZoomChange(cy.zoom());
    }

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [data, onNodeClick, onHover, onZoomChange]);

  // Zoom controls
  const zoomIn = useCallback(() => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2);
    }
  }, []);

  const zoomOut = useCallback(() => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() / 1.2);
    }
  }, []);

  const fit = useCallback(() => {
    if (cyRef.current) {
      cyRef.current.fit(undefined, 50);
    }
  }, []);

  const reset = useCallback(() => {
    if (cyRef.current) {
      cyRef.current.reset();
      cyRef.current.fit(undefined, 50);
    }
  }, []);

  // Handle search query filtering
  useEffect(() => {
    if (!cyRef.current) return;

    const cy = cyRef.current;
    
    if (searchQuery.trim()) {
      // Filter nodes by label
      cy.nodes().forEach((node) => {
        const label = node.data('label') || '';
        const matches = label.toLowerCase().includes(searchQuery.toLowerCase());
        if (matches) {
          node.addClass('highlight');
        } else {
          node.removeClass('highlight');
        }
      });
    } else {
      // Remove all highlights
      cy.nodes().removeClass('highlight');
    }
  }, [searchQuery]);

  // Handle collapsed nodes
  useEffect(() => {
    if (!cyRef.current || !onToggleCollapse) return;

    const cy = cyRef.current;
    
    // Hide edges to collapsed nodes
    cy.edges().forEach((edge) => {
      const source = edge.source();
      const target = edge.target();
      
      if (collapsedNodes.has(source.id()) || collapsedNodes.has(target.id())) {
        edge.hide();
      } else {
        edge.show();
      }
    });

    // Hide collapsed nodes and their descendants
    cy.nodes().forEach((node) => {
      if (collapsedNodes.has(node.id())) {
        // Hide node and its outgoing edges
        node.hide();
        node.outgoers().hide();
      } else {
        node.show();
      }
    });
  }, [collapsedNodes, onToggleCollapse]);

  // Expose zoom controls via ref
  const internalControlsRef = useRef<GraphViewControls | null>(null);
  
  // Update controls ref whenever zoom functions change
  useEffect(() => {
    internalControlsRef.current = {
      zoomIn,
      zoomOut,
      fit,
      reset,
    };
    
    // Expose controls to parent via external ref
    if (externalControlsRef) {
      externalControlsRef.current = internalControlsRef.current;
    }
  }, [zoomIn, zoomOut, fit, reset, externalControlsRef]);

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />
      {hoverPayload && hoverPosition && (
        <HoverCard
          payload={hoverPayload}
          x={hoverPosition.x}
          y={hoverPosition.y}
          onClose={() => {
            setHoverPayload(null);
            setHoverPosition(null);
            setHoverNodeId(null);
          }}
        />
      )}
    </div>
  );
}

/**
 * Graph view controls interface.
 */
export interface GraphViewControls {
  zoomIn: () => void;
  zoomOut: () => void;
  fit: () => void;
  reset: () => void;
}

