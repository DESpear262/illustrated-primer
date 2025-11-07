/**
 * Header component for AI Tutor application.
 * 
 * Displays the top menu bar with navigation and actions.
 */

import { Link, useLocation } from 'react-router-dom';

/**
 * Header component with top menu bar.
 */
export function Header() {
  const location = useLocation();

  return (
    <header className="bg-gray-800 text-white shadow-md">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <h1 className="text-xl font-bold">AI Tutor</h1>
            <nav className="flex space-x-4">
              <Link
                to="/chat"
                className={`px-3 py-2 rounded ${
                  location.pathname === '/chat'
                    ? 'bg-gray-700'
                    : 'hover:bg-gray-700'
                }`}
              >
                Chat
              </Link>
              <Link
                to="/console"
                className={`px-3 py-2 rounded ${
                  location.pathname === '/console'
                    ? 'bg-gray-700'
                    : 'hover:bg-gray-700'
                }`}
              >
                Console
              </Link>
              <Link
                to="/review"
                className={`px-3 py-2 rounded ${
                  location.pathname === '/review'
                    ? 'bg-gray-700'
                    : 'hover:bg-gray-700'
                }`}
              >
                Review
              </Link>
              <Link
                to="/context"
                className={`px-3 py-2 rounded ${
                  location.pathname === '/context'
                    ? 'bg-gray-700'
                    : 'hover:bg-gray-700'
                }`}
              >
                Context
              </Link>
              <Link
                to="/knowledge-tree"
                className={`px-3 py-2 rounded ${
                  location.pathname === '/knowledge-tree'
                    ? 'bg-gray-700'
                    : 'hover:bg-gray-700'
                }`}
              >
                Knowledge Tree
              </Link>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <button className="px-3 py-2 rounded hover:bg-gray-700">
              File
            </button>
            <button className="px-3 py-2 rounded hover:bg-gray-700">
              Database
            </button>
            <button className="px-3 py-2 rounded hover:bg-gray-700">
              Index
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

