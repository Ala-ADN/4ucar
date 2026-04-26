import {
  LayoutDashboard,
  School,
  ShieldCheck,
  Wallet,
  FileText,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAppStore } from '@/src/store';
import { cn } from '@/src/lib/utils';
import logoSrc from '@/src/assets/logo-ucar.png';

const navItems = [
  { icon: LayoutDashboard, label: 'Tableau de Bord', path: '/' },
  { icon: School, label: 'Carte du Réseau', path: '/institutions' },
  { icon: ShieldCheck, label: 'Accréditations', path: '/accreditations' },
  { icon: Wallet, label: 'Finances', path: '/finance' },
  { icon: AlertCircle, label: 'Centre d\'Opérations', path: '/alertes' },
  { icon: FileText, label: 'Rapports', path: '/reports' },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <aside
      className={cn(
        'bg-[#112D4E] h-screen sticky top-0 flex flex-col shrink-0 z-50 transition-[width] duration-150',
        sidebarCollapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Brand */}
      <div className="h-16 flex items-center justify-center border-b border-slate-200 bg-white px-4 m-5 rounded-lg">
        {!sidebarCollapsed && (
          <img
            src={logoSrc}
            alt="Logo Université de Carthage"
            className="h-11 w-auto object-contain"
          />
        )}
        {sidebarCollapsed && (
          <img
            src={logoSrc}
            alt="Logo Université de Carthage"
            className="h-8 w-auto object-contain"
          />
        )}
      </div>

      {/* Toggle */}
      <div className={cn('flex px-2 pt-3', sidebarCollapsed ? 'justify-center' : 'justify-end')}>
        <button
          onClick={toggleSidebar}
          className="p-1.5 hover:bg-white/10 rounded-md text-white/40 transition-colors duration-100"
          aria-label={sidebarCollapsed ? 'Développer' : 'Réduire'}
        >
          {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-2 overflow-y-auto overflow-x-hidden">
        <ul className="space-y-0.5 px-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) => cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors duration-100 group relative text-[13px]',
                  isActive
                    ? 'bg-white/15 text-white font-semibold'
                    : 'text-white/60 hover:bg-white/8 hover:text-white/90 font-medium'
                )}
                title={sidebarCollapsed ? item.label : undefined}
              >
                {({ isActive }) => (
                  <>
                    <item.icon
                      size={18}
                      className={cn(
                        isActive ? 'text-white' : 'text-white/40 group-hover:text-white/70'
                      )}
                      strokeWidth={isActive ? 2.2 : 1.8}
                    />
                    {!sidebarCollapsed && (
                      <span className="whitespace-nowrap">{item.label}</span>
                    )}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Bottom */}
      {!sidebarCollapsed && (
        <div className="px-5 py-4 border-t border-white/10">
          <p className="text-[10px] text-white/30 uppercase tracking-wider">UCAR ERP · v0.9-beta</p>
        </div>
      )}
    </aside>
  );
}

