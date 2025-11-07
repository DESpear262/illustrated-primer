/**
 * Context page for AI Tutor application.
 * 
 * Placeholder page for the Context Inspector interface.
 */

import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';

/**
 * Context page component.
 */
export function Context() {
  const [apiStatus, setApiStatus] = useState<string>('Checking...');

  useEffect(() => {
    // Minimal API call for validation
    apiClient
      .healthCheck()
      .then(() => setApiStatus('API connected'))
      .catch(() => setApiStatus('API connection failed'));
  }, []);

  return (
    <div className="space-y-4 p-6 bg-parchment-50">
      <h1 className="text-3xl font-headline font-semibold text-ink-900">Context Inspector</h1>
      <p className="text-ink-900 opacity-70">
        This is a placeholder for the Context Inspector interface.
      </p>
      <div className="card">
        <p className="text-sm text-ink-900">
          <strong>Status:</strong> {apiStatus}
        </p>
      </div>
    </div>
  );
}

