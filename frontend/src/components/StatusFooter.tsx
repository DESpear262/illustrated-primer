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
    <footer className="bg-parchment-100 border-t border-brass-600 px-4 py-2 shadow-brass">
      <div className="container mx-auto flex items-center justify-between text-sm text-ink-900">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <span>API:</span>
            <span
              className={`px-2 py-1 rounded-xl ${
                apiHealth === 'ok'
                  ? 'bg-verdigris-500 text-white'
                  : apiHealth === 'error'
                  ? 'bg-garnet-600 text-white'
                  : 'bg-brass-600 text-white'
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
        <div className="text-ink-900">
          AI Tutor v1.0.0
        </div>
      </div>
    </footer>
  );
}

