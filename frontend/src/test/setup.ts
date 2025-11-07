/**
 * Test setup file for Vitest.
 * 
 * Configures testing environment with React Testing Library and jest-dom matchers.
 */

import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// Cleanup after each test
afterEach(() => {
  cleanup();
});

