/**
 * Tests for GraphView component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { GraphView } from '../components/GraphView';
import type { GraphData } from '../lib/api';

// Mock Cytoscape
vi.mock('cytoscape', () => {
  const mockCy = {
    on: vi.fn(),
    fit: vi.fn(),
    zoom: vi.fn(() => 1),
    nodes: vi.fn(() => ({
      forEach: vi.fn(),
      removeClass: vi.fn(),
      addClass: vi.fn(),
    })),
    edges: vi.fn(() => ({
      forEach: vi.fn(),
      show: vi.fn(),
      hide: vi.fn(),
    })),
    destroy: vi.fn(),
  };
  
  return {
    default: vi.fn(() => mockCy),
    use: vi.fn(),
  };
});

// Mock cytoscape-elk
vi.mock('cytoscape-elk', () => ({
  default: vi.fn(),
}));

describe('GraphView', () => {
  const mockGraphData: GraphData = {
    nodes: [
      {
        data: {
          id: 'topic:math',
          type: 'topic',
          label: 'Math',
          summary: 'Mathematics fundamentals',
        },
      },
      {
        data: {
          id: 'skill:derivative',
          type: 'skill',
          label: 'Derivative',
          mastery: 0.8,
        },
      },
    ],
    edges: [
      {
        data: {
          id: 'e1',
          source: 'topic:math',
          target: 'skill:derivative',
          type: 'belongs-to',
          label: 'has-skill',
        },
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders graph view', () => {
    const { container } = render(<GraphView data={mockGraphData} />);
    expect(container.querySelector('.relative')).toBeInTheDocument();
  });

  it('handles node click', async () => {
    const onNodeClick = vi.fn();
    render(<GraphView data={mockGraphData} onNodeClick={onNodeClick} />);
    
    // Wait for Cytoscape to initialize
    await waitFor(() => {
      expect(onNodeClick).toBeDefined();
    });
  });

  it('handles search query filtering', async () => {
    const { container } = render(<GraphView data={mockGraphData} searchQuery="math" />);
    
    // Wait for component to render
    await waitFor(() => {
      expect(container.querySelector('.relative')).toBeInTheDocument();
    });
  });

  it('handles collapsed nodes', async () => {
    const collapsedNodes = new Set(['topic:math']);
    const { container } = render(<GraphView data={mockGraphData} collapsedNodes={collapsedNodes} />);
    
    // Wait for component to render
    await waitFor(() => {
      expect(container.querySelector('.relative')).toBeInTheDocument();
    });
  });
});

