import { useState } from "react";
import { Search, Filter, ArrowUpRight, AlertCircle, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { Institution, InstitutionType } from "@/src/types";
import institutionsData from "@/src/data/institutions.json";
import { Badge, StatusDot } from "@/src/components/ui/StatusDot";
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
          <h2 className="text-xl font-bold text-text-primary">Liste des établissements</h2>
          <p className="text-sm text-text-muted mt-1">Gérez et surveillez l'ensemble du réseau UCAR</p>
        </div>
        
        <div className="flex items-center gap-3">
          <Badge variant="good">35 actifs</Badge>
          <Badge variant="warning">12 alertes</Badge>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-surface p-4 rounded-xl shadow-card flex flex-wrap items-center gap-4 border border-border">
        <div className="relative flex-1 min-w-[240px]">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input 
            type="text" 
            placeholder="Rechercher un établissement..."
            className="w-full bg-off-white border-none rounded-lg pl-10 pr-4 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-2">
          <select 
            className="bg-off-white border-none rounded-lg px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500/20 appearance-none pr-10 relative cursor-pointer"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as any)}
          >
            <option value="all">Tous les types</option>
            <option value="grande_ecole">Grandes Écoles</option>
            <option value="faculte">Facultés</option>
            <option value="preparatoire">Classes Préparatoires</option>
          </select>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-text-secondary hover:bg-surface-hover rounded-lg transition-colors">
          <Filter size={16} /> Filters
        </button>
      </div>

      {/* Table container */}
      <div className="bg-slate-50 border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="bg-white px-8 py-5 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600">Registre des Établissements</h3>
            <div className="flex items-center gap-4">
               <span className="text-[10px] font-bold text-blue-600 border-b border-blue-600 cursor-pointer">EXPORTER DATA</span>
            </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50">
                <th className="px-8 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200">ID Système</th>
                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200">Établissement</th>
                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200">Type</th>
                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200 text-center">Score</th>
                <th className="px-8 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              <AnimatePresence mode="popLayout">
                {filteredInstitutions.map((inst, idx) => (
                  <motion.tr 
                    key={inst.code}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ delay: idx * 0.02 }}
                    className="hover:bg-slate-50/80 transition-colors group"
                  >
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-3">
                         <div className={cn("w-2 h-2 rounded-full", inst.global_health === 'good' ? 'bg-green-500' : 'bg-amber-500')} />
                         <span className="text-xs font-mono bg-slate-100 px-2 py-1 rounded text-slate-600 font-bold">{inst.code}</span>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex flex-col">
                        <span className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">{inst.name}</span>
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-tight">{inst.city}</span>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <Badge variant={inst.type === 'grande_ecole' ? 'info' : (inst.type === 'faculte' ? 'purple' : 'amber')}>
                        {inst.type.replace('_', ' ')}
                      </Badge>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex justify-center">
                        <ScoreValue value={inst.kpi_snapshot?.taux_reussite ?? 0} />
                      </div>
                    </td>
                    <td className="px-8 py-5 text-right">
                      <Link 
                        to={`/institutions/${inst.code}`}
                        className="px-4 py-2 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-slate-800 transition-all opacity-0 group-hover:opacity-100"
                      >
                        ANALYSER
                      </Link>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
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
      <span className="text-sm font-bold text-slate-900 font-tabular">{value}%</span>
      <div className="w-16 h-1 bg-slate-100 rounded-full overflow-hidden">
        <div 
          className={cn("h-full rounded-full transition-all duration-1000", value > 80 ? "bg-green-500" : "bg-blue-500")} 
          style={{ width: `${value}%` }} 
        />
      </div>
    </div>
  );
}
