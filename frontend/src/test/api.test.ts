/**
 * Tests for API client.
 * 
 * Verifies that API client is configured correctly and can make requests.
 */

import { describe, it, expect, vi } from 'vitest';
import { ApiClient, apiConfig } from '../lib/api';

describe('ApiClient', () => {
  it('has correct default base URL', () => {
    expect(apiConfig.baseUrl).toBe('http://localhost:8000/api');
  });

  it('can be instantiated with custom base URL', () => {
    const client = new ApiClient('http://custom-url/api');
    expect(client).toBeInstanceOf(ApiClient);
  });

  it('can make GET requests', async () => {
    const client = new ApiClient('http://localhost:8000/api');
    
    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'ok' }),
    });

    const result = await client.get<{ status: string }>('/health');
    expect(result).toEqual({ status: 'ok' });
  });

  it('handles API errors', async () => {
    const client = new ApiClient('http://localhost:8000/api');
    
    // Mock fetch to return error
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      statusText: 'Not Found',
    });

    await expect(client.get('/invalid')).rejects.toThrow('API request failed: Not Found');
  });
});

