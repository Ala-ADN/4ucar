import { motion } from 'motion/react';
import { School, CheckCircle2, AlertCircle, Wallet, TrendingUp, TrendingDown } from 'lucide-react';
import { KPICard } from '@/src/components/kpi/KPICard';
import institutionsData from '@/src/data/institutions.json';
import alertsData from '@/src/data/alerts.json';
import { Badge, StatusDot } from '@/src/components/ui/StatusDot';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Link } from 'react-router-dom';
import { Institution, HealthStatus } from '@/src/types';
import { cn } from '@/src/lib/utils';

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
    <div className="space-y-8">
      {/* Summary Strip */}
      <motion.div 
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
      >
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
      </motion.div>

      {/* Institution Health Grid */}
      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold font-sans text-text-primary">Santé des établissements</h2>
          <Link to="/institutions" className="text-sm font-semibold text-blue-500 hover:text-blue-600 transition-colors">
            Voir tous les établissements →
          </Link>
        </div>
        
        <motion.div 
          variants={{ visible: { transition: { staggerChildren: 0.05 } } }}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
        >
          {institutions.slice(0, 8).map((inst) => (
            <div key={inst.code}>
              <InstitutionCard institution={inst} />
            </div>
          ))}
        </motion.div>
      </section>

      {/* Bottom split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Network Trends Section */}
        <div className="lg:col-span-8 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-10">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-[0.15em] text-slate-600">Rapport de Performance Réseau</h2>
              <p className="text-xs text-slate-400 mt-1">Données agrégées sur les 6 derniers semestres</p>
            </div>
            <div className="flex items-center gap-6">
               <div className="flex flex-col items-end">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Tendance</span>
                  <span className="text-sm font-bold text-green-600">+4.2% HAUT</span>
               </div>
               <div className="h-8 w-px bg-slate-100" />
               <button className="text-[10px] font-bold text-blue-600 underline">IMPRIMER</button>
            </div>
          </div>
          
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 10, fontWeight: 700, fill: '#94a3b8' }} 
                  dy={10}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 10, fontWeight: 700, fill: '#94a3b8' }} 
                  unit="%"
                />
                <Tooltip 
                  contentStyle={{ 
                    borderRadius: '12px', 
                    border: '1px solid #e2e8f0', 
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }} 
                />
                <Line 
                  type="monotone" 
                  dataKey="reussite" 
                  stroke="#2563eb" 
                  strokeWidth={3} 
                  dot={{ r: 4, fill: '#2563eb', strokeWidth: 2, stroke: '#fff' }} 
                  activeDot={{ r: 6 }} 
                  name="Réussite"
                />
                <Line 
                  type="monotone" 
                  dataKey="abandon" 
                  stroke="#cbd5e1" 
                  strokeWidth={2} 
                  strokeDasharray="5 5"
                  name="Abandon"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Alerts Feed Section -> "Service Nodes" look */}
        <div className="lg:col-span-4 bg-slate-50 border border-slate-200 rounded-2xl overflow-hidden shadow-sm flex flex-col">
          <div className="bg-white px-6 py-5 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600">Noeuds en Alerte</h3>
            <span className="text-[10px] font-bold text-blue-600 underline">FILTRER</span>
          </div>
          <div className="divide-y divide-slate-200">
            {alertsData.slice(0, 5).map((alert) => (
              <div key={alert.id} className="px-6 py-4 flex items-center justify-between bg-white hover:bg-slate-50/50 transition-colors group cursor-pointer">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    alert.severity === 'critical' ? 'bg-red-500 animate-pulse' : 'bg-status-high'
                  )} />
                  <div className="flex flex-col">
                    <span className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-all">{alert.institution}</span>
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-tight truncate max-w-[140px]">{alert.title}</span>
                  </div>
                </div>
                <span className="text-xs font-mono bg-slate-100 px-2 py-1 rounded text-slate-500">{alert.time}</span>
              </div>
            ))}
          </div>
          <div className="mt-auto p-6 bg-blue-50 border-t border-blue-100">
             <p className="text-xs leading-relaxed text-blue-900">
               <span className="font-bold">Info Système:</span> {alertsData.length} alertes actives détectées. Protocoles de remédiation suggérés pour les noeuds critiques.
             </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function InstitutionCard({ institution }: { institution: Institution }) {
  const typeLabels = {
    grande_ecole: "Grande École",
    faculte: "Faculté",
    preparatoire: "Préparatoire"
  };

  const typeVariants = {
    grande_ecole: "info",
    faculte: "purple",
    preparatoire: "amber"
  } as const;

  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 16 },
        visible: { opacity: 1, y: 0 }
      }}
      whileHover={{ y: -4 }}
      className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm transition-all cursor-pointer group hover:border-blue-200"
    >
      <Link to={`/institutions/${institution.code}`}>
        <div className="flex justify-between items-start mb-6">
          <Badge variant={typeVariants[institution.type]}>{typeLabels[institution.type]}</Badge>
          <div className="flex items-center gap-2">
             <span className="text-[10px] font-bold text-slate-400 uppercase tabular-nums">{institution.code}</span>
             <StatusDot status={institution.global_health} animate />
          </div>
        </div>

        <div className="mb-6">
          <h3 className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors truncate">
            {institution.name}
          </h3>
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tight mt-0.5">
            Campus: {institution.city}
          </p>
        </div>

        <div className="space-y-4 mb-6">
          <ResourceLinear label="Académique" value={institution.kpi_snapshot?.taux_reussite || 0} color="bg-blue-600" />
          <ResourceLinear label="Budget exécuté" value={institution.kpi_snapshot?.budget_execution || 0} color="bg-slate-900" />
        </div>

        <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 border-t border-slate-100 pt-5 uppercase tracking-tight">
          <span>{institution.students.toLocaleString()} ÉTUDIANTS</span>
          <span className="text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity underline">ANALYSER</span>
        </div>
      </Link>
    </motion.div>
  );
}

function ResourceLinear({ label, value, color }: { label: string, value: number, color: string }) {
  return (
    <div>
      <div className="flex justify-between text-[10px] mb-1.5 font-bold uppercase">
        <span className="text-slate-500">{label}</span>
        <span className="text-blue-600">{value}%</span>
      </div>
      <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={cn("h-full transition-all duration-1000", color)} style={{ width: `${value}%` }}></div>
      </div>
    </div>
  );
}

function DomainHealth({ dot, status, label }: { dot: string, status: HealthStatus, label: string }) {
  const colors = {
    good: "bg-status-good",
    warning: "bg-status-medium",
    critical: "bg-status-critical"
  };

  return (
    <div className="flex flex-col items-center gap-1.5 flex-1 p-1 px-0 rounded-lg hover:bg-surface-hover transition-colors" title={label}>
      <span className="text-sm grayscale-[0.5]">{dot}</span>
      <div className={cn("w-1.5 h-1.5 rounded-full", colors[status])} />
    </div>
  );
}
