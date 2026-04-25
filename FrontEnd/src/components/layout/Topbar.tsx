import { Bell, Search, User } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { motion } from 'motion/react';

const pageTitles: Record<string, string> = {
  '/': 'Vue d\'ensemble',
  '/institutions': 'Établissements',
  '/carte': 'Carte interactive',
  '/alertes': 'Centre d\'alertes',
  '/analytiques': 'Explorateur KPI',
  '/classements': 'Classements'
};

export function Topbar() {
  const location = useLocation();
  const title = pageTitles[location.pathname] || 'Tableau de bord';

  return (
    <header className="h-20 bg-surface border-b border-slate-200 px-10 flex items-center justify-between sticky top-0 z-40">
      <div className="flex flex-col">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
        <p className="text-slate-400 text-[10px] font-bold uppercase tracking-[0.2em] mt-0.5">Réseau Universitaire: TUNIS-CENTRAL</p>
      </div>

      <div className="flex items-center gap-8">
        <div className="flex items-center gap-6">
          <div className="flex flex-col items-end">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">Stabilité Réseau</span>
            <span className="text-sm font-bold text-status-good flex items-center gap-1.5 font-tabular">99.98% STABLE</span>
          </div>
          <div className="h-10 w-px bg-slate-200" />
        </div>

        <div className="flex items-center gap-4">
          <motion.div 
            className="relative group hidden lg:block"
            whileFocus-within={{ width: 280 }}
            initial={{ width: 220 }}
          >
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-600 transition-colors" />
            <input 
              type="text" 
              placeholder="Recherche système..."
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-blue-600/10 outline-none transition-all placeholder:text-slate-400"
            />
          </motion.div>

          <button className="relative p-2.5 text-slate-500 hover:bg-slate-50 rounded-lg transition-colors border border-transparent hover:border-slate-200">
            <Bell size={20} />
            <span className="absolute top-2 right-2 w-2 h-2 bg-status-critical rounded-full border-2 border-surface" />
          </button>
          
          <button className="px-5 py-2.5 bg-slate-900 text-white rounded-lg text-sm font-bold shadow-lg shadow-black/10 hover:bg-slate-800 transition-all">
            Déployer Rapport
          </button>
        </div>
      </div>
    </header>
  );
}
