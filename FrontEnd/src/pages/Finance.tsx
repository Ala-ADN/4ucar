import { institutions } from '@/src/data/dashboardMock';
import { cn } from '@/src/lib/utils';
import { Wallet, TrendingUp, AlertTriangle, Users, Briefcase, GraduationCap, Calendar, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

/* ─── Segmented Bar ─── */

function SegmentedBar({ allocated, engaged, mandated, paid }: {
  allocated: number;
  engaged: number;
  mandated: number;
  paid: number;
}) {
  const total = allocated || 1;
  const pctPaid = (paid / total) * 100;
  const pctMandated = (mandated / total) * 100;
  const pctEngaged = (engaged / total) * 100;

  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden flex">
        <div
          className="h-full bg-[#1B4F8B] transition-all duration-300"
          style={{ width: `${pctPaid}%` }}
          title={`Payé: ${pctPaid.toFixed(0)}%`}
        />
        <div
          className="h-full bg-[#4A7DC0] transition-all duration-300"
          style={{ width: `${Math.max(0, pctMandated - pctPaid)}%` }}
          title={`Mandaté: ${(pctMandated - pctPaid).toFixed(0)}%`}
        />
        <div
          className="h-full bg-[#87A6C7] transition-all duration-300"
          style={{ width: `${Math.max(0, pctEngaged - pctMandated)}%` }}
          title={`Engagé: ${(pctEngaged - pctMandated).toFixed(0)}%`}
        />
      </div>
      <span className="text-xs text-slate-500 tabular-nums w-12 text-right">{pctPaid.toFixed(0)}%</span>
    </div>
  );
}

/* ─── Mock Transactions Data ─── */

interface Transaction {
  id: string;
  date: string;
  institution: string;
  lineItem: string;
  amount: number;
  status: 'Engagé' | 'Mandaté' | 'Payé';
  direction: 'debit' | 'credit';
}

const recentTransactions: Transaction[] = [
  { id: 'TX-2026-0891', date: '2026-04-25', institution: 'EPT', lineItem: 'Titre I — Fonctionnement', amount: 245_000, status: 'Payé', direction: 'debit' },
  { id: 'TX-2026-0890', date: '2026-04-24', institution: 'INSAT', lineItem: 'Titre II — Investissement', amount: 1_280_000, status: 'Engagé', direction: 'debit' },
  { id: 'TX-2026-0889', date: '2026-04-24', institution: 'SUPCOM', lineItem: 'Titre I — Salaires', amount: 890_500, status: 'Payé', direction: 'debit' },
  { id: 'TX-2026-0888', date: '2026-04-23', institution: 'FST', lineItem: 'Titre II — Équipement Labo', amount: 620_000, status: 'Mandaté', direction: 'debit' },
  { id: 'TX-2026-0887', date: '2026-04-23', institution: 'INAT', lineItem: 'Titre I — Fonctionnement', amount: 178_300, status: 'Payé', direction: 'debit' },
  { id: 'TX-2026-0886', date: '2026-04-22', institution: 'FSEG', lineItem: 'Titre II — Infrastructure', amount: 2_150_000, status: 'Engagé', direction: 'debit' },
  { id: 'TX-2026-0885', date: '2026-04-22', institution: 'ISG', lineItem: 'Titre I — Formation Continue', amount: 95_000, status: 'Mandaté', direction: 'debit' },
  { id: 'TX-2026-0884', date: '2026-04-21', institution: 'ENSTAB', lineItem: 'Titre I — Fonctionnement', amount: 310_000, status: 'Payé', direction: 'debit' },
  { id: 'TX-2026-0883', date: '2026-04-21', institution: 'EPT', lineItem: 'Titre II — Recherche', amount: 540_000, status: 'Engagé', direction: 'debit' },
  { id: 'TX-2026-0882', date: '2026-04-20', institution: 'INSAT', lineItem: 'Titre I — Salaires', amount: 1_420_000, status: 'Payé', direction: 'debit' },
];

/* ─── Finance Page ─── */

