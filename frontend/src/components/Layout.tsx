/**
 * Layout component for AI Tutor application.
 * 
 * Provides the main layout structure with header, sidebar, content area,
 * and status footer. All pages are rendered within this layout.
 */

import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { StatusFooter } from './StatusFooter';

/**
 * Main layout component.
 */
export function Layout() {
  return (
    <div className="flex flex-col h-screen">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-white">
          <div className="container mx-auto px-4 py-6">
            <Outlet />
          </div>
        </main>
      </div>
      <StatusFooter />
    </div>
  );
}

