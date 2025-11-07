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
    <header className="bg-parchment-100 border-b border-brass-600 shadow-brass">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <h1 className="text-xl font-headline font-semibold text-ink-900">AI Tutor</h1>
            <nav className="flex space-x-4">
              <Link
                to="/chat"
                className={`px-3 py-2 rounded-xl transition-all duration-120 ${
                  location.pathname === '/chat'
                    ? 'bg-brass-600 text-white'
                    : 'text-ink-900 hover:bg-parchment-50 hover:text-verdigris-500'
                }`}
              >
                Chat
              </Link>
              <Link
                to="/console"
                className={`px-3 py-2 rounded-xl transition-all duration-120 ${
                  location.pathname === '/console'
                    ? 'bg-brass-600 text-white'
                    : 'text-ink-900 hover:bg-parchment-50 hover:text-verdigris-500'
                }`}
              >
                Console
              </Link>
              <Link
                to="/review"
                className={`px-3 py-2 rounded-xl transition-all duration-120 ${
                  location.pathname === '/review'
                    ? 'bg-brass-600 text-white'
                    : 'text-ink-900 hover:bg-parchment-50 hover:text-verdigris-500'
                }`}
              >
                Review
              </Link>
              <Link
                to="/context"
                className={`px-3 py-2 rounded-xl transition-all duration-120 ${
                  location.pathname === '/context'
                    ? 'bg-brass-600 text-white'
                    : 'text-ink-900 hover:bg-parchment-50 hover:text-verdigris-500'
                }`}
              >
                Context
              </Link>
              <Link
                to="/knowledge-tree"
                className={`px-3 py-2 rounded-xl transition-all duration-120 ${
                  location.pathname === '/knowledge-tree'
                    ? 'bg-brass-600 text-white'
                    : 'text-ink-900 hover:bg-parchment-50 hover:text-verdigris-500'
                }`}
              >
                Knowledge Tree
              </Link>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <button className="px-3 py-2 rounded-xl text-ink-900 hover:bg-parchment-50 hover:text-verdigris-500 transition-all duration-120">
              File
            </button>
            <button className="px-3 py-2 rounded-xl text-ink-900 hover:bg-parchment-50 hover:text-verdigris-500 transition-all duration-120">
              Database
            </button>
            <button className="px-3 py-2 rounded-xl text-ink-900 hover:bg-parchment-50 hover:text-verdigris-500 transition-all duration-120">
              Index
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

