import {
  LayoutDashboard,
  School,
  Map as MapIcon,
  Bell,
  BarChart3,
  Trophy,
  Settings,
  User,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAppStore } from '@/src/store';
import { cn } from '@/src/lib/utils';

const navItems = [
  { icon: LayoutDashboard, label: 'Vue d\'ensemble', path: '/' },
  { icon: School, label: 'Établissements', path: '/institutions' },
  { icon: MapIcon, label: 'Carte interactive', path: '/carte' },
  { icon: Bell, label: 'Alertes', path: '/alertes', badge: 8 },
  { icon: BarChart3, label: 'Analytiques', path: '/analytiques' },
  { icon: Trophy, label: 'Classements', path: '/classements' },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <aside
      className={cn(
        'bg-slate-900 border-r border-slate-700 h-screen sticky top-0 flex flex-col flex-shrink-0 z-50 transition-[width] duration-150',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )}
    >
      <div className={cn('h-16 flex items-center justify-between border-b border-slate-700', sidebarCollapsed ? 'px-2' : 'px-4')}>
        {!sidebarCollapsed && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-700 rounded-md flex items-center justify-center">
              <div className="w-3.5 h-3.5 border-2 border-white rounded-sm"></div>
            </div>
            <span className="text-base font-semibold text-white">UCAR HQ</span>
          </div>
        )}
        <button 
          onClick={toggleSidebar}
          className="p-2 hover:bg-slate-800 rounded text-slate-300 transition-colors duration-150"
          aria-label={sidebarCollapsed ? 'Developper la barre laterale' : 'Reduire la barre laterale'}
        >
          {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="flex-1 py-4 overflow-y-auto overflow-x-hidden">
        <ul className="space-y-1 px-2 text-slate-300">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) => cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md transition-colors duration-150 group relative text-sm',
                  isActive 
                    ? 'bg-blue-800 text-white font-semibold'
                    : 'hover:bg-slate-800 hover:text-white font-medium'
                )}
                title={sidebarCollapsed ? item.label : undefined}
              >
                {({ isActive }) => (
                  <>
                    <item.icon size={18} className={cn(isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200')} />
                    {!sidebarCollapsed && (
                      <span className="whitespace-nowrap">{item.label}</span>
                    )}
                    {item.badge && (
                      <span className={cn(
                        'ml-auto text-xs font-semibold px-1.5 py-0.5 rounded',
                        isActive ? 'bg-white/20 text-white' : 'bg-slate-700 text-slate-100'
                      )}>
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="mt-8 px-2">
          {!sidebarCollapsed && (
            <div className="px-3 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wide">
              Administration
            </div>
          )}
          <ul className="space-y-1.5">
            <li>
              <button className="w-full flex items-center gap-3 px-3 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-md transition-colors duration-150 font-medium text-sm">
                <Settings size={18} className="text-slate-400" />
                {!sidebarCollapsed && <span className="text-sm">Configuration</span>}
              </button>
            </li>
            <li>
              <button className="w-full flex items-center gap-3 px-3 py-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-md transition-colors duration-150 font-medium text-sm">
                <User size={18} className="text-slate-400" />
                {!sidebarCollapsed && <span className="text-sm">Mon compte</span>}
              </button>
            </li>
          </ul>
        </div>
      </nav>

      <div className="p-3 border-t border-slate-700">
        <div className={cn(
          'flex items-center gap-3 bg-slate-800 p-2 rounded-md',
          sidebarCollapsed && "justify-center"
        )}>
          <div className="w-8 h-8 rounded-full bg-slate-700 flex-shrink-0 flex items-center justify-center text-slate-200 font-semibold text-xs">
            BS
          </div>
          {!sidebarCollapsed && (
            <div className="overflow-hidden">
              <p className="text-sm font-semibold text-white truncate">Dr. Ben Salah</p>
              <p className="text-xs text-slate-400 truncate">Lead Architect</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
