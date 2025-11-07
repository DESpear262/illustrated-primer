/**
 * Graph view component for AI Tutor application.
 * 
 * Displays knowledge tree graph using Cytoscape.js with ELK layout.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import cytoscape from 'cytoscape';
import type { Core, NodeSingular } from 'cytoscape';
import type { GraphData, HoverPayload } from '../lib/api';
import { HoverCard } from './HoverCard';

// Try to register ELK layout extension
(async () => {
  try {
    const elk = await import('cytoscape-elk');
    if (elk && typeof elk.default === 'function') {
      cytoscape.use(elk.default);
    } else if (elk && typeof elk === 'function') {
      cytoscape.use(elk);
    }
  } catch (error) {
    console.warn('ELK layout not available, using fallback layout');
  }
})();

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
    if (!containerRef.current || !data || !data.nodes) {
      console.warn('GraphView: Missing container or data', { 
        hasContainer: !!containerRef.current, 
        hasData: !!data,
        nodeCount: data?.nodes?.length 
      });
      return;
    }

    // Wait for container to have dimensions
    const checkDimensions = () => {
      if (!containerRef.current) return false;
      const rect = containerRef.current.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    };

    if (!checkDimensions()) {
      // Wait a bit for layout to settle
      const timeoutId = setTimeout(() => {
        if (checkDimensions() && containerRef.current && data && data.nodes) {
          initializeCytoscape();
        }
      }, 100);
      return () => clearTimeout(timeoutId);
    }

    initializeCytoscape();

    function initializeCytoscape() {
      if (!containerRef.current || !data || !data.nodes) return;

      try {
        console.log('Initializing Cytoscape with', data.nodes.length, 'nodes and', data.edges?.length || 0, 'edges');
        
        // Clean up previous instance if it exists
        if (cyRef.current) {
          cyRef.current.destroy();
          cyRef.current = null;
        }
        
        const cy = cytoscape({
          container: containerRef.current,
          elements: {
            nodes: data.nodes,
            edges: data.edges || [],
          },
          style: [
            {
              selector: 'node[type="topic"]',
              style: {
                'shape': 'round-rectangle',
                'background-color': '#F1EAD5',
                'border-color': '#B08D57',
                'border-width': 1.5,
                'label': 'data(label)',
                'font-family': '"Source Serif 4","Georgia",serif',
                'font-size': 14,
                'text-wrap': 'wrap',
                'text-max-width': 120,
                'text-valign': 'center',
                'text-halign': 'center',
                'color': '#111216',
                'width': 60,
                'height': 60,
              },
            },
            {
              selector: 'node[type="skill"]',
              style: {
                'shape': 'ellipse',
                'background-color': '#FFFFFF',
                'border-color': (node: NodeSingular) => {
                  // Mastery ring colors: 0-0.4 = garnet, 0.4-0.7 = brass, 0.7-1.0 = verdigris
                  const mastery = node.data('mastery') || node.data('p_mastery') || 0;
                  if (mastery < 0.4) return '#8F1D2C'; // garnet
                  if (mastery < 0.7) return '#B08D57'; // brass
                  return '#2A8F8A'; // verdigris
                },
                'border-width': (node: NodeSingular) => {
                  const mastery = node.data('mastery') || node.data('p_mastery');
                  return mastery !== undefined ? 3 : 1;
                },
                'label': 'data(label)',
                'font-family': '"Source Serif 4","Georgia",serif',
                'font-size': 11,
                'text-valign': 'center',
                'text-halign': 'center',
                'color': '#111216',
                'width': 50,
                'height': 50,
              },
            },
            {
              selector: 'node[type="artifact"]',
              style: {
                'shape': 'hexagon',
                'background-color': '#E6EAF4',
                'border-color': '#1F2C44',
                'border-width': 1,
                'label': 'data(label)',
                'font-family': '"Source Serif 4","Georgia",serif',
                'font-size': 11,
                'text-valign': 'center',
                'text-halign': 'center',
                'color': '#111216',
                'width': 50,
                'height': 50,
              },
            },
            {
              selector: 'edge[rel="contains"]',
              style: {
                'line-color': '#B08D57',
                'width': 1.5,
                'curve-style': 'bezier',
              },
            },
            {
              selector: 'edge[rel="prereq"]',
              style: {
                'line-color': '#1F2C44',
                'width': 2,
                'line-style': 'dashed',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#1F2C44',
                'curve-style': 'bezier',
              },
            },
            {
              selector: 'edge[rel="applies_in"]',
              style: {
                'line-color': '#2A8F8A',
                'width': 1.5,
                'line-style': 'dotted',
                'curve-style': 'bezier',
              },
            },
            {
              selector: 'edge[type="parent-child"]',
              style: {
                'line-color': '#B08D57',
                'width': 1.5,
                'curve-style': 'bezier',
              },
            },
            {
              selector: 'edge[type="belongs-to"]',
              style: {
                'line-color': '#1F2C44',
                'width': 2,
                'line-style': 'dashed',
                'target-arrow-shape': 'triangle',
                'target-arrow-color': '#1F2C44',
                'curve-style': 'bezier',
              },
            },
            {
              selector: 'edge[type="evidence"]',
              style: {
                'line-color': '#2A8F8A',
                'width': 1.5,
                'line-style': 'dotted',
                'curve-style': 'bezier',
              },
            },
            {
              selector: 'node:selected',
              style: {
                'border-width': 4,
                'border-color': '#2A8F8A',
              },
            },
            {
              selector: 'node.highlight',
              style: {
                'border-width': 3,
                'border-color': '#2A8F8A',
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
        
        // Debug: Log container dimensions
        if (containerRef.current) {
          const rect = containerRef.current.getBoundingClientRect();
          console.log('Container dimensions:', { width: rect.width, height: rect.height });
        }
        
        // Debug: Log after a short delay to see if nodes are added
        setTimeout(() => {
          if (cyRef.current) {
            console.log('Cytoscape nodes:', cyRef.current.nodes().length);
            console.log('Cytoscape edges:', cyRef.current.edges().length);
            console.log('Cytoscape viewport:', cyRef.current.extent());
          }
        }, 1000);

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

        // Wait for layout to complete before fitting
        cy.ready(() => {
          console.log('Cytoscape ready, fitting to viewport');
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
        });

        return () => {
          if (cyRef.current) {
            cyRef.current.destroy();
            cyRef.current = null;
          }
        };
      } catch (error) {
        console.error('Failed to initialize Cytoscape:', error);
        console.error('Error details:', {
          error,
          data: data ? { nodeCount: data.nodes?.length, edgeCount: data.edges?.length } : null,
          hasContainer: !!containerRef.current,
          containerDimensions: containerRef.current ? containerRef.current.getBoundingClientRect() : null,
        });
      }
    }
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
    <div className="relative w-full h-full" style={{ minHeight: '500px' }}>
      <div 
        ref={containerRef} 
        className="w-full h-full" 
        style={{ minHeight: '500px', backgroundColor: '#F8F5EC' }}
      />
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

