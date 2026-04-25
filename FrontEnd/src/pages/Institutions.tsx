import { useState } from "react";
import { Search, Filter } from "lucide-react";
import { Institution, InstitutionType } from "@/src/types";
import institutionsData from "@/src/data/institutions.json";
import { Badge } from "@/src/components/ui/StatusDot";
import { Link } from "react-router-dom";
import { cn } from "@/src/lib/utils";

export function Institutions() {
  const institutions = institutionsData as Institution[];
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
          <h2 className="text-xl font-semibold text-slate-900">Liste des etablissements</h2>
          <p className="text-sm text-slate-600 mt-1">Gestion et supervision du reseau UCAR</p>
        </div>
        
        <div className="flex items-center gap-3">
          <Badge variant="good">35 actifs</Badge>
          <Badge variant="warning">12 alertes</Badge>
        </div>
      </div>

      <div className="bg-white p-4 rounded-md flex flex-wrap items-center gap-4 border border-slate-200">
        <div className="relative flex-1 min-w-[240px]">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text" 
            placeholder="Rechercher un etablissement..."
            className="w-full bg-slate-50 border border-slate-300 rounded-md pl-10 pr-4 py-2 text-sm outline-none focus:border-blue-700"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-2">
          <select 
            className="bg-slate-50 border border-slate-300 rounded-md px-4 py-2 text-sm outline-none focus:border-blue-700 appearance-none pr-10 relative cursor-pointer"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as any)}
          >
            <option value="all">Tous les types</option>
            <option value="grande_ecole">Grandes Écoles</option>
            <option value="faculte">Facultés</option>
            <option value="preparatoire">Classes Préparatoires</option>
          </select>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-md transition-colors duration-150 border border-slate-200">
          <Filter size={16} /> Filters
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-base font-semibold text-slate-900">Registre des etablissements</h3>
            <div className="flex items-center gap-4">
               <span className="text-sm text-blue-800 border-b border-blue-800 cursor-pointer">Exporter</span>
            </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50">
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200">ID systeme</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200">Etablissement</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200">Type</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200 text-center">Score</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {filteredInstitutions.map((inst) => (
                <tr key={inst.code} className="hover:bg-slate-50 transition-colors duration-150">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className={cn('w-2 h-2 rounded-full', inst.global_health === 'good' ? 'bg-green-600' : 'bg-amber-500')} />
                        <span className="text-xs font-medium bg-slate-100 px-2 py-1 rounded text-slate-700">{inst.code}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-slate-900">{inst.name}</span>
                      <span className="text-xs text-slate-500">{inst.city}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <Badge variant={inst.type === 'grande_ecole' ? 'info' : (inst.type === 'faculte' ? 'purple' : 'amber')}>
                      {inst.type.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex justify-center">
                      <ScoreValue value={inst.kpi_snapshot?.taux_reussite ?? 0} />
                    </div>
                  </td>
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

function ScoreValue({ value }: { value: number }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-sm font-semibold text-slate-900 font-tabular">{value}%</span>
      <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div 
          className={cn("h-full rounded-full", value > 80 ? "bg-green-600" : "bg-blue-700")} 
          style={{ width: `${value}%` }} 
        />
      </div>
    </div>
  );
}
