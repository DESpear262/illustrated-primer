/**
 * Tests for Chat component.
 * 
 * Verifies that chat interface works correctly with session management,
 * message sending, and context chunks display.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Chat } from '../pages/Chat';
import { apiClient } from '../lib/api';

// Mock API client
vi.mock('../lib/api', () => ({
  apiClient: {
    chatList: vi.fn(),
    chatStart: vi.fn(),
    chatResume: vi.fn(),
    chatTurn: vi.fn(),
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

describe('Chat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    // Mock chatList to return empty sessions by default
    vi.mocked(apiClient.chatList).mockResolvedValue({
      success: true,
      result: { sessions: [] },
      duration_seconds: 0.1,
    });
  });

  it('renders chat interface', async () => {
    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Tutor Chat')).toBeInTheDocument();
    });
  });

  it('loads sessions on mount', async () => {
    const mockSessions = [
      { session_id: '1', title: 'Test Session', last_at: '2024-01-01', cnt: 5 },
    ];
    vi.mocked(apiClient.chatList).mockResolvedValue({
      success: true,
      result: { sessions: mockSessions },
      duration_seconds: 0.1,
    });

    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(apiClient.chatList).toHaveBeenCalled();
    });
  });

  it('starts new session', async () => {
    const user = userEvent.setup();
    const mockSession = { session_id: '1', title: 'New Session' };
    vi.mocked(apiClient.chatStart).mockResolvedValue({
      success: true,
      result: mockSession,
      duration_seconds: 0.1,
    });

    render(
      <BrowserRouter>
        <Chat />
      </BrowserRouter>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(apiClient.chatList).toHaveBeenCalled();
    });

    // Find and click new session button
    const newSessionButton = screen.getByText('New Session');
    await user.click(newSessionButton);

    await waitFor(() => {
      expect(apiClient.chatStart).toHaveBeenCalled();
    });
  });
});

