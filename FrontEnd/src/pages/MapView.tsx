import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import conventionsData from '@/src/data/conventions.json';
import institutionsData from '@/src/data/institutions.json';
import { cn } from '@/src/lib/utils';

type ConventionStatus = 'pending' | 'in_progress' | 'validated' | 'rejected';
type StepStatus = 'done' | 'in_progress' | 'todo';

interface Convention {
  id: string;
  institution_code: string;
  partner: string;
  type: string;
  submitted_on: string;
  due_date: string;
  status: ConventionStatus;
  delay_days: number;
  current_step: string;
  steps: Record<string, StepStatus>;
}

const statusLabel: Record<ConventionStatus, string> = {
  pending: 'En attente',
  in_progress: 'En cours',
  validated: 'Validee',
  rejected: 'Rejetee',
};

const statusClass: Record<ConventionStatus, string> = {
  pending: 'bg-amber-50 text-amber-700 border border-amber-200',
  in_progress: 'bg-blue-50 text-blue-800 border border-blue-200',
  validated: 'bg-green-50 text-green-800 border border-green-200',
  rejected: 'bg-red-50 text-red-700 border border-red-200',
};

export function MapView() {
  const conventions = conventionsData as Convention[];
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<ConventionStatus | 'all'>('all');

  const institutionMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const inst of institutionsData) {
      map.set(inst.code, inst.name);
    }
    return map;
  }, []);

  const filtered = conventions.filter((item) => {
    const matchesQuery =
      item.id.toLowerCase().includes(query.toLowerCase()) ||
      item.partner.toLowerCase().includes(query.toLowerCase()) ||
      item.institution_code.toLowerCase().includes(query.toLowerCase());
    const matchesStatus = status === 'all' || item.status === status;
    return matchesQuery && matchesStatus;
  });

  const delayedCount = conventions.filter((c) => c.delay_days > 0).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Gestion des conventions</h2>
          <p className="text-sm text-slate-600 mt-1">Workflow juridique et financier multi-etablissements</p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="px-2 py-1 bg-slate-100 text-slate-700 rounded border border-slate-200">{conventions.length} conventions</span>
          <span className="px-2 py-1 bg-red-50 text-red-700 rounded border border-red-200">{delayedCount} en retard</span>
        </div>
      </div>

      <section className="bg-white border border-slate-200 rounded-md p-4 flex flex-col lg:flex-row gap-3 lg:items-center lg:justify-between">
        <div className="relative w-full lg:w-80">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher convention, partenaire ou code"
            className="w-full border border-slate-300 rounded-md pl-9 pr-3 py-2 text-sm bg-slate-50 focus:outline-none focus:border-blue-700"
          />
        </div>
        <div className="flex items-center gap-2">
          <select
            className="border border-slate-300 bg-slate-50 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-blue-700"
            value={status}
            onChange={(e) => setStatus(e.target.value as ConventionStatus | 'all')}
          >
            <option value="all">Tous les statuts</option>
            <option value="pending">En attente</option>
            <option value="in_progress">En cours</option>
            <option value="validated">Validee</option>
            <option value="rejected">Rejetee</option>
          </select>
        </div>
      </section>

      <section className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Reference</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Etablissement</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Partenaire</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Type</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Etape en cours</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Statut</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Retard</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {filtered.map((item) => (
              <tr key={item.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 text-sm font-medium text-slate-900">{item.id}</td>
                <td className="px-4 py-3 text-sm text-slate-700">
                  <div className="flex flex-col">
                    <span className="font-medium text-slate-900">{item.institution_code}</span>
                    <span className="text-xs text-slate-500">{institutionMap.get(item.institution_code) || 'N/A'}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-slate-700">{item.partner}</td>
                <td className="px-4 py-3 text-sm text-slate-700">{item.type.replaceAll('_', ' ')}</td>
                <td className="px-4 py-3 text-sm text-slate-700">{item.current_step.replaceAll('_', ' ')}</td>
                <td className="px-4 py-3 text-sm">
                  <span className={cn('px-2 py-0.5 rounded text-xs font-medium', statusClass[item.status])}>
                    {statusLabel[item.status]}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-right font-tabular">
                  {item.delay_days > 0 ? <span className="text-red-700">{item.delay_days} j</span> : <span className="text-slate-600">0 j</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
