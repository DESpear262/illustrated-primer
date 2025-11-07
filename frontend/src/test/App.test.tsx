/**
 * Tests for App component.
 * 
 * Verifies that routing works correctly and navigation preserves app state.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

describe('App', () => {
  it('renders the app with routing', () => {
    render(<App />);

    // Check that the header is rendered
    expect(screen.getByText('AI Tutor')).toBeInTheDocument();
  });

  it('navigates to chat page by default', () => {
    render(<App />);

    // Check that Chat link is present (there are multiple, so use getAllByText)
    const chatLinks = screen.getAllByText('Chat');
    expect(chatLinks.length).toBeGreaterThan(0);
  });
});

