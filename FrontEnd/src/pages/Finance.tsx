import { institutions } from '@/src/data/dashboardMock';
import { cn } from '@/src/lib/utils';
import { Wallet, TrendingUp, AlertTriangle } from 'lucide-react';

/* ─── Segmented Bar ─── */

function SegmentedBar({ allocated, engaged, mandated, paid }: {
  allocated: number;
  engaged: number;
  mandated: number;
  paid: number;
}) {
  const total = allocated || 1;
  const pctEngaged = (engaged / total) * 100;
  const pctMandated = (mandated / total) * 100;
  const pctPaid = (paid / total) * 100;

  return (
    <div className="flex items-center gap-2 w-full">
      <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden flex">
        <div
          className="h-full bg-[#1d5394] transition-all duration-300"
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

/* ─── Finance Page ─── */

export function Finance() {
  // Derive finance data from mock institutions
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
  const totalRemaining = totalAllocated - totalExecuted;
  const globalExecRate = ((totalExecuted / totalAllocated) * 100).toFixed(1);

  // Budget lines split
  const titreI = {
    label: 'Titre I — Fonctionnement',
    allocated: Math.round(totalAllocated * 0.72),
    engaged: Math.round(totalAllocated * 0.72 * 0.88),
    mandated: Math.round(totalAllocated * 0.72 * 0.81),
    paid: Math.round(totalAllocated * 0.72 * 0.74),
  };
  const titreII = {
    label: 'Titre II — Investissement',
    allocated: Math.round(totalAllocated * 0.28),
    engaged: Math.round(totalAllocated * 0.28 * 0.69),
    mandated: Math.round(totalAllocated * 0.28 * 0.54),
    paid: Math.round(totalAllocated * 0.28 * 0.41),
  };

  return (
    <div className="space-y-6">
      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KPIFinanceCard
          label="Budget Alloué"
          value={`${(totalAllocated / 1_000_000).toFixed(1)} M`}
          unit="TND"
          icon={Wallet}
          accent="bg-[#F0F5FA] text-[#1d5394]"
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

      {/* ── Dépenses par Titre ── */}
      <section className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h3 className="text-sm font-semibold text-[#0F172A]">Exécution budgétaire par titre</h3>
        </div>

        {/* Legend */}
        <div className="px-6 pt-4 pb-2 flex items-center gap-5">
          <LegendDot color="bg-[#1d5394]" label="Payé" />
          <LegendDot color="bg-[#4A7DC0]" label="Mandaté" />
          <LegendDot color="bg-[#87A6C7]" label="Engagé" />
          <LegendDot color="bg-slate-100" label="Alloué" />
        </div>

        <table className="w-full text-left">
          <thead>
            <tr>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider">Ligne budgétaire</th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">Alloué (TND)</th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">Payé (TND)</th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider w-72">Progression</th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">Écart</th>
            </tr>
          </thead>
          <tbody>
            {[titreI, titreII].map((line) => (
              <tr key={line.label} className="border-b border-slate-200/50 hover:bg-slate-50/50 transition-colors duration-100">
                <td className="py-4 px-6 text-sm font-medium text-[#0F172A]">{line.label}</td>
                <td className="py-4 px-6 text-sm text-right tabular-nums text-slate-700">{line.allocated.toLocaleString('fr-FR')}</td>
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
            <tr className="bg-slate-50/80">
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
      </section>

      {/* ── Per-Institution Table ── */}
      <section className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-[#0F172A]">Détail par établissement</h3>
          <span className="text-xs text-slate-500">{rows.length} établissements</span>
        </div>

        <table className="w-full text-left">
          <thead>
            <tr>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider">Établissement</th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">Alloué (TND)</th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">Exécuté (TND)</th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">Exécution</th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider w-56">Progression</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.code} className="border-b border-slate-200/50 hover:bg-slate-50/50 transition-colors duration-100">
                <td className="py-4 px-6">
                  <p className="text-sm font-medium text-[#0F172A]">{row.code}</p>
                  <p className="text-xs text-slate-500">{row.city}</p>
                </td>
                <td className="py-4 px-6 text-sm text-right tabular-nums text-slate-700">{row.allocated.toLocaleString('fr-FR')}</td>
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
    <div className="bg-white border border-slate-200 rounded-lg p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</span>
        <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center', accent)}>
          <Icon size={16} />
        </div>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold text-[#0F172A] tabular-nums">{value}</span>
        {unit && <span className="text-sm text-slate-500">{unit}</span>}
      </div>
      {sub && <p className="text-xs text-slate-500 mt-1.5">{sub}</p>}
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
