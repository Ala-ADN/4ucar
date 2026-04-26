import { institutions } from '@/src/data/dashboardMock';
import { cn } from '@/src/lib/utils';
import { Link } from 'react-router-dom';
import { Badge } from '@/src/components/ui/StatusDot';
import { Trophy } from 'lucide-react';

export function Rankings() {
  const sorted = [...institutions].sort((a, b) => a.rank - b.rank);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Classement UCAR</h2>
          <p className="text-sm text-slate-600 mt-1">Classement interne des 35 établissements par score composite UCAR</p>
        </div>
        <div className="flex items-center gap-2">
          <Trophy size={16} className="text-amber-500" />
          <span className="text-sm text-slate-600">Période en cours: S1 25-26</span>
        </div>
      </div>

      <section className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Rang</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Établissement</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Type</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Score UCAR</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Δ</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Académique</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Gouvernance</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Durabilité</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">RH</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {sorted.map((inst) => (
              <tr key={inst.code} className={cn('hover:bg-slate-50 transition-colors duration-150', inst.rank <= 3 && 'bg-blue-50/30')}>
                <td className="px-4 py-3">
                  <span className={cn(
                    'text-sm font-bold font-tabular',
                    inst.rank === 1 ? 'text-amber-600' : inst.rank === 2 ? 'text-slate-500' : inst.rank === 3 ? 'text-amber-800' : 'text-slate-700'
                  )}>#{inst.rank}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-slate-900">{inst.code}</span>
                    <span className="text-xs text-slate-500">{inst.city} · {inst.students.toLocaleString()} étudiants</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <Badge variant={inst.type === 'grande_ecole' ? 'info' : inst.type === 'faculte' ? 'purple' : 'amber'}>
                    {inst.type.replace('_', ' ')}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-sm text-right font-tabular font-bold text-slate-900">{inst.ucarScore}</td>
                <td className="px-4 py-3 text-sm text-right font-tabular">
                  <span className={cn('font-medium', inst.scoreDelta >= 0 ? 'text-green-700' : 'text-red-700')}>
                    {inst.scoreDelta >= 0 ? '+' : ''}{inst.scoreDelta}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-right font-tabular text-slate-700">{inst.domainScores.academic}</td>
                <td className="px-4 py-3 text-sm text-right font-tabular text-slate-700">{inst.domainScores.governance}</td>
                <td className="px-4 py-3 text-sm text-right font-tabular text-slate-700">{inst.domainScores.sustainability}</td>
                <td className="px-4 py-3 text-sm text-right font-tabular text-slate-700">{inst.domainScores.hr}</td>
                <td className="px-4 py-3 text-right">
                  <Link
                    to={`/institutions/${inst.code}`}
                    className="px-3 py-1.5 bg-blue-800 text-white text-sm font-medium rounded-md hover:bg-blue-900 transition-colors duration-150"
                  >
                    Détail
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
