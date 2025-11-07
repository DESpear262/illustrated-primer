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
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">Context Inspector</h1>
      <p className="text-gray-600">
        This is a placeholder for the Context Inspector interface.
      </p>
      <div className="p-4 bg-gray-100 rounded">
        <p className="text-sm">
          <strong>Status:</strong> {apiStatus}
        </p>
      </div>
    </div>
  );
}

