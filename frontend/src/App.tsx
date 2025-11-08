/**
 * Main App component for AI Tutor application.
 * 
 * Sets up React Router and provides the main routing structure.
 * Handles Tauri backend startup in bundled mode.
 */

import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Layout } from './components/Layout';
import { Chat } from './pages/Chat';
import { Console } from './pages/Console';
import { Review } from './pages/Review';
import { Context } from './pages/Context';
import { KnowledgeTree } from './pages/KnowledgeTree';
import { Home } from './pages/Home';
import { isTauri, startBackend, stopBackend } from './lib/tauri';

/**
 * Main App component.
 */
function App() {
  useEffect(() => {
    if (isTauri()) {
      // Start backend when app loads in Tauri mode
      startBackend().catch((err) => {
        console.error('Failed to start backend:', err);
      });
      
      // Cleanup: stop backend on unmount
      return () => {
        if (isTauri()) {
          stopBackend().catch(console.error);
        }
      };
    }
  }, []);

  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="chat" element={<Chat />} />
          <Route path="console" element={<Console />} />
          <Route path="review" element={<Review />} />
          <Route path="context" element={<Context />} />
          <Route path="knowledge-tree" element={<KnowledgeTree />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
