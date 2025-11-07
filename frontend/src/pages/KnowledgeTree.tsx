/**
 * Knowledge Tree page for AI Tutor application.
 * 
 * Implements the Knowledge Tree visualization interface with Cytoscape.js,
 * search, collapse, zoom, pan, and navigation to Context page.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../lib/api';
import type { GraphData, HoverPayload } from '../lib/api';
import { GraphView } from '../components/GraphView';
import type { GraphViewControls } from '../components/GraphView';
import { useWebSocket } from '../hooks/useWebSocket';
import toast from 'react-hot-toast';

/**
 * Knowledge Tree page component.
 */
export function KnowledgeTree() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [collapsedNodes, setCollapsedNodes] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState({
    scope: '',
    depth: 1,
    relation: '',
    include_events: false,
  });
  const [nodeCount, setNodeCount] = useState(0);
  const navigate = useNavigate();
  const hoverCacheRef = useRef<Map<string, HoverPayload>>(new Map());
  
  // WebSocket connection for real-time updates
  const { isConnected, messages } = useWebSocket();
  
  // Load graph data
  const loadGraph = useCallback(async () => {
    try {
      setIsLoading(true);
      console.log('Loading graph with filters:', filters);
      const data = await apiClient.getGraph({
        scope: filters.scope || undefined,
        depth: filters.depth || undefined,
        relation: filters.relation || undefined,
        include_events: filters.include_events,
      });
      console.log('Graph data received:', { 
        nodeCount: data.nodes?.length || 0, 
        edgeCount: data.edges?.length || 0 
      });
      
      if (!data || !data.nodes) {
        throw new Error('Invalid graph data received from server');
      }
      
      setGraphData(data);
      setNodeCount(data.nodes.length);
      
      if (data.nodes.length === 0) {
        toast.error('No graph data found. Generate stub data or import transcripts to create topics and skills.', {
          duration: 5000,
        });
      } else {
        toast.success(`Graph loaded with ${data.nodes.length} nodes`);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error('Failed to load graph:', error);
      console.error('Error details:', {
        message: errorMessage,
        filters,
        error
      });
      toast.error(`Failed to load graph: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  // Handle WebSocket updates
  useEffect(() => {
    messages.forEach((message) => {
      if (message.type === 'graph_update') {
        // Refresh graph when updates are received
        loadGraph();
        toast.success('Graph updated');
      }
    });
  }, [messages, loadGraph]);

  // Load graph on mount and when filters change
  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  // Handle node click - navigate to Context page
  const handleNodeClick = useCallback(
    (nodeId: string) => {
      navigate(`/context?node=${encodeURIComponent(nodeId)}`);
    },
    [navigate]
  );

  // Handle hover - fetch hover payload with caching
  const handleHover = useCallback(
    async (nodeId: string): Promise<HoverPayload | null> => {
      // Check cache first
      if (hoverCacheRef.current.has(nodeId)) {
        return hoverCacheRef.current.get(nodeId) || null;
      }

      try {
        const payload = await apiClient.getHover(nodeId);
        // Cache payload
        hoverCacheRef.current.set(nodeId, payload);
        return payload;
      } catch (error) {
        console.error('Failed to fetch hover payload:', error);
        return null;
      }
    },
    []
  );

  // Handle collapse/expand
  const handleToggleCollapse = useCallback((nodeId: string) => {
    setCollapsedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  }, []);

  // Handle expand all
  const handleExpandAll = useCallback(() => {
    setCollapsedNodes(new Set());
  }, []);

  // Handle collapse all
  const handleCollapseAll = useCallback(() => {
    if (!graphData) return;
    const allNodeIds = new Set(graphData.nodes.map((node) => node.data.id));
    setCollapsedNodes(allNodeIds);
  }, [graphData]);

  // Zoom controls
  const graphViewControlsRef = useRef<{ zoomIn: () => void; zoomOut: () => void; fit: () => void; reset: () => void } | null>(null);
  const [currentZoom, setCurrentZoom] = useState(1);

  return (
    <div className="flex flex-col h-full w-full px-4 py-4">
      {/* Header with controls */}
      <div className="bg-parchment-100 px-4 py-3 border-b border-brass-600 rounded-t-lg">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-2xl font-headline font-semibold text-ink-900">Knowledge Tree</h1>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-ink-900 opacity-70">
              {nodeCount} nodes
            </span>
            {isConnected && (
              <span className="text-xs px-2 py-1 bg-verdigris-500 text-white rounded-xl">
                Live
              </span>
            )}
          </div>
        </div>

        {/* Search and filters */}
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search nodes..."
              className="input w-full"
            />
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={filters.scope}
              onChange={(e) => setFilters({ ...filters, scope: e.target.value })}
              placeholder="Scope (topic ID)"
              className="input px-3 py-2 text-sm"
            />
            <input
              type="number"
              value={filters.depth}
              onChange={(e) => setFilters({ ...filters, depth: parseInt(e.target.value) || 1 })}
              placeholder="Depth"
              min={1}
              max={10}
              className="input w-20 px-3 py-2 text-sm"
            />
            <select
              value={filters.relation}
              onChange={(e) => setFilters({ ...filters, relation: e.target.value })}
              className="input px-3 py-2 text-sm"
            >
              <option value="">All Relations</option>
              <option value="parent-child">Parent-Child</option>
              <option value="belongs-to">Belongs-To</option>
              <option value="evidence">Evidence</option>
            </select>
            <label className="flex items-center space-x-2 text-sm text-ink-900">
              <input
                type="checkbox"
                checked={filters.include_events}
                onChange={(e) => setFilters({ ...filters, include_events: e.target.checked })}
                className="rounded border-brass-600"
              />
              <span>Include Events</span>
            </label>
            <button
              onClick={loadGraph}
              disabled={isLoading}
              className="button button--primary disabled:opacity-50"
            >
              {isLoading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Collapse and zoom controls */}
        <div className="flex items-center space-x-2 mt-2">
          <button
            onClick={handleExpandAll}
            className="button px-3 py-1 text-sm"
          >
            Expand All
          </button>
          <button
            onClick={handleCollapseAll}
            className="button px-3 py-1 text-sm"
          >
            Collapse All
          </button>
          <div className="flex items-center space-x-2 ml-4 border-l border-brass-600 pl-4">
            <button
              onClick={() => graphViewControlsRef.current?.zoomIn()}
              className="button button--primary px-3 py-1 text-sm"
            >
              Zoom In
            </button>
            <button
              onClick={() => graphViewControlsRef.current?.zoomOut()}
              className="button button--primary px-3 py-1 text-sm"
            >
              Zoom Out
            </button>
            <button
              onClick={() => graphViewControlsRef.current?.fit()}
              className="button button--primary px-3 py-1 text-sm"
            >
              Fit
            </button>
            <button
              onClick={() => graphViewControlsRef.current?.reset()}
              className="button button--primary px-3 py-1 text-sm"
            >
              Reset
            </button>
            <span className="text-sm text-ink-900 opacity-70 ml-2">
              Zoom: {(currentZoom * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Graph view */}
      <div className="flex-1 relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-parchment-50 bg-opacity-75 z-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-verdigris-500 mx-auto mb-4"></div>
              <p className="text-ink-900 opacity-70">Loading graph...</p>
            </div>
          </div>
        )}
        {graphData && (
          <GraphView
            data={graphData}
            onNodeClick={handleNodeClick}
            onHover={handleHover}
            searchQuery={searchQuery}
            collapsedNodes={collapsedNodes}
            onToggleCollapse={handleToggleCollapse}
            onZoomChange={setCurrentZoom}
            controlsRef={graphViewControlsRef}
          />
        )}
      </div>
    </div>
  );
}
