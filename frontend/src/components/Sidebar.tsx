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
      className={`bg-gray-100 border-r border-gray-300 transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="p-4">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full mb-4 px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded text-sm"
        >
          {isCollapsed ? '▶' : '◀'}
        </button>
        <nav className="space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-3 px-3 py-2 rounded ${
                location.pathname === item.path
                  ? 'bg-blue-500 text-white'
                  : 'hover:bg-gray-200'
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

