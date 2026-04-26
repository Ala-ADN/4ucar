import { School, CheckCircle2, AlertCircle, ShieldCheck, TrendingDown } from 'lucide-react';
import { KPICard } from '@/src/components/kpi/KPICard';
import { alerts, frameworkPosture, institutions, networkTrend, TOTAL_INSTITUTIONS } from '@/src/data/dashboardMock';
import { Badge } from '@/src/components/ui/StatusDot';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Link } from 'react-router-dom';
import { cn } from '@/src/lib/utils';

export function Overview() {
  const medianUcarScore = Number(
    (institutions.reduce((sum, inst) => sum + inst.ucarScore, 0) / institutions.length).toFixed(1)
  );
  const activeAlerts = alerts.filter((item) => item.status !== 'resolved').length;
  const networkCompliance = Number(
    (
      institutions.reduce((sum, inst) => sum + inst.kpiSnapshot.documentControlCompliance, 0) / institutions.length
    ).toFixed(1)
  );
  const topInstitutions = [...institutions].sort((a, b) => a.rank - b.rank).slice(0, 8);
  const anomalies = [...institutions].sort((a, b) => a.scoreDelta - b.scoreDelta).slice(0, 5).filter(i => i.scoreDelta < 0);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard 
          label="Établissements surveillés" 
          value={TOTAL_INSTITUTIONS} 
          icon={School} 
          trend={{ value: 2, unit: '' }}
        />
        <KPICard 
          label="Score UCAR réseau" 
          value={medianUcarScore} 
          icon={CheckCircle2} 
          trend={{ value: 0.4, unit: '%' }}
        />
        <KPICard 
          label="Alertes actives" 
          value={activeAlerts} 
          icon={AlertCircle} 
          badge={String(activeAlerts)}
          trend={{ value: -3, unit: '', isPositiveGood: false }}
        />
        <KPICard 
          label="Conformité documentaire (GOV-01)" 
          value={networkCompliance} 
          suffix="%" 
          icon={ShieldCheck} 
          trend={{ value: 1.1, unit: '%' }}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-8 bg-white p-6 rounded-md border border-slate-200">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Performance réseau — tendance</h2>
              <p className="text-sm text-slate-600 mt-1">Score UCAR et domaines stratégiques (4 semestres)</p>
            </div>
            <button className="px-3 py-1.5 rounded border border-slate-300 text-sm text-slate-700 hover:bg-slate-50 transition-colors duration-150">
              Exporter
            </button>
          </div>

          <div className="h-70 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={networkTrend}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis 
                  dataKey="period" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 12, fill: '#475569' }} 
                  dy={10}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 12, fill: '#475569' }} 
                  unit="%"
                  domain={[60, 80]}
                />
                <Tooltip 
                  contentStyle={{ 
                    borderRadius: '6px', 
                    border: '1px solid #e2e8f0', 
                    boxShadow: 'none',
                    fontSize: '12px'
                  }} 
                />
                <Line type="monotone" dataKey="ucarScore" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 3, fill: '#2563eb', strokeWidth: 0 }} activeDot={{ r: 4 }} name="Score UCAR" />
                <Line type="monotone" dataKey="academic" stroke="#0f766e" strokeWidth={1.5} strokeDasharray="5 5" name="Académique" />
                <Line type="monotone" dataKey="governance" stroke="#64748b" strokeWidth={1.5} strokeDasharray="5 5" name="Gouvernance" />
                <Line type="monotone" dataKey="hr" stroke="#b45309" strokeWidth={1.5} strokeDasharray="5 5" name="RH" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-sm font-semibold text-slate-900">Posture accréditation</h3>
            <ShieldCheck size={16} className="text-slate-500" />
          </div>
          <div className="divide-y divide-slate-200 bg-white">
            {frameworkPosture.map((item) => {
              const percentage = Math.round((item.passingControls / item.totalControls) * 100);
              return (
                <div key={item.framework} className="px-4 py-3 space-y-1.5">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-slate-900">{item.framework}</span>
                    <span className="text-xs text-slate-500 font-tabular">{percentage}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className={cn('h-full rounded-full', percentage >= 60 ? 'bg-blue-700' : 'bg-amber-500')} style={{ width: `${percentage}%` }} />
                  </div>
                  <p className="text-xs text-slate-500 font-tabular">
                    {item.passingControls} / {item.totalControls} contrôles
                  </p>
                </div>
              );
            })}
          </div>
          <div className="mt-auto p-4 bg-slate-50 border-t border-slate-200">
            <p className="text-xs leading-relaxed text-slate-700">
              La progression de conformité est calculée automatiquement selon les preuves documentaires et KPI validés.
            </p>
          </div>
        </div>
      </div>

      {/* Top-5 Anomalies */}
      {anomalies.length > 0 && (
        <section className="bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-2">
            <TrendingDown size={16} className="text-red-600" />
            <h2 className="text-base font-semibold text-slate-900">Anomalies détectées — plus fortes baisses</h2>
          </div>
          <div className="divide-y divide-slate-200">
            {anomalies.map((inst) => (
              <div key={inst.code} className="px-4 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors duration-150">
                <div className="flex items-center gap-4">
                  <div className={cn('w-2.5 h-2.5 rounded-full', inst.globalHealth === 'critical' ? 'bg-red-600' : 'bg-amber-500')} />
                  <div>
                    <Link to={`/institutions/${inst.code}`} className="text-sm font-medium text-slate-900 hover:text-blue-800">{inst.code}</Link>
                    <p className="text-xs text-slate-500">{inst.name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm font-semibold text-slate-900 font-tabular">{inst.ucarScore}</p>
                    <p className="text-xs text-slate-500">Score UCAR</p>
                  </div>
                  <span className="text-sm font-semibold text-red-700 font-tabular bg-red-50 px-2 py-0.5 rounded">
                    {inst.scoreDelta}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Institution Leaderboard Table */}
      <section className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Classement des établissements</h2>
          <Link to="/rankings" className="text-sm text-blue-800 hover:text-blue-900 transition-colors duration-150">
            Voir le classement complet
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700">Rang</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700">Établissement</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700">Type</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Score UCAR</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Δ</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Réussite (ACA-02)</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Conformité (GOV-01)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {topInstitutions.map((institution) => (
                <tr key={institution.code} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-sm font-semibold text-slate-900 font-tabular">#{institution.rank}</td>
                  <td className="px-4 py-3 text-sm text-slate-900">
                    <Link to={`/institutions/${institution.code}`} className="hover:text-blue-800">
                      <div className="flex flex-col">
                        <span className="font-medium">{institution.code}</span>
                        <span className="text-xs text-slate-500">{institution.city}</span>
                      </div>
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-700">
                    <Badge variant={institution.type === 'grande_ecole' ? 'info' : institution.type === 'faculte' ? 'purple' : 'amber'}>
                      {institution.type.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-900 text-right font-tabular font-semibold">{institution.ucarScore}</td>
                  <td className="px-4 py-3 text-sm text-right font-tabular">
                    <span className={institution.scoreDelta >= 0 ? 'text-green-700' : 'text-red-700'}>
                      {institution.scoreDelta >= 0 ? '+' : ''}{institution.scoreDelta}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-900 text-right font-tabular">{institution.kpiSnapshot.successRate}%</td>
                  <td className="px-4 py-3 text-sm text-slate-900 text-right font-tabular">{institution.kpiSnapshot.documentControlCompliance}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