export function Finance() {
  const rows = institutions.map((inst) => {
    const allocated = Math.round(inst.students * 1650);
    const executionRate = inst.kpiSnapshot.documentControlCompliance / 100;
    const paid = Math.round(allocated * executionRate * 0.82);
    const mandated = Math.round(allocated * executionRate * 0.92);
    const engaged = Math.round(allocated * executionRate);
    const executed = Math.round(allocated * executionRate);
    return {
      code: inst.code,
      name: inst.name,
      city: inst.city,
      students: inst.students,
      allocated,
      engaged,
      mandated,
      paid,
      executed,
      executionRate: Number((executionRate * 100).toFixed(1)),
      remaining: allocated - executed,
    };
  });

  const totalAllocated = rows.reduce((s, r) => s + r.allocated, 0);
  const totalExecuted = rows.reduce((s, r) => s + r.executed, 0);
  const totalStudents = rows.reduce((s, r) => s + r.students, 0);
  const totalRemaining = totalAllocated - totalExecuted;
  const globalExecRate = ((totalExecuted / totalAllocated) * 100).toFixed(1);
  const costPerStudent = Math.round(totalAllocated / totalStudents);
  const masseSalariale = Math.round(totalAllocated * 0.72 * 0.58); // ~58% of T1 is salaries
  const masseSalarialePct = ((masseSalariale / totalAllocated) * 100).toFixed(1);
  const fondsRecherche = Math.round(totalAllocated * 0.08); // ~8% of total

  // Budget split for donut
  const titreI = {
    label: 'Titre I — Fonctionnement & Salaires',
    shortLabel: 'Titre I',
    allocated: Math.round(totalAllocated * 0.72),
    engaged: Math.round(totalAllocated * 0.72 * 0.88),
    mandated: Math.round(totalAllocated * 0.72 * 0.81),
    paid: Math.round(totalAllocated * 0.72 * 0.74),
  };
  const titreII = {
    label: 'Titre II — Investissement',
    shortLabel: 'Titre II',
    allocated: Math.round(totalAllocated * 0.28),
    engaged: Math.round(totalAllocated * 0.28 * 0.69),
    mandated: Math.round(totalAllocated * 0.28 * 0.54),
    paid: Math.round(totalAllocated * 0.28 * 0.41),
  };

  const donutData = [
    { name: titreI.shortLabel, value: titreI.allocated, fill: '#1B4F8B' },
    { name: titreII.shortLabel, value: titreII.allocated, fill: '#87A6C7' },
  ];

  return (
    <div className="space-y-6">
      {/* ── KPI Row 1: Core Finance ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KPIFinanceCard
          label="Budget Alloué"
          value={`${(totalAllocated / 1_000_000).toFixed(1)} M`}
          unit="TND"
          icon={Wallet}
          accent="bg-[#F0F5FA] text-[#1B4F8B]"
        />
        <KPIFinanceCard
          label="Taux d'Exécution"
          value={`${globalExecRate}%`}
          icon={TrendingUp}
          accent="bg-emerald-50 text-emerald-700"
          sub={`${(totalExecuted / 1_000_000).toFixed(1)} M TND exécutés`}
        />
        <KPIFinanceCard
          label="Reste à Payer"
          value={`${(totalRemaining / 1_000_000).toFixed(1)} M`}
          unit="TND"
          icon={AlertTriangle}
          accent="bg-amber-50 text-amber-700"
          sub={`Écart: ${((totalRemaining / totalAllocated) * 100).toFixed(1)}%`}
        />
      </div>

      {/* ── KPI Row 2: Analytical Metrics ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KPIFinanceCard
          label="Coût moyen par étudiant"
          value={costPerStudent.toLocaleString('fr-FR')}
          unit="TND/an"
          icon={GraduationCap}
          accent="bg-indigo-50 text-indigo-700"
          sub={`${totalStudents.toLocaleString('fr-FR')} étudiants inscrits`}
        />
        <KPIFinanceCard
          label="Part de la Masse Salariale"
          value={`${masseSalarialePct}%`}
          icon={Users}
          accent="bg-slate-100 text-slate-600"
          sub={`${(masseSalariale / 1_000_000).toFixed(1)} M TND en charges personnel`}
        />
        <KPIFinanceCard
          label="Fonds de Recherche"
          value={`${(fondsRecherche / 1_000_000).toFixed(1)} M`}
          unit="TND"
          icon={Briefcase}
          accent="bg-teal-50 text-teal-700"
          sub="8% du budget total affecté à la recherche"
        />
      </div>

      {/* ── Donut + Budget Lines Side by Side ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Donut Chart */}
        <div className="lg:col-span-4 bg-white rounded-lg border border-slate-200 p-6">
          <h3 className="text-sm font-semibold text-[#0F172A] mb-1">Répartition budgétaire</h3>
          <p className="text-xs text-slate-500 mb-5">Distribution entre titres budgétaires</p>

          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={donutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {donutData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: number) => `${(val / 1_000_000).toFixed(1)} M TND`}
                  contentStyle={{
                    borderRadius: '8px', border: '1px solid #e2e8f0',
                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', fontSize: '12px',
                    fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Legend */}
          <div className="flex flex-col gap-3 mt-4">
            {donutData.map((item) => {
              const pct = ((item.value / totalAllocated) * 100).toFixed(0);
              return (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: item.fill }} />
                    <span className="text-xs font-medium text-slate-700">{item.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-500 tabular-nums">{(item.value / 1_000_000).toFixed(1)} M</span>
                    <span className="text-xs font-semibold text-slate-900 tabular-nums w-10 text-right">{pct}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Execution by Titre */}
        <div className="lg:col-span-8 bg-white rounded-lg border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[#0F172A]">Exécution budgétaire par titre</h3>
            <div className="flex items-center gap-5">
              <LegendDot color="bg-[#1B4F8B]" label="Payé" />
              <LegendDot color="bg-[#4A7DC0]" label="Mandaté" />
              <LegendDot color="bg-[#87A6C7]" label="Engagé" />
              <LegendDot color="bg-slate-100" label="Alloué" />
            </div>
          </div>

          <table className="w-full text-left">
            <thead>
              <tr>
                <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Ligne budgétaire</th>
                <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Alloué (TND)</th>
                <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Payé (TND)</th>
                <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider w-72">Progression</th>
                <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Écart</th>
              </tr>
            </thead>
            <tbody>
              {[titreI, titreII].map((line) => (
                <tr key={line.label} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors duration-100">
                  <td className="py-4 px-6 text-sm font-medium text-[#0F172A]">{line.label}</td>
                  <td className="py-4 px-6 text-sm text-right tabular-nums text-slate-600">{line.allocated.toLocaleString('fr-FR')}</td>
                  <td className="py-4 px-6 text-sm text-right tabular-nums text-[#0F172A] font-medium">{line.paid.toLocaleString('fr-FR')}</td>
                  <td className="py-4 px-6">
                    <SegmentedBar allocated={line.allocated} engaged={line.engaged} mandated={line.mandated} paid={line.paid} />
                  </td>
                  <td className="py-4 px-6 text-sm text-right tabular-nums text-amber-700 font-medium">
                    {(line.allocated - line.paid).toLocaleString('fr-FR')}
                  </td>
                </tr>
              ))}
              {/* Total */}
              <tr className="bg-slate-50/60">
                <td className="py-4 px-6 text-sm font-semibold text-[#0F172A]">Total réseau</td>
                <td className="py-4 px-6 text-sm text-right tabular-nums font-semibold text-[#0F172A]">{(titreI.allocated + titreII.allocated).toLocaleString('fr-FR')}</td>
                <td className="py-4 px-6 text-sm text-right tabular-nums font-semibold text-[#0F172A]">{(titreI.paid + titreII.paid).toLocaleString('fr-FR')}</td>
                <td className="py-4 px-6">
                  <SegmentedBar
                    allocated={titreI.allocated + titreII.allocated}
                    engaged={titreI.engaged + titreII.engaged}
                    mandated={titreI.mandated + titreII.mandated}
                    paid={titreI.paid + titreII.paid}
                  />
                </td>
                <td className="py-4 px-6 text-sm text-right tabular-nums font-semibold text-amber-700">
                  {((titreI.allocated + titreII.allocated) - (titreI.paid + titreII.paid)).toLocaleString('fr-FR')}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Per-Institution Table ── */}
      <section className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-[#0F172A]">Détail par établissement</h3>
          <span className="text-xs text-slate-500">{rows.length} établissements</span>
        </div>

        <table className="w-full text-left">
          <thead>
            <tr>
              <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Établissement</th>
              <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Alloué (TND)</th>
              <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Exécuté (TND)</th>
              <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Exécution</th>
              <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider w-56">Progression</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.code} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors duration-100">
                <td className="py-4 px-6">
                  <p className="text-sm font-medium text-[#0F172A]">{row.code}</p>
                  <p className="text-xs text-slate-500">{row.city}</p>
                </td>
                <td className="py-4 px-6 text-sm text-right tabular-nums text-slate-600">{row.allocated.toLocaleString('fr-FR')}</td>
                <td className="py-4 px-6 text-sm text-right tabular-nums text-[#0F172A] font-medium">{row.executed.toLocaleString('fr-FR')}</td>
                <td className="py-4 px-6 text-sm text-right tabular-nums">
                  <span className={cn(
                    'font-medium',
                    row.executionRate >= 80 ? 'text-emerald-700' :
                    row.executionRate >= 60 ? 'text-amber-700' :
                    'text-red-600'
                  )}>
                    {row.executionRate}%
                  </span>
                </td>
                <td className="py-4 px-6">
                  <SegmentedBar allocated={row.allocated} engaged={row.engaged} mandated={row.mandated} paid={row.paid} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* ── Mouvements & Engagements Récents ── */}
      <section className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-[#0F172A]">Mouvements & Engagements Récents</h3>
            <p className="text-xs text-slate-500 mt-0.5">Dernières opérations budgétaires du réseau</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Calendar size={13} />
            <span>Avr. 2026</span>
          </div>
        </div>

        <table className="w-full text-left">
          <thead>
            <tr>
              <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Date</th>
              <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Établissement</th>
              <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Ligne budgétaire</th>
              <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-right">Montant (TND)</th>
              <th className="py-3 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-center">Statut</th>
            </tr>
          </thead>
          <tbody>
            {recentTransactions.map((tx) => (
              <tr key={tx.id} className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors duration-100">
                <td className="py-4 px-6">
                  <span className="text-sm text-slate-700 tabular-nums">
                    {new Date(tx.date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })}
                  </span>
                </td>
                <td className="py-4 px-6">
                  <span className="text-sm font-medium text-[#0F172A]">{tx.institution}</span>
                </td>
                <td className="py-4 px-6">
                  <span className="text-sm text-slate-600">{tx.lineItem}</span>
                </td>
                <td className="py-4 px-6 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    {tx.direction === 'debit' ? (
                      <ArrowUpRight size={13} className="text-red-400" />
                    ) : (
                      <ArrowDownRight size={13} className="text-emerald-500" />
                    )}
                    <span className="text-sm font-medium text-[#0F172A] tabular-nums">
                      {tx.amount.toLocaleString('fr-FR')}
                    </span>
                  </div>
                </td>
                <td className="py-4 px-6 text-center">
                  <TransactionStatusBadge status={tx.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50/60 border-t border-slate-200 flex justify-between items-center">
          <span className="text-xs text-slate-500">
            Affichage des 10 dernières opérations
          </span>
          <button className="text-xs font-semibold text-[#1B4F8B] hover:underline">
            Voir l'historique complet →
          </button>
        </div>
      </section>
    </div>
  );
}

/* ─── Sub-Components ─── */

function KPIFinanceCard({ label, value, unit, icon: Icon, accent, sub }: {
  label: string;
  value: string;
  unit?: string;
  icon: typeof Wallet;
  accent: string;
  sub?: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6 hover:border-slate-300 transition-colors duration-150">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</span>
        <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center', accent)}>
          <Icon size={16} strokeWidth={1.6} />
        </div>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold text-[#0F172A] tabular-nums tracking-tight">{value}</span>
        {unit && <span className="text-sm text-slate-500">{unit}</span>}
      </div>
      {sub && <p className="text-xs text-slate-500 mt-2">{sub}</p>}
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={cn('w-2.5 h-2.5 rounded-sm', color)} />
      <span className="text-xs text-slate-500">{label}</span>
    </div>
  );
}

function TransactionStatusBadge({ status }: { status: Transaction['status'] }) {
  const config: Record<string, { style: string }> = {
    'Engagé': { style: 'bg-blue-50 text-blue-700 border border-blue-200/60' },
    'Mandaté': { style: 'bg-amber-50 text-amber-700 border border-amber-200/60' },
    'Payé': { style: 'bg-emerald-50 text-emerald-700 border border-emerald-200/60' },
  };
  const c = config[status] || config['Engagé'];
  return (
    <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-md text-[11px] font-medium', c.style)}>
      {status}
    </span>
  );
}
