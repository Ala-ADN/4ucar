import { Bell, Search, User } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const pageTitles: Record<string, string> = {
  '/': 'Tableau KPI UCAR',
  '/institutions': 'Établissements',
  '/rankings': 'Classement UCAR',
  '/finance': 'Suivi financier',
  '/alertes': 'Alertes et conformité',
  '/reports': 'Rapports et analyses'
};

export function Topbar() {
  const location = useLocation();
  const isInstitutionDetail = location.pathname.startsWith('/institutions/');
  const title = isInstitutionDetail ? 'Fiche et pilotage institution' : (pageTitles[location.pathname] || 'Tableau de bord');

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 lg:px-8 flex items-center justify-between sticky top-0 z-40">
      <div className="flex flex-col">
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        <p className="text-xs text-slate-500 mt-0.5">Réseau Universitaire: TUNIS-CENTRAL</p>
      </div>

      <div className="flex items-center gap-6">
        <div className="hidden md:flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-xs font-medium text-slate-500">Stabilité réseau</span>
            <span className="text-sm font-semibold text-green-700 font-tabular">99.98% stable</span>
          </div>
          <div className="h-8 w-px bg-slate-200" />
        </div>

        <div className="flex items-center gap-4">
          <div className="relative hidden lg:block w-64">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input 
              type="text" 
              placeholder="Recherche système..."
              className="w-full bg-slate-50 border border-slate-300 rounded-md pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-blue-700 placeholder:text-slate-400"
            />
          </div>

          <button className="relative p-2 text-slate-600 hover:bg-slate-100 rounded-md transition-colors duration-150 border border-slate-200">
            <Bell size={18} />
            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white" />
          </button>

          <button className="p-2 text-slate-600 hover:bg-slate-100 rounded-md transition-colors duration-150 border border-slate-200">
            <User size={18} />
          </button>
          
          <button className="px-4 py-2 bg-blue-800 text-white rounded-md text-sm font-medium hover:bg-blue-900 transition-colors duration-150">
            Déployer Rapport
          </button>
        </div>
      </div>
    </header>
  );
}
