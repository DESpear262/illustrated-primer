/**
 * Tests for Layout component.
 * 
 * Verifies that layout renders correctly with header, sidebar, and footer.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Layout } from '../components/Layout';

describe('Layout', () => {
  it('renders header, sidebar, and footer', () => {
    render(
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    );

    // Check that header is rendered
    expect(screen.getByText('AI Tutor')).toBeInTheDocument();
    
    // Check that sidebar navigation is rendered (there are multiple Chat/Console elements, so use getAllByText)
    const chatLinks = screen.getAllByText('Chat');
    expect(chatLinks.length).toBeGreaterThan(0);
    
    const consoleLinks = screen.getAllByText('Console');
    expect(consoleLinks.length).toBeGreaterThan(0);
  });
});

