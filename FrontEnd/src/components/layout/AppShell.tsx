import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { useLocation } from 'react-router-dom';

export function AppShell() {
  const location = useLocation();

  return (
    <div className="app-atmosphere flex h-screen w-full overflow-hidden text-gray-900">
      {/* Fixed Sidebar */}
      <aside className="shrink-0 z-20">
        <Sidebar />
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0">
        <header className="shrink-0 z-10">
          <Topbar />
        </header>

        {/* Scrollable Content */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet key={location.pathname} />
          </div>
        </main>
      </div>
    </div>
  );
}
