/**
 * Tests for HoverCard component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HoverCard } from '../components/HoverCard';
import { HoverPayload } from '../lib/api';

describe('HoverCard', () => {
  const mockTopicPayload: HoverPayload = {
    title: 'Math',
    type: 'topic',
    summary: 'Mathematics fundamentals',
    event_count: 10,
    last_event_at: '2024-01-01T00:00:00Z',
    statistics: {},
  };

  const mockSkillPayload: HoverPayload = {
    title: 'Derivative',
    type: 'skill',
    mastery: 0.8,
    evidence_count: 5,
    last_evidence_at: '2024-01-01T00:00:00Z',
    topic_id: 'math',
    statistics: {},
  };

  const mockEventPayload: HoverPayload = {
    title: 'Event 123',
    type: 'event',
    content: 'This is a test event',
    event_type: 'chat',
    actor: 'student',
    created_at: '2024-01-01T00:00:00Z',
    statistics: {},
  };

  it('renders topic hover card', () => {
    render(<HoverCard payload={mockTopicPayload} x={100} y={100} />);
    expect(screen.getByText('Math')).toBeInTheDocument();
    expect(screen.getByText('topic')).toBeInTheDocument();
    expect(screen.getByText('Mathematics fundamentals')).toBeInTheDocument();
  });

  it('renders skill hover card', () => {
    render(<HoverCard payload={mockSkillPayload} x={100} y={100} />);
    expect(screen.getByText('Derivative')).toBeInTheDocument();
    expect(screen.getByText('skill')).toBeInTheDocument();
    expect(screen.getByText(/80%/)).toBeInTheDocument();
  });

  it('renders event hover card', () => {
    render(<HoverCard payload={mockEventPayload} x={100} y={100} />);
    expect(screen.getByText('Event 123')).toBeInTheDocument();
    expect(screen.getByText('event')).toBeInTheDocument();
    expect(screen.getByText('This is a test event')).toBeInTheDocument();
  });

  it('handles close button', () => {
    const onClose = vi.fn();
    render(<HoverCard payload={mockTopicPayload} x={100} y={100} onClose={onClose} />);
    
    const closeButton = screen.getByRole('button');
    expect(closeButton).toBeInTheDocument();
  });
});

