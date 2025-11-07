/**
 * Tests for Console component.
 * 
 * Verifies that command console works correctly with form-based UI
 * and command execution.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Console } from '../pages/Console';
import { apiClient } from '../lib/api';

// Mock API client
vi.mock('../lib/api', () => ({
  apiClient: {
    dbCheck: vi.fn(),
    dbInit: vi.fn(),
    indexBuild: vi.fn(),
    indexStatus: vi.fn(),
    indexSearch: vi.fn(),
    aiRoutes: vi.fn(),
    aiTest: vi.fn(),
    chatStart: vi.fn(),
    chatResume: vi.fn(),
    chatList: vi.fn(),
  },
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
globalThis.localStorage = localStorageMock as unknown as Storage;

describe('Console', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  it('renders console interface', () => {
    render(
      <BrowserRouter>
        <Console />
      </BrowserRouter>
    );

    expect(screen.getByText('Command Console')).toBeInTheDocument();
  });

  it('executes database check command', async () => {
    const user = userEvent.setup();
    vi.mocked(apiClient.dbCheck).mockResolvedValue({
      success: true,
      result: { status: 'ok' },
      duration_seconds: 0.1,
    });

    render(
      <BrowserRouter>
        <Console />
      </BrowserRouter>
    );

    const checkButton = screen.getByText('Check Database');
    await user.click(checkButton);

    await waitFor(() => {
      expect(apiClient.dbCheck).toHaveBeenCalled();
    });
  });

  it('executes index search command', async () => {
    const user = userEvent.setup();
    vi.mocked(apiClient.indexSearch).mockResolvedValue({
      success: true,
      result: { results: [] },
      duration_seconds: 0.1,
    });

    render(
      <BrowserRouter>
        <Console />
      </BrowserRouter>
    );

    // Switch to index tab
    const indexTab = screen.getByText('INDEX');
    await user.click(indexTab);

    // Enter search query
    const queryInput = screen.getByPlaceholderText('Enter search query');
    await user.type(queryInput, 'test query');

    // Click search button
    const searchButton = screen.getByText('Search');
    await user.click(searchButton);

    await waitFor(() => {
      expect(apiClient.indexSearch).toHaveBeenCalledWith('test query', 5, true);
    });
  });
});

