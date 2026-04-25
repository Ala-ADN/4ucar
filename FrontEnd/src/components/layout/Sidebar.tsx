import { motion, AnimatePresence } from 'motion/react';
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

  return (    <motion.aside
      initial={false}
      animate={{ width: sidebarCollapsed ? 60 : 240 }}
      className="bg-[#0F172A] border-r border-slate-800 h-screen sticky top-0 flex flex-col flex-shrink-0 z-50 shadow-2xl shadow-black/50"
    >
      <div className="h-20 flex items-center justify-between px-6 border-b border-slate-800">
        {!sidebarCollapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-3"
          >
            <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
              <div className="w-4 h-4 border-2 border-white rounded-sm"></div>
            </div>
            <span className="text-lg font-bold text-white tracking-tight">UCAR HQ</span>
          </motion.div>
        )}
        <button 
          onClick={toggleSidebar}
          className="p-1.5 hover:bg-slate-800 rounded-md text-slate-400 transition-colors"
        >
          {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="flex-1 py-6 overflow-y-auto overflow-x-hidden">
        <ul className="space-y-1.5 px-4 text-slate-400">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) => cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group relative",
                  isActive 
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/10 font-semibold" 
                    : "hover:bg-slate-800 hover:text-white font-medium"
                )}
                title={sidebarCollapsed ? item.label : undefined}
              >
                {({ isActive }) => (
                  <>
                    <item.icon size={18} className={cn(isActive ? "text-white" : "text-slate-500 group-hover:text-slate-300")} />
                    {!sidebarCollapsed && (
                      <motion.span
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="text-sm whitespace-nowrap"
                      >
                        {item.label}
                      </motion.span>
                    )}
                    {item.badge && (
                      <span className={cn(
                        "ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded-md",
                        isActive ? "bg-white/20 text-white" : "bg-blue-600 text-white"
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

        <div className="mt-10 px-4">
          {!sidebarCollapsed && (
            <div className="px-4 mb-2 text-[10px] font-bold text-slate-500 uppercase tracking-[0.15em]">
              Administration
            </div>
          )}
          <ul className="space-y-1.5">
            <li>
              <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors font-medium">
                <Settings size={18} className="text-slate-500" />
                {!sidebarCollapsed && <span className="text-sm">Configuration</span>}
              </button>
            </li>
            <li>
              <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors font-medium">
                <User size={18} className="text-slate-500" />
                {!sidebarCollapsed && <span className="text-sm">Mon compte</span>}
              </button>
            </li>
          </ul>
        </div>
      </nav>

      <div className="p-4 border-t border-slate-800 m-2 mt-0">
        <div className={cn(
          "flex items-center gap-3 bg-slate-800/50 p-3 rounded-xl",
          sidebarCollapsed && "justify-center"
        )}>
          <div className="w-9 h-9 rounded-full bg-slate-700 flex-shrink-0 flex items-center justify-center text-slate-300 font-bold text-xs ring-2 ring-slate-800">
            BS
          </div>
          {!sidebarCollapsed && (
            <div className="overflow-hidden">
              <p className="text-xs font-bold text-white uppercase tracking-tight truncate">Dr. Ben Salah</p>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter truncate">Lead Architect</p>
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
