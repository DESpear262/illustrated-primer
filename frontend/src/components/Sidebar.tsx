/**
 * Sidebar component for AI Tutor application.
 * 
 * Displays collapsible navigation shortcuts.
 */

import { Link, useLocation } from 'react-router-dom';
import { useState } from 'react';

/**
 * Sidebar component with navigation shortcuts.
 */
export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  const navItems = [
    { path: '/chat', label: 'Chat', icon: '💬' },
    { path: '/console', label: 'Console', icon: '⌨️' },
    { path: '/review', label: 'Review', icon: '📚' },
    { path: '/context', label: 'Context', icon: '🔍' },
    { path: '/knowledge-tree', label: 'Knowledge Tree', icon: '🌳' },
  ];

  return (
    <aside
      className={`bg-parchment-100 border-r border-brass-600 transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="p-4">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full mb-4 px-3 py-2 bg-parchment-50 hover:bg-brass-600 hover:text-white rounded-xl text-sm transition-all duration-120 border border-brass-600"
        >
          {isCollapsed ? '▶' : '◀'}
        </button>
        <nav className="space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-3 px-3 py-2 rounded-xl transition-all duration-120 ${
                location.pathname === item.path
                  ? 'bg-verdigris-500 text-white'
                  : 'text-ink-900 hover:bg-parchment-50 hover:text-verdigris-500'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              {!isCollapsed && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  );
}

