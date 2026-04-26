import { useState } from "react";
import { Search } from "lucide-react";
import { InstitutionType } from "@/src/types";
import { alerts, institutions } from "@/src/data/dashboardMock";
import { Badge } from "@/src/components/ui/StatusDot";
import { Link } from "react-router-dom";
import { cn } from "@/src/lib/utils";

export function Institutions() {
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState<InstitutionType | "all">("all");

  const filteredInstitutions = institutions.filter(inst => {
    const matchesSearch = inst.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          inst.code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === "all" || inst.type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Liste des établissements</h2>
          <p className="text-sm text-slate-600 mt-1">Gestion et supervision du réseau UCAR</p>
        </div>
        
        <div className="flex items-center gap-3">
          <Badge variant="good">{institutions.length} actifs</Badge>
          <Badge variant="warning">{alerts.filter((item) => item.status !== 'resolved').length} alertes</Badge>
        </div>
      </div>

      <div className="bg-white p-4 rounded-md flex flex-wrap items-center gap-4 border border-slate-200">
        <div className="relative flex-1 min-w-60">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text" 
            placeholder="Rechercher un établissement..."
            className="w-full bg-slate-50 border border-slate-300 rounded-md pl-10 pr-4 py-2 text-sm outline-none focus:border-blue-700"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-2">
          <select 
            className="bg-slate-50 border border-slate-300 rounded-md px-4 py-2 text-sm outline-none focus:border-blue-700 appearance-none pr-10 relative cursor-pointer"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as InstitutionType | 'all')}
          >
            <option value="all">Tous les types</option>
            <option value="grande_ecole">Grandes Écoles</option>
            <option value="faculte">Facultés</option>
            <option value="preparatoire">Classes Préparatoires</option>
          </select>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-base font-semibold text-slate-900">Registre des établissements</h3>
            <div className="flex items-center gap-4">
               <span className="text-sm text-slate-600">{filteredInstitutions.length} lignes</span>
            </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50">
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200">Rang</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200">Établissement</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200">Type</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200 text-right">Score UCAR</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200 text-right">Δ</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200 text-right">Alertes</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200 text-right">Conformité</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {filteredInstitutions.map((inst) => (
                <tr key={inst.code} className="hover:bg-slate-50 transition-colors duration-150">
                  <td className="px-6 py-4 text-sm font-bold text-slate-900 font-tabular">#{inst.rank}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className={cn('w-2 h-2 rounded-full', inst.globalHealth === 'good' ? 'bg-green-600' : inst.globalHealth === 'critical' ? 'bg-red-600' : 'bg-amber-500')} />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-slate-900">{inst.code}</span>
                        <span className="text-xs text-slate-500">{inst.name} · {inst.city}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <Badge variant={inst.type === 'grande_ecole' ? 'info' : (inst.type === 'faculte' ? 'purple' : 'amber')}>
                      {inst.type.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 text-sm text-right font-tabular font-semibold text-slate-900">{inst.ucarScore}</td>
                  <td className="px-6 py-4 text-sm text-right font-tabular">
                    <span className={cn('font-medium', inst.scoreDelta >= 0 ? 'text-green-700' : 'text-red-700')}>
                      {inst.scoreDelta >= 0 ? '+' : ''}{inst.scoreDelta}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-right font-tabular text-slate-700">{inst.alertsActive}</td>
                  <td className="px-6 py-4 text-sm text-right font-tabular text-slate-700">{inst.kpiSnapshot.documentControlCompliance}%</td>
                  <td className="px-6 py-4 text-right">
                    <Link 
                      to={`/institutions/${inst.code}`}
                      className="px-3 py-1.5 bg-blue-800 text-white text-sm font-medium rounded-md hover:bg-blue-900 transition-colors duration-150"
                    >
                      Analyser
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
