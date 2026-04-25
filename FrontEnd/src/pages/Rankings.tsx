import { Trophy, TrendingUp, TrendingDown, Minus, Users } from "lucide-react";
import { useState } from "react";
import { Institution } from "@/src/types";
import institutionsData from "@/src/data/institutions.json";
import { cn } from "@/src/lib/utils";

export function Rankings() {
  const [mode, setMode] = useState<'national' | 'intl'>('national');
  const institutions = (institutionsData as Institution[]).sort((a, b) => (b.ranking_national || 100) - (a.ranking_national || 100)).reverse();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Classements des etablissements</h2>
          <p className="text-sm text-slate-600 mt-1">Production d'etudes comparatives 2024</p>
        </div>
        
        <div className="flex bg-white p-1 border border-slate-300 rounded-md">
          <button 
            onClick={() => setMode('national')}
            className={cn('px-4 py-1.5 rounded text-sm font-medium transition-colors duration-150', mode === 'national' ? 'bg-blue-800 text-white' : 'text-slate-700 hover:bg-slate-100')}
          >
            National
          </button>
          <button 
            onClick={() => setMode('intl')}
            className={cn('px-4 py-1.5 rounded text-sm font-medium transition-colors duration-150', mode === 'intl' ? 'bg-blue-800 text-white' : 'text-slate-700 hover:bg-slate-100')}
          >
            International
          </button>
        </div>
      </div>

      {mode === 'national' ? (
        <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-base font-semibold text-slate-900">Index de performance tunisien</h3>
            <span className="text-sm text-slate-600">Derniere sync: 14:02 UTC</span>
          </div>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50">
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200 text-center w-24">Rang</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200">Etablissement</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200">Score</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200 text-center">Statut domaines</th>
                <th className="px-6 py-3 text-xs font-semibold text-slate-700 border-b border-slate-200 text-right">Momentum</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {institutions.map((inst, idx) => (
                <tr key={inst.code} className="hover:bg-slate-50 transition-colors duration-150">
                  <td className={cn(
                    'px-6 py-4 text-center font-semibold font-tabular text-base',
                    idx === 0 ? 'text-amber-700 bg-amber-50' :
                    idx === 1 ? 'text-slate-600 bg-slate-50' :
                    idx === 2 ? 'text-amber-800 bg-amber-50/50' : 'text-slate-500'
                  )}>
                    {idx + 1}
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 font-mono text-xs font-medium">
                        {inst.code}
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-slate-900">{inst.name}</span>
                        <span className="text-xs text-slate-500">{inst.city}</span>
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
                         'text-xs font-medium',
                         idx < 3 ? 'text-green-700' : (idx > 12 ? 'text-red-700' : 'text-slate-500')
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <IntlMetric icon={Users} label="Partenariats actifs" value="142" suffix="Accords" trend="+12.4%" />
          <IntlMetric icon={TrendingUp} label="Mobilité sortante" value="850" suffix="Étudiants" trend="+24.2%" />
          <IntlMetric icon={Trophy} label="Publications" value="2.4k" suffix="Articles" trend="+8.1%" />
          <div className="md:col-span-3 bg-white p-12 rounded-md border border-slate-200 border-dashed text-center">
             <Trophy size={40} className="mx-auto text-slate-400 mb-4" />
             <p className="text-slate-600 font-medium text-sm">Donnees internationales en synchronisation (THE/QS)</p>
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
       <span className="text-xs font-semibold text-slate-900 tabular-nums">{score}</span>
       <span className="text-[10px] font-medium text-slate-500">/100</span>
       </div>
       <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div 
         className={cn("h-full rounded-full", score > 80 ? "bg-blue-700" : "bg-slate-700")} 
             style={{ width: `${score}%` }} 
          />
       </div>
    </div>
  );
}

function ScoreDot({ status, label }: { status: string, label: string }) {
  const color = status === 'good' ? 'bg-green-600' : (status === 'warning' ? 'bg-amber-500' : 'bg-red-600');
  return (
    <div className="flex flex-col items-center gap-1.5" title={label}>
      <div className={cn("w-2 h-2 rounded-full", color)} />
      <span className="text-[10px] font-medium text-slate-500">{label}</span>
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
    <div className="bg-white p-6 rounded-md border border-slate-200">
      <div className="flex justify-between items-start mb-6">
        <div className="p-2 bg-slate-100 border border-slate-200 rounded text-slate-700">
          <Icon size={20} />
        </div>
        <span className="text-xs font-medium text-green-800 bg-green-50 px-2 py-1 rounded border border-green-100">{trend}</span>
      </div>
      <h3 className="text-sm font-medium text-slate-700">{label}</h3>
      <div className="flex items-baseline gap-2 mt-2">
        <span className="text-3xl font-semibold text-slate-900 tabular-nums">{value}</span>
        <span className="text-xs font-medium text-slate-600">{suffix}</span>
      </div>
    </div>
  );
}
