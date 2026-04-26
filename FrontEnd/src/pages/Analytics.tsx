import { useMemo, useState } from 'react';
import kpiData from '@/src/data/kpis.json';

const options = [
  { key: 'taux_reussite', label: 'Taux de reussite' },
  { key: 'taux_abandon', label: 'Taux d abandon' },
  { key: 'budget_execution', label: 'Budget execute' },
] as const;

type KpiKey = (typeof options)[number]['key'];

export function Analytics() {
  const [selected, setSelected] = useState<KpiKey>('taux_reussite');

  const rows = useMemo(() => {
    const entries = Object.entries(kpiData) as Array<[string, any]>;
    return entries.map(([code, value]) => {
      const series = value[selected] as number[];
      const current = series[series.length - 1] ?? 0;
      const previous = series[series.length - 2] ?? current;
      return {
        code,
        current,
        delta: Number((current - previous).toFixed(1)),
      };
    });
  }, [selected]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Rapports et analyses</h2>
          <p className="text-sm text-slate-600 mt-1">Lecture consolidee des evolutions KPI sur 6 semestres</p>
        </div>
        <div>
          <select
            className="border border-slate-300 bg-slate-50 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-blue-700"
            value={selected}
            onChange={(e) => setSelected(e.target.value as KpiKey)}
          >
            {options.map((opt) => (
              <option key={opt.key} value={opt.key}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      <section className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Etablissement</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Semestres observes</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Valeur actuelle</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Variation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {rows.map((row) => (
              <tr key={row.code} className="hover:bg-slate-50">
                <td className="px-4 py-3 text-sm font-medium text-slate-900">{row.code}</td>
                <td className="px-4 py-3 text-sm text-slate-700">6</td>
                <td className="px-4 py-3 text-sm text-right font-tabular text-slate-900">{row.current}%</td>
                <td className="px-4 py-3 text-sm text-right font-tabular">
                  <span className={row.delta >= 0 ? 'text-green-700' : 'text-red-700'}>
                    {row.delta >= 0 ? '+' : ''}{row.delta}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
