import { useMemo, useState } from 'react';
import { institutionKpiSeries } from '@/src/data/dashboardMock';

const options = [
  { key: 'successRate', label: 'Taux de réussite (ACA-02)' },
  { key: 'curriculumCoverage', label: 'Couverture programme (ACA-05)' },
  { key: 'workloadCompliance', label: 'Conformité charge (HR-01)' },
  { key: 'documentControlCompliance', label: 'Conformité documentaire (GOV-01)' },
  { key: 'dropoutRate', label: 'Taux d\'abandon (ACA-03)' },
] as const;

type KpiKey = (typeof options)[number]['key'];

export function Analytics() {
  const [selected, setSelected] = useState<KpiKey>('successRate');

  const rows = useMemo(() => {
    const entries = Object.entries(institutionKpiSeries);
    return entries.map(([code, value]) => {
      const series = value[selected] as number[];
      const current = series[series.length - 1] ?? 0;
      const previous = series[series.length - 2] ?? current;
      return {
        code,
        periods: value.periods,
        series,
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
          <p className="text-sm text-slate-600 mt-1">Lecture consolidée des évolutions KPI sur 4 semestres</p>
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
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Établissement</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Semestres observés</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Valeur actuelle</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Variation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {rows.map((row) => (
              <tr key={row.code} className="hover:bg-slate-50">
                <td className="px-4 py-3 text-sm font-medium text-slate-900">{row.code}</td>
                <td className="px-4 py-3 text-sm text-slate-700">{row.periods.length}</td>
                <td className="px-4 py-3 text-sm text-right font-tabular text-slate-900">
                  {selected === 'dropoutRate' || selected === 'successRate' || selected === 'curriculumCoverage' || selected === 'workloadCompliance' || selected === 'documentControlCompliance' 
                    ? `${row.current}%` 
                    : row.current}
                </td>
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
