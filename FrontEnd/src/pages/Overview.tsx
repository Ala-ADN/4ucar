import { School, CheckCircle2, AlertCircle, Wallet } from 'lucide-react';
import { KPICard } from '@/src/components/kpi/KPICard';
import institutionsData from '@/src/data/institutions.json';
import alertsData from '@/src/data/alerts.json';
import { Badge } from '@/src/components/ui/StatusDot';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Link } from 'react-router-dom';
import { Institution } from '@/src/types';

const trendData = [
  { name: 'S2 21-22', reussite: 72, abandon: 5.2 },
  { name: 'S1 22-23', reussite: 74, abandon: 4.8 },
  { name: 'S2 22-23', reussite: 75, abandon: 4.5 },
  { name: 'S1 23-24', reussite: 76, abandon: 4.2 },
  { name: 'S2 23-24', reussite: 76.4, abandon: 3.8 },
  { name: 'S1 24-25', reussite: 77.1, abandon: 3.5 },
];

export function Overview() {
  const institutions = institutionsData as Institution[];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard 
          label="Établissements surveillés" 
          value={35} 
          icon={School} 
          trend={{ value: 2, unit: '' }}
        />
        <KPICard 
          label="Taux de réussite moyen" 
          value={76.4} 
          suffix="%" 
          icon={CheckCircle2} 
          trend={{ value: 1.2, unit: '%' }}
        />
        <KPICard 
          label="Alertes actives" 
          value={8} 
          icon={AlertCircle} 
          badge="8"
          trend={{ value: -3, unit: '', isPositiveGood: false }}
        />
        <KPICard 
          label="Budget exécuté (réseau)" 
          value={68.2} 
          suffix="%" 
          icon={Wallet} 
          trend={{ value: 5.4, unit: '%' }}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-8 bg-white p-6 rounded-md border border-slate-200">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Rapport de performance reseau</h2>
              <p className="text-sm text-slate-600 mt-1">Donnees agregees sur les 6 derniers semestres</p>
            </div>
            <button className="px-3 py-1.5 rounded border border-slate-300 text-sm text-slate-700 hover:bg-slate-50 transition-colors duration-150">
              Imprimer
            </button>
          </div>

          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis 
                  dataKey="name" 
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
                />
                <Tooltip 
                  contentStyle={{ 
                    borderRadius: '6px', 
                    border: '1px solid #e2e8f0', 
                    boxShadow: 'none',
                    fontSize: '12px'
                  }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="reussite" 
                  stroke="#2563eb" 
                  strokeWidth={2} 
                  dot={{ r: 3, fill: '#2563eb', strokeWidth: 0 }} 
                  activeDot={{ r: 4 }} 
                  name="Réussite"
                />
                <Line 
                  type="monotone" 
                  dataKey="abandon" 
                  stroke="#64748b" 
                  strokeWidth={2} 
                  strokeDasharray="5 5"
                  name="Abandon"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-md overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-sm font-semibold text-slate-900">Alertes actives</h3>
            <span className="text-xs text-slate-500">{alertsData.length} elements</span>
          </div>
          <div className="divide-y divide-slate-200 bg-white">
            {alertsData.slice(0, 5).map((alert) => (
              <div key={alert.id} className="px-4 py-3 flex items-start justify-between gap-3">
                <div className="flex items-center gap-4">
                  <div className={alert.severity === 'critical' ? 'w-2 h-2 rounded-full bg-red-600 mt-1.5' : 'w-2 h-2 rounded-full bg-amber-500 mt-1.5'} />
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-slate-900">{alert.institution}</span>
                    <span className="text-xs text-slate-600 truncate max-w-[180px]">{alert.title}</span>
                  </div>
                </div>
                <span className="text-xs font-medium text-slate-500">{alert.time}</span>
              </div>
            ))}
          </div>
          <div className="mt-auto p-4 bg-slate-50 border-t border-slate-200">
            <p className="text-xs leading-relaxed text-slate-700">
              {alertsData.length} alertes actives detectees. Les etablissements critiques sont a traiter en priorite.
            </p>
          </div>
        </div>
      </div>

      <section className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Sante des etablissements</h2>
          <Link to="/institutions" className="text-sm text-blue-800 hover:text-blue-900 transition-colors duration-150">
            Voir tous les etablissements
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700">Code</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700">Etablissement</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700">Type</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700">Ville</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Reussite</th>
                <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Budget</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {institutions.slice(0, 8).map((institution) => (
                <tr key={institution.code} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-sm font-medium text-slate-800">{institution.code}</td>
                  <td className="px-4 py-3 text-sm text-slate-900">
                    <Link to={`/institutions/${institution.code}`} className="hover:text-blue-800">
                      {institution.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-700">
                    <Badge variant={institution.type === 'grande_ecole' ? 'info' : institution.type === 'faculte' ? 'purple' : 'amber'}>
                      {institution.type.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-700">{institution.city}</td>
                  <td className="px-4 py-3 text-sm text-slate-900 text-right font-tabular">{institution.kpi_snapshot?.taux_reussite ?? 0}%</td>
                  <td className="px-4 py-3 text-sm text-slate-900 text-right font-tabular">{institution.kpi_snapshot?.budget_execution ?? 0}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
