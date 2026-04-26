import { School, AlertCircle, ShieldCheck, TrendingDown, Info, Calendar } from 'lucide-react';
import { KPICard } from '@/src/components/kpi/KPICard';
import { alerts, frameworkPosture, institutions, networkTrend, TOTAL_INSTITUTIONS } from '@/src/data/dashboardMock';
import { Badge } from '@/src/components/ui/StatusDot';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Link } from 'react-router-dom';
import { cn } from '@/src/lib/utils';
import { useState } from 'react';

/* ─── IPG Gauge ─────────────────────────────────────────────────────────── */

function IPGGauge({ value }: { value: number }) {
  const size = 120;
  const strokeWidth = 9;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = value / 100;
  const offset = circumference - pct * circumference;
  const [showFormula, setShowFormula] = useState(false);

  const scoreColor = value >= 80 ? '#16A34A' : value >= 65 ? '#1B4F8B' : '#EAB308';

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6 flex flex-col justify-between relative">
      <div className="flex justify-between items-start mb-3">
        <div>
          <div className="flex items-center gap-1.5">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-tight">
              Indice de Perf. Global (IPG)
            </h3>
            <button
              onMouseEnter={() => setShowFormula(true)}
              onMouseLeave={() => setShowFormula(false)}
              onClick={() => setShowFormula(!showFormula)}
              className="text-slate-400 hover:text-[#1B4F8B] transition-colors duration-150"
              aria-label="Voir la formule IPG"
            >
              <Info size={13} />
            </button>
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5 leading-tight max-w-[200px]">
            Moy. pondérée : Académique (40%), Finance (30%), RH (30%).
          </p>
        </div>
        <Badge variant="good">+0.4%</Badge>
      </div>

      {showFormula && (
        <div className="absolute top-[72px] left-4 right-4 z-20 bg-slate-900 text-white rounded-lg p-4 shadow-xl border border-slate-700">
          <div className="absolute -top-1.5 left-6 w-3 h-3 bg-slate-900 rotate-45 border-l border-t border-slate-700" />
          <p className="text-xs font-semibold text-blue-300 uppercase tracking-wider mb-2">
            Formule IPG
          </p>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            Moyenne pondérée des performances <span className="text-white font-medium">académiques (40%)</span>,
            de l'<span className="text-white font-medium">exécution budgétaire (30%)</span>,
            et de la <span className="text-white font-medium">capacité RH (30%)</span>.
          </p>
          <div className="mt-2.5 pt-2.5 border-t border-slate-700/60">
            <code className="text-[10px] text-blue-400 font-mono">
              IPG = 0.40 × Acad. + 0.30 × Finance + 0.30 × RH
            </code>
          </div>
        </div>
      )}

      <div className="flex items-center gap-5">
        <div className="relative" style={{ width: size, height: size }}>
          <svg width={size} height={size} className="-rotate-90">
            <circle
              cx={size / 2} cy={size / 2} r={radius}
              fill="none" stroke="#F1F5F9" strokeWidth={strokeWidth}
            />
            <circle
              cx={size / 2} cy={size / 2} r={radius}
              fill="none" stroke={scoreColor} strokeWidth={strokeWidth}
              strokeDasharray={circumference} strokeDashoffset={offset}
              strokeLinecap="round"
              className="gauge-ring"
              style={{ '--gauge-circumference': circumference } as React.CSSProperties}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold text-[#0F172A] tabular-nums tracking-tighter leading-none">
              {Math.round(value)}
            </span>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest mt-0.5">
              / 100
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-2.5 flex-1">
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-500">Objectif S1:</span>
            <span className="font-semibold text-slate-700 tabular-nums">80</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-500">Réseau:</span>
            <span className="font-semibold text-emerald-600">Conforme</span>
          </div>
          <div className="w-full h-px bg-slate-100 my-0.5" />
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-500">Δ Sem.:</span>
            <span className="font-semibold text-emerald-600 tabular-nums">+0.4</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Sparkline data derived from networkTrend ─── */

const ipgSparkline = networkTrend.map(t => t.ucarScore);
const alertSparkline = [14, 12, 9, 6]; // declining is good
const complianceSparkline = networkTrend.map(t => t.governance);

/* ─── Overview Page ─────────────────────────────────────────────────────── */

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

  const now = new Date();
  const dateStr = now.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });

  return (
    <div className="space-y-6">
      {/* ── Executive Header ── */}
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-xl font-semibold text-[#0F172A] tracking-tight">
            Vue d'ensemble — Réseau UCAR
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Année universitaire 2025-26 · Semestre 1
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Calendar size={14} />
          <span>{dateStr}</span>
        </div>
      </div>

      {/* ── KPI Row ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 items-stretch">
        <KPICard
          label="Établissements surveillés"
          value={TOTAL_INSTITUTIONS}
          icon={School}
          trend={{ value: 2, unit: '' }}
          sparkline={[28, 30, 32, 33, 34, 35]}
        />
        <IPGGauge value={medianUcarScore} />
        <KPICard
          label="Alertes actives"
          value={activeAlerts}
          icon={AlertCircle}
          badge={String(activeAlerts)}
          trend={{ value: -3, unit: '', isPositiveGood: false }}
          sparkline={alertSparkline}
        />
        <KPICard
          label="Conformité documentaire (GOV-01)"
          value={networkCompliance}
          suffix="%"
          icon={ShieldCheck}
          trend={{ value: 1.1, unit: '%' }}
          sparkline={complianceSparkline}
        />
      </div>

      {/* ── Main Charts Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Trend Chart */}
        <div className="lg:col-span-8 bg-white p-6 rounded-lg border border-slate-200">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Performance réseau — tendance</h2>
              <p className="text-sm text-slate-500 mt-1">Score IPG et domaines stratégiques (4 semestres)</p>
            </div>
            <button className="px-3 py-1.5 rounded-md border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 transition-colors duration-150">
              Exporter
            </button>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={networkTrend}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis
                  dataKey="period" axisLine={false} tickLine={false}
                  tick={{ fontSize: 12, fill: '#475569' }} dy={10}
                />
                <YAxis
                  axisLine={false} tickLine={false}
                  tick={{ fontSize: 12, fill: '#475569' }} unit="%"
                  domain={[60, 80]}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px', border: '1px solid #e2e8f0',
                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', fontSize: '12px',
                    fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
                  }}
                />
                <Line type="monotone" dataKey="ucarScore" stroke="#1B4F8B" strokeWidth={2.5} dot={{ r: 3, fill: '#1B4F8B', strokeWidth: 0 }} activeDot={{ r: 5 }} name="Score IPG" />
                <Line type="monotone" dataKey="academic" stroke="#0f766e" strokeWidth={1.5} strokeDasharray="5 5" name="Académique" />
                <Line type="monotone" dataKey="governance" stroke="#64748b" strokeWidth={1.5} strokeDasharray="5 5" name="Gouvernance" />
                <Line type="monotone" dataKey="hr" stroke="#b45309" strokeWidth={1.5} strokeDasharray="5 5" name="RH" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Accreditation Posture */}
        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-lg overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-sm font-semibold text-slate-900">Posture accréditation</h3>
            <ShieldCheck size={16} className="text-slate-400" />
          </div>
          <div className="divide-y divide-slate-200 bg-white">
            {frameworkPosture.map((item) => {
              const percentage = Math.round((item.passingControls / item.totalControls) * 100);
              return (
                <div key={item.framework} className="px-5 py-4 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-slate-900">{item.framework}</span>
                    <span className="text-xs text-slate-500 font-tabular">{percentage}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full transition-all duration-500', percentage >= 60 ? 'bg-[#1B4F8B]' : 'bg-amber-500')}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-500 font-tabular">
                    {item.passingControls} / {item.totalControls} contrôles
                  </p>
                </div>
              );
            })}
          </div>
          <div className="p-4 bg-slate-50 border-t border-slate-200">
            <p className="text-xs leading-relaxed text-slate-600">
              Progression calculée automatiquement selon les preuves documentaires et KPI validés.
            </p>
          </div>
        </div>
      </div>

      {/* ── Anomalies ── */}
      {anomalies.length > 0 && (
        <section className="bg-white border border-slate-200 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
            <TrendingDown size={16} className="text-red-600" />
            <h2 className="text-sm font-semibold text-slate-900">Anomalies détectées — plus fortes baisses</h2>
          </div>
          <div className="divide-y divide-slate-100">
            {anomalies.map((inst) => (
              <div key={inst.code} className="px-6 py-4 flex items-center justify-between hover:bg-slate-50/60 transition-colors duration-150">
                <div className="flex items-center gap-4">
                  <div className={cn('w-2.5 h-2.5 rounded-full shrink-0', inst.globalHealth === 'critical' ? 'bg-red-600' : 'bg-amber-500')} />
                  <div>
                    <Link to={`/institutions/${inst.code}`} className="text-sm font-medium text-slate-900 hover:text-[#1B4F8B] transition-colors duration-100">{inst.code}</Link>
                    <p className="text-xs text-slate-500">{inst.name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm font-semibold text-slate-900 font-tabular">{inst.ucarScore}</p>
                    <p className="text-xs text-slate-500">Score IPG</p>
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

      {/* ── Leaderboard ── */}
      <section className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900">Classement des établissements</h2>
          <Link to="/rankings" className="text-sm text-[#1B4F8B] hover:text-[#153d6e] transition-colors duration-150">
            Voir le classement complet →
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr>
                <th className="px-6 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Rang</th>
                <th className="px-6 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Établissement</th>
                <th className="px-6 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Score IPG</th>
                <th className="px-6 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Δ</th>
                <th className="px-6 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Réussite</th>
                <th className="px-6 py-3 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Conformité</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {topInstitutions.map((institution) => (
                <tr key={institution.code} className="hover:bg-slate-50/60 transition-colors duration-100">
                  <td className="px-6 py-3.5 text-sm font-semibold text-slate-900 font-tabular">#{institution.rank}</td>
                  <td className="px-6 py-3.5 text-sm text-slate-900">
                    <Link to={`/institutions/${institution.code}`} className="hover:text-[#1B4F8B]">
                      <div className="flex flex-col">
                        <span className="font-medium">{institution.code}</span>
                        <span className="text-xs text-slate-500">{institution.city}</span>
                      </div>
                    </Link>
                  </td>
                  <td className="px-6 py-3.5 text-sm text-slate-700">
                    <Badge variant={institution.type === 'grande_ecole' ? 'info' : institution.type === 'faculte' ? 'purple' : 'amber'}>
                      {institution.type.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="px-6 py-3.5 text-sm text-slate-900 text-right font-tabular font-semibold">{institution.ucarScore}</td>
                  <td className="px-6 py-3.5 text-sm text-right font-tabular">
                    <span className={institution.scoreDelta >= 0 ? 'text-green-700' : 'text-red-700'}>
                      {institution.scoreDelta >= 0 ? '+' : ''}{institution.scoreDelta}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 text-sm text-slate-900 text-right font-tabular">{institution.kpiSnapshot.successRate}%</td>
                  <td className="px-6 py-3.5 text-sm text-slate-900 text-right font-tabular">{institution.kpiSnapshot.documentControlCompliance}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
