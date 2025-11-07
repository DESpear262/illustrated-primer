/**
 * Knowledge Tree page for AI Tutor application.
 * 
 * Implements the Knowledge Tree visualization interface with Cytoscape.js,
 * search, collapse, zoom, pan, and navigation to Context page.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient, GraphData, HoverPayload } from '../lib/api';
import { GraphView, GraphViewControls } from '../components/GraphView';
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

  // Load graph data
  const loadGraph = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.getGraph({
        scope: filters.scope || undefined,
        depth: filters.depth || undefined,
        relation: filters.relation || undefined,
        include_events: filters.include_events,
      });
      setGraphData(data);
      setNodeCount(data.nodes.length);
      toast.success(`Graph loaded with ${data.nodes.length} nodes`);
    } catch (error) {
      toast.error('Failed to load graph');
      console.error('Failed to load graph:', error);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

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
    <div className="flex flex-col h-full">
      {/* Header with controls */}
      <div className="bg-gray-200 px-4 py-3 border-b border-gray-300">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-2xl font-bold">Knowledge Tree</h1>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">
              {nodeCount} nodes
            </span>
            {isConnected && (
              <span className="text-xs px-2 py-1 bg-green-500 text-white rounded">
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
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={filters.scope}
              onChange={(e) => setFilters({ ...filters, scope: e.target.value })}
              placeholder="Scope (topic ID)"
              className="px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              type="number"
              value={filters.depth}
              onChange={(e) => setFilters({ ...filters, depth: parseInt(e.target.value) || 1 })}
              placeholder="Depth"
              min={1}
              max={10}
              className="w-20 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={filters.relation}
              onChange={(e) => setFilters({ ...filters, relation: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Relations</option>
              <option value="parent-child">Parent-Child</option>
              <option value="belongs-to">Belongs-To</option>
              <option value="evidence">Evidence</option>
            </select>
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={filters.include_events}
                onChange={(e) => setFilters({ ...filters, include_events: e.target.checked })}
                className="rounded"
              />
              <span>Include Events</span>
            </label>
            <button
              onClick={loadGraph}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {isLoading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Collapse and zoom controls */}
        <div className="flex items-center space-x-2 mt-2">
          <button
            onClick={handleExpandAll}
            className="px-3 py-1 bg-gray-300 rounded hover:bg-gray-400 text-sm"
          >
            Expand All
          </button>
          <button
            onClick={handleCollapseAll}
            className="px-3 py-1 bg-gray-300 rounded hover:bg-gray-400 text-sm"
          >
            Collapse All
          </button>
          <div className="flex items-center space-x-2 ml-4 border-l border-gray-400 pl-4">
            <button
              onClick={() => graphViewControlsRef.current?.zoomIn()}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
            >
              Zoom In
            </button>
            <button
              onClick={() => graphViewControlsRef.current?.zoomOut()}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
            >
              Zoom Out
            </button>
            <button
              onClick={() => graphViewControlsRef.current?.fit()}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
            >
              Fit
            </button>
            <button
              onClick={() => graphViewControlsRef.current?.reset()}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
            >
              Reset
            </button>
            <span className="text-sm text-gray-600 ml-2">
              Zoom: {(currentZoom * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Graph view */}
      <div className="flex-1 relative overflow-hidden">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading graph...</p>
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
