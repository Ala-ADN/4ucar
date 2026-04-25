import { Trophy, TrendingUp, TrendingDown, Minus, Info, Users } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { Institution } from "@/src/types";
import institutionsData from "@/src/data/institutions.json";
import { cn } from "@/src/lib/utils";
import { Badge } from "@/src/components/ui/StatusDot";

export function Rankings() {
  const [mode, setMode] = useState<'national' | 'intl'>('national');
  const institutions = (institutionsData as Institution[]).sort((a, b) => (b.ranking_national || 100) - (a.ranking_national || 100)).reverse();

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Classements des Établissements</h2>
          <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-1">Production d'Études Comparatives 2024</p>
        </div>
        
        <div className="flex bg-slate-900 p-1.5 rounded-xl shadow-lg shadow-slate-900/10">
          <button 
            onClick={() => setMode('national')}
            className={cn("px-6 py-2.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all", mode === 'national' ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white")}
          >
            National
          </button>
          <button 
            onClick={() => setMode('intl')}
            className={cn("px-6 py-2.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all", mode === 'intl' ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white")}
          >
            International
          </button>
        </div>
      </div>

      {mode === 'national' ? (
        <div className="bg-slate-50 border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
          <div className="bg-white px-8 py-5 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600">Index de Performance Tunisien</h3>
            <span className="text-[10px] font-bold text-slate-400">DERNIÈRE SYNC: 14:02 UTC</span>
          </div>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50">
                <th className="px-8 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200 text-center w-24">Rang</th>
                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200">Établissement</th>
                <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200">Score HQ</th>
                <th className="px-4 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200 text-center">Status Domaines</th>
                <th className="px-8 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200 text-right">Momentum</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {institutions.map((inst, idx) => (
                <tr key={inst.code} className="hover:bg-slate-50/80 transition-colors group">
                  <td className={cn(
                    "px-8 py-5 text-center font-bold font-tabular text-xl",
                    idx === 0 ? "text-amber-600 bg-amber-50/30" : 
                    idx === 1 ? "text-slate-500 bg-slate-50/50" :
                    idx === 2 ? "text-amber-800 bg-amber-50/10" : "text-slate-300"
                  )}>
                    {idx + 1}
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400 font-mono text-[9px] font-bold shadow-sm group-hover:border-blue-200 group-hover:text-blue-600 transition-all">
                        {inst.code}
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">{inst.name}</span>
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-tight">{inst.city}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <ScoreBadge score={92 - idx * 4} />
                  </td>
                  <td className="px-4 py-5">
                    <div className="flex justify-center gap-3">
                      <ScoreDot status={inst.health.academic} label="Acad." />
                      <ScoreDot status={inst.health.financial} label="Fin." />
                      <ScoreDot status={inst.health.hr} label="RH" />
                      <ScoreDot status={inst.health.research} label="Rech." />
                    </div>
                  </td>
                  <td className="px-8 py-5 text-right">
                    <div className="flex items-center justify-end gap-2 pr-2">
                       <span className={cn(
                         "text-[10px] font-black uppercase tracking-tighter",
                         idx < 3 ? "text-green-600" : (idx > 12 ? "text-red-500" : "text-slate-400")
                       )}>
                         {idx < 3 ? 'BULLISH' : (idx > 12 ? 'BEARISH' : 'STABLE')}
                       </span>
                       <TrendIcon trend={idx < 3 ? 'up' : (idx > 12 ? 'down' : 'stable')} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <IntlMetric icon={Users} label="Partenariats actifs" value="142" suffix="Accords" trend="+12.4%" />
          <IntlMetric icon={TrendingUp} label="Mobilité sortante" value="850" suffix="Étudiants" trend="+24.2%" />
          <IntlMetric icon={Trophy} label="Publications" value="2.4k" suffix="Articles" trend="+8.1%" />
          <div className="md:col-span-3 bg-white p-20 rounded-2xl border border-slate-200 border-dashed text-center shadow-inner bg-slate-50/30">
             <Trophy size={48} className="mx-auto text-slate-200 mb-6" />
             <p className="text-slate-400 font-bold uppercase tracking-[0.2em] text-xs">Données Internationales en synchronisation (THE/QS)</p>
          </div>
        </div>
      )}
    </div>
  );
}

function ScoreBadge({ score }: { score: number }) {
  return (
    <div className="flex flex-col gap-1.5">
       <div className="flex justify-between items-center w-24">
          <span className="text-xs font-bold text-slate-900 tabular-nums">{score}</span>
          <span className="text-[9px] font-black text-slate-400">/100</span>
       </div>
       <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div 
             className={cn("h-full rounded-full transition-all duration-1000", score > 80 ? "bg-blue-600" : "bg-slate-900")} 
             style={{ width: `${score}%` }} 
          />
       </div>
    </div>
  );
}

function ScoreDot({ status, label }: { status: string, label: string }) {
  const color = status === 'good' ? "bg-green-500" : (status === 'warning' ? "bg-amber-500" : "bg-red-500");
  return (
    <div className="flex flex-col items-center gap-1.5" title={label}>
      <div className={cn("w-2 h-2 rounded-full", color)} />
      <span className="text-[8px] font-bold text-slate-300 uppercase tracking-tighter">{label}</span>
    </div>
  );
}

function TrendIcon({ trend }: { trend: 'up' | 'down' | 'stable' }) {
  if (trend === 'up') return <TrendingUp size={14} className="text-green-600" />;
  if (trend === 'down') return <TrendingDown size={14} className="text-red-500" />;
  return <Minus size={14} className="text-slate-300" />;
}

function IntlMetric({ icon: Icon, label, value, suffix, trend }: { icon: any, label: string, value: string, suffix: string, trend: string }) {
  return (
    <motion.div 
      whileHover={{ y: -4 }}
      className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200"
    >
      <div className="flex justify-between items-start mb-6">
        <div className="p-3 bg-blue-50 border border-blue-100 rounded-xl text-blue-600">
          <Icon size={24} />
        </div>
        <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded tracking-tighter">{trend}</span>
      </div>
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">{label}</h3>
      <div className="flex items-baseline gap-2 mt-2">
        <span className="text-4xl font-bold text-slate-900 tabular-nums">{value}</span>
        <span className="text-xs font-bold text-slate-500 uppercase tracking-tighter">{suffix}</span>
      </div>
    </motion.div>
  );
}
