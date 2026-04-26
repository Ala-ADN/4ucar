import { Bell, Search } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const pageTitles: Record<string, string> = {
  '/': 'Tableau de Bord',
  '/institutions': 'Carte du Réseau',
  '/accreditations': 'Accréditations & Conformité',
  '/rankings': 'Classement UCAR',
  '/finance': 'Finances',
  '/alertes': 'Centre d\'Opérations',
  '/reports': 'Rapports & Synthèses IA'
};

export function Topbar() {
  const location = useLocation();
  const isInstitutionDetail = location.pathname.startsWith('/institutions/');
  const title = isInstitutionDetail
    ? 'Fiche institution'
    : (pageTitles[location.pathname] || 'UCAR');

  return (
    <header className="h-14 bg-white border-b border-slate-200 px-6 lg:px-8 flex items-center justify-between sticky top-0 z-40">
      <div>
        <h1 className="text-base font-semibold text-[#0F172A]">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative hidden lg:block w-56">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Rechercher..."
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-1.5 text-sm outline-none focus:border-[#1d5394] placeholder:text-slate-400 transition-colors duration-100"
          />
        </div>

        <button className="relative p-2 text-slate-500 hover:bg-slate-50 rounded-lg transition-colors duration-100">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white" />
        </button>

        <div className="h-8 w-8 rounded-full bg-[#1d5394] flex items-center justify-center text-white text-xs font-semibold">
          BS
        </div>
      </div>
    </header>
  );
}
