/**
 * Status footer component for AI Tutor application.
 * 
 * Displays API health, database path, and FAISS index state.
 */

import { useEffect, useState } from 'react';
import { apiClient } from '../lib/api';

/**
 * Status footer component.
 */
export function StatusFooter() {
  const [apiHealth, setApiHealth] = useState<'ok' | 'error' | 'checking'>('checking');
  const [dbPath, setDbPath] = useState<string>('Unknown');
  const [indexState, setIndexState] = useState<string>('Unknown');

  useEffect(() => {
    // Check API health
    const checkHealth = async () => {
      try {
        const response = await apiClient.healthCheck();
        setApiHealth(response.status === 'ok' ? 'ok' : 'error');
      } catch (error) {
        setApiHealth('error');
      }
    };

    checkHealth();
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="bg-gray-200 border-t border-gray-300 px-4 py-2">
      <div className="container mx-auto flex items-center justify-between text-sm">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <span>API:</span>
            <span
              className={`px-2 py-1 rounded ${
                apiHealth === 'ok'
                  ? 'bg-green-500 text-white'
                  : apiHealth === 'error'
                  ? 'bg-red-500 text-white'
                  : 'bg-yellow-500 text-white'
              }`}
            >
              {apiHealth === 'ok' ? 'Connected' : apiHealth === 'error' ? 'Error' : 'Checking...'}
            </span>
          </div>
          <div>
            <span className="font-semibold">Database:</span> {dbPath}
          </div>
          <div>
            <span className="font-semibold">Index:</span> {indexState}
          </div>
        </div>
        <div className="text-gray-600">
          AI Tutor v1.0.0
        </div>
      </div>
    </footer>
  );
}

