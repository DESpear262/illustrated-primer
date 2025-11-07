/**
 * Home page for AI Tutor application.
 * 
 * Default landing page that redirects to Chat.
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Home page component.
 */
export function Home() {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to Chat page by default
    navigate('/chat', { replace: true });
  }, [navigate]);

  return null;
}

